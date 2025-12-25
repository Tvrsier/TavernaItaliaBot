import asyncio
import os
import pkgutil

import psutil
from typing import List, Optional, Union

from discord import Intents, NoEntryPointError, ExtensionFailed, Activity, ActivityType, Interaction, \
    ApplicationContext
from discord.ext.commands import Context, Bot

from app.lib.db import DatabaseManager
from app.logger import logger
from app.lib.extension_context import TavernaContext, TavernaApplicationContext
from app.lib.db.scheme import GuildSchema


ANY_CONTEXT = Union[Context, ApplicationContext]
ANY_EXTENSION_CONTEXT = Union[TavernaContext, TavernaApplicationContext]


def discover_cogs() -> Optional[List[str]]:
    try:
        import app.cogs as cogs_pkg
        names: List[str] = [name for _, name, ispkg in pkgutil.iter_modules(cogs_pkg.__path__)
                            if not ispkg and not name.startswith("_")]
        if names:
            return names
    except Exception as e:
        logger.error("Failed to discover cogs: %s", e, exc_info=True)
        raise RuntimeError("Failed to discover cogs. Please check your cogs directory.") from e


prefix = "tav&"
OWNER_IDS = [int(x) for x in os.getenv("OWNER_IDS").split(",") if x]
COGS = discover_cogs()


class Ready:
    """Tracks cogs loading status."""

    def __init__(self):
        if COGS is None or len(COGS) == 0:
            logger.warning("No cogs found to load. If you think this is an error, please check your cogs directory.")

        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog: str):
        setattr(self, cog, True)
        logger.info(f"Cog {cog} has been loaded")

    def all_ready(self) -> bool:
        if not COGS or len(COGS) == 0:
            return True
        return all(getattr(self, cog) for cog in COGS)


class TavernaBot(Bot):
    def __init__(self):
        intents = Intents.default() | Intents.message_content | Intents.members | Intents.presences | Intents.guilds

        super().__init__(
            command_prefix=prefix,
            owner_ids=OWNER_IDS,
            intents=intents,
        )
        models = {"models": ["app.lib.db.schemes"]}
        self.db = DatabaseManager(os.getenv("DATABASE_URL"), models)
        self.version = None
        self.token = os.getenv("API_KEY")
        if not self.token:
            raise ValueError("API_KEY environment variable not set. Please set it to your bot's token.")
        self.cogs_ready = Ready()
        self.__ready__ = False
        self.owner_id = OWNER_IDS[0] if OWNER_IDS else None
        self.before_invoke(self._inject_log_channel)
        self.after_invoke(self._auto_log)
        self.auto_sync_commands = True

    def run(self, version: str):
        self.version = version
        logger.info("Starting Taverna Bot version %s", version)
        logger.info("Running setup . . .")
        self.setup_cogs()
        logger.info("Setup complete. Running bot . . .")
        super().run(self.token, reconnect=True)

    def setup_cogs(self):
        if COGS is not None and len(COGS) > 0:
            for cog in COGS:
                try:
                    logger.debug("Loading cog: %s", cog)
                    self.load_extension(f"app.cogs.{cog}")
                except NoEntryPointError as e:
                    logger.error("Ignoring %s (load failed): %s", cog, e, exc_info=True)
                except ExtensionFailed as e:
                    logger.error("Ignoring %s (load failed): %s", cog, e, exc_info=True)
                except Exception as e:
                    logger.error("Ignoring %s (load failed): %s", cog, e, exc_info=True)
                else:
                    logger.debug("Cog %s loaded successfully", cog)
                    self.cogs_ready.ready_up(cog)
        else:
            logger.warning("No cogs found to load. If you think this is an error, please check your cogs directory."
                           "Launching bot assuming no cogs is present.")
            self.__ready__ = True

    async def on_connect(self):
        await self.db.connect()
        logger.info("Database connected.")
        logger.info(f"Bot {self.user} connected to Discord.")

    async def on_ready(self):
        if not self.__ready__:
            while not self.cogs_ready.all_ready():
                await asyncio.sleep(0.5)
        logger.info("Taverna Bot is ready!")
        self.memory_monitor()
        await self.change_presence(activity=Activity(type=ActivityType.watching,
                                                     name=f"{len(self.users)} users | v{self.version}"))
        logger.debug("Syncing commands . . .")
        guild_ids = [guild.id for guild in self.guilds]
        await self.sync_commands(guild_ids=guild_ids)

    async def get_context(self, message, *, cls=Context):
        """Override to inject log channel into context."""
        ctx = await super().get_context(message, cls=cls)
        return ctx

    async def get_application_context(
            self, interaction: Interaction, cls=ApplicationContext
    ):
        actx = await super().get_application_context(interaction, cls=cls)
        return actx

    # noinspection PyMethodMayBeStatic
    async def _inject_log_channel(self, ctx: ANY_EXTENSION_CONTEXT) -> None:
        """Injects the log channel into the context if it exists."""
        if ctx.guild:
            db_guild = await GuildSchema.get_or_none(id=ctx.guild.id)
            if db_guild and db_guild.log_channel_id:
                ctx.log_channel = ctx.guild.get_channel(db_guild.log_channel_id)
            else:
                ctx.log_channel = None
        else:
            ctx.log_channel = None

    # noinspection PyMethodMayBeStatic
    async def _auto_log(self, ctx: ANY_EXTENSION_CONTEXT) -> None:
        """Automatically sends a log message if the context has a log_message attribute."""
        await ctx.send_log()

    def memory_monitor(self, *args):
        """Monitors the bot's memory usage and logs it every 10 minutes."""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        cpu_pct = process.cpu_percent(interval=1.0)
        mb_rss = memory_info.rss / (1024 * 1024)
        mb_vms = memory_info.vms / (1024 * 1024)
        if mb_rss > 500 or mb_vms > 1000 or cpu_pct > 50:
            logger.warning(
                f"High memory usage detected: RSS={mb_rss:.2f} MB, VMS={mb_vms:.2f} MB, CPU usage: {cpu_pct}%")
        asyncio.get_event_loop().call_later(20, self.memory_monitor, *args)  # every 20 seconds

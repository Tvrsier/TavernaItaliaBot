from discord.ext import commands

from app.bot import ANY_CONTEXT
from app.lib.db.queries import get_command_permission
from app.lib.db.scheme import CommandEnum
from app.logger import logger


def require_role(command: CommandEnum):
    async def predicate(ctx: ANY_CONTEXT):
        guild = ctx.guild
        if not guild:
            logger.error("Command cannot be used in private messages.")
            raise commands.NoPrivateMessage("Questo comando non può essere usato nei messaggi privati.")

        if ctx.author.guild_permissions.administrator:
            return True

        role_ids = await get_command_permission(guild, command)
        if not role_ids:
            raise commands.CheckFailure("❌ Non hai i permessi per usare questo comando")
        if any(role.id in role_ids for role in ctx.author.roles):
            return True
        else:
            raise commands.CheckFailure("❌ Non hai i permessi per usare questo comando")

    return commands.check(predicate)

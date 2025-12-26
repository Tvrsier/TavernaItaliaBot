from typing import List

from discord import Guild

from app.lib.db.schemes import CommandEnum, CommandPermissionSchema, GuildSchema
from app.logger import logger


async def get_command_permission(guild: Guild, command: CommandEnum) -> List[int]:
    role_ids = await CommandPermissionSchema.filter(
        guild_id=guild.id,
        command=command
    ).values_list("role_id", flat=True)
    return role_ids


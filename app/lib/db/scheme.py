from enum import Enum

from tortoise import models, fields


class CommandEnum(str, Enum):
    PLACE_HOLDER = "place_holder"


class GuildSchema(models.Model):
    id = fields.BigIntField(primary_key=True, unique=True)
    name = fields.CharField(max_length=255, null=True)
    icon_hash = fields.CharField(max_length=255, null=True)
    owner_id = fields.BigIntField(null=True)
    log_channel_id = fields.BigIntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guild"


class UserSchema(models.Model):
    id = fields.BigIntField(primary_key=True, unique=True)
    username = fields.CharField(max_length=255, null=True)
    discriminator = fields.CharField(max_length=10, null=True)
    avatar_hash = fields.CharField(max_length=255, null=True)
    is_bot = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)
    tav_coins = fields.IntField(default=0)

    class Meta:
        table = "user"


class CommandPermissionSchema(models.Model):
    id = fields.IntField(primary_key=True, unique=True, auto_increment=True)
    guild = fields.ForeignKeyField("models.GuildSchema", related_name="command_permissions",
                                   on_delete=fields.CASCADE, null=False)
    command = fields.CharEnumField(CommandEnum, null=False, max_length=255)
    role_id = fields.BigIntField(null=False)

    class Meta:
        table = "command_permission"
        unique_together = (("guild", "command", "role_id"),)
        indexes = (("guild", "command"),)


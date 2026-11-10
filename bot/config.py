"""Environment-backed configuration.

Defaults are safe for local development. Production deployments should set at
least ``DISCORD_TOKEN``; everything else is optional.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_COMMAND_PREFIX = "?"
DEFAULT_LOG_LEVEL = "INFO"


@dataclass(frozen=True)
class Settings:
    token: str | None
    command_prefix: str
    emoji_guild_id: int | None
    log_level: str
    log_file: str | None


def _optional_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_settings() -> Settings:
    return Settings(
        token=os.getenv("DISCORD_TOKEN") or None,
        command_prefix=os.getenv("COMMAND_PREFIX", DEFAULT_COMMAND_PREFIX),
        emoji_guild_id=_optional_int(os.getenv("EMOJI_GUILD_ID")),
        log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
        log_file=os.getenv("LOG_FILE") or None,
    )

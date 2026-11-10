"""Guild emoji lookup used for mana symbols.

Emojis are optional: if the configured guild is unavailable or the bot is not a
member, :func:`get` returns the caller's text fallback (for example ``{W}``).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


class _Emoji(Protocol):
    name: str
    id: int


EMOJIS: list[_Emoji] = []
_BY_NAME: dict[str, str] = {}


def load(guild_emojis: Iterable[_Emoji]) -> None:
    global EMOJIS
    EMOJIS = list(guild_emojis)
    _BY_NAME.clear()
    _BY_NAME.update({emoji.name.lower(): f"<:{emoji.name}:{emoji.id}>" for emoji in EMOJIS})


def get(name: str, fallback: str = "") -> str:
    return _BY_NAME.get(name.lower(), fallback)


def is_loaded() -> bool:
    return bool(_BY_NAME)

"""Discord-facing response shape."""

from __future__ import annotations

from typing import TypedDict

from discord import Embed, File


class ScryQueryBotResponse(TypedDict):
    response_message: str
    files: list[File]
    embed: Embed | None


class ClashEntry(TypedDict):
    user: str
    card_name: str
    card_image_url: str
    cmc: float

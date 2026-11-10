from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import discord
import pytest

import bot.utils as utils
from bot.utils import get_reply_card_name, get_reply_query


def _message(
    content: str = "",
    *,
    message_id: int = 1,
    referenced_id: int | None = None,
    author_id: int = 1,
    embeds: list[discord.Embed] | None = None,
) -> Any:
    reference = None if referenced_id is None else SimpleNamespace(message_id=referenced_id)
    return SimpleNamespace(
        content=content,
        id=message_id,
        reference=reference,
        author=SimpleNamespace(id=author_id),
        embeds=embeds or [],
    )


def _context(
    *,
    message: Any,
    messages: dict[int, Any] | None = None,
    bot_user_id: int = 999,
) -> Any:
    messages = messages or {}

    async def fetch_message(message_id: int) -> Any:
        try:
            return messages[message_id]
        except KeyError:
            raise discord.NotFound(
                SimpleNamespace(status=404, reason="Not Found"), "gone"
            ) from None

    channel = SimpleNamespace(fetch_message=fetch_message)
    return SimpleNamespace(
        message=message,
        channel=channel,
        bot=SimpleNamespace(user=SimpleNamespace(id=bot_user_id)),
    )


@pytest.mark.asyncio
async def test_reply_query_collects_chain_nearest_first() -> None:
    oldest = _message("?sq t:elf", message_id=1)
    middle = _message("?sq otag:manadork", message_id=2, referenced_id=1)
    newest = _message("?sq c:green", message_id=3, referenced_id=2)
    ctx = _context(message=_message("?sq", referenced_id=3), messages={1: oldest, 2: middle})

    # The bot first fetches message 3, which is not in the map, so provide it.
    ctx.channel.fetch_message = _fetcher({1: oldest, 2: middle, 3: newest})

    assert await get_reply_query(ctx, "?sq") == "c:green otag:manadork t:elf"


@pytest.mark.asyncio
async def test_reply_query_ignores_other_commands() -> None:
    previous = _message("?gamble 20", message_id=1)
    ctx = _context(message=_message("?sq", referenced_id=1), messages={1: previous})

    assert await get_reply_query(ctx, "?sq") == ""


@pytest.mark.asyncio
async def test_reply_query_without_reference_returns_empty() -> None:
    ctx = _context(message=_message("?sq t:elf"))

    assert await get_reply_query(ctx, "?sq") == ""


@pytest.mark.asyncio
async def test_reply_query_is_case_insensitive() -> None:
    previous = _message("?SQ t:elf", message_id=1)
    ctx = _context(message=_message("?sq", referenced_id=1), messages={1: previous})

    assert await get_reply_query(ctx, "?sq") == "t:elf"


@pytest.mark.asyncio
async def test_reply_query_stops_when_message_is_deleted() -> None:
    ctx = _context(message=_message("?sq", referenced_id=42), messages={})

    assert await get_reply_query(ctx, "?sq") == ""


@pytest.mark.asyncio
async def test_reply_query_depth_is_capped() -> None:
    messages: dict[int, Any] = {}
    for message_id in range(1, utils.MAX_REPLY_DEPTH + 5):
        messages[message_id] = _message(
            f"?sq term{message_id}",
            message_id=message_id,
            referenced_id=message_id - 1 if message_id > 1 else None,
        )

    start_id = utils.MAX_REPLY_DEPTH + 4
    ctx = _context(message=_message("?sq", referenced_id=start_id), messages=messages)

    fragments = (await get_reply_query(ctx, "?sq")).split()
    assert len(fragments) == utils.MAX_REPLY_DEPTH


@pytest.mark.asyncio
async def test_reply_query_enforces_length_limit() -> None:
    huge = "x" * (utils.MAX_REPLY_QUERY_LENGTH + 10)
    previous = _message(f"?sq {huge}", message_id=1)
    ctx = _context(message=_message("?sq", referenced_id=1), messages={1: previous})

    assert await get_reply_query(ctx, "?sq") == ""


@pytest.mark.asyncio
async def test_reply_card_name_from_embed_title() -> None:
    embed = discord.Embed(title="Sol Ring", url="https://scryfall.com/card/lea/1")
    previous = _message(message_id=1, author_id=999, embeds=[embed])
    ctx = _context(message=_message("?cards", referenced_id=1), messages={1: previous})

    assert await get_reply_card_name(ctx) == "Sol Ring"


@pytest.mark.asyncio
async def test_reply_card_name_from_markdown_link() -> None:
    previous = _message(
        "**[Sol Ring](<https://scryfall.com/card/lea/1>)**",
        message_id=1,
        author_id=999,
    )
    ctx = _context(message=_message("?cards", referenced_id=1), messages={1: previous})

    assert await get_reply_card_name(ctx) == "Sol Ring"


@pytest.mark.asyncio
async def test_reply_card_name_ignores_human_messages() -> None:
    previous = _message("Sol Ring", message_id=1, author_id=1234)
    ctx = _context(message=_message("?cards", referenced_id=1), messages={1: previous})

    assert await get_reply_card_name(ctx) is None


@pytest.mark.asyncio
async def test_reply_card_name_ignores_non_scryfall_embeds() -> None:
    embed = discord.Embed(title="Sol Ring", url="https://example.com/card")
    previous = _message(message_id=1, author_id=999, embeds=[embed])
    ctx = _context(message=_message("?cards", referenced_id=1), messages={1: previous})

    assert await get_reply_card_name(ctx) is None


@pytest.mark.asyncio
async def test_fetch_error_is_swallowed() -> None:
    async def forbidden(message_id: int) -> Any:
        raise discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "nope")

    ctx = _context(message=_message("?sq", referenced_id=1))
    ctx.channel.fetch_message = forbidden

    assert await utils._fetch_referenced_message(ctx, ctx.message) is None


def _fetcher(messages: dict[int, Any]) -> Any:
    async def fetch_message(message_id: int) -> Any:
        return messages[message_id]

    return fetch_message

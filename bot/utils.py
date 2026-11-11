"""Discord formatting and reply-chain helpers."""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence

import discord
from discord.ext import commands

import bot.emojis as emojis
from bot.types import ClashEntry, ScryQueryBotResponse
from image_utils import generate_grid
from scryfall.service import ScryQueryCard

RESPONSE_LIMIT = 32
GRID_BATCH_SIZE = 16
MAX_REPLY_DEPTH = 10
MAX_REPLY_QUERY_LENGTH = 1000
EMBED_DESCRIPTION_LIMIT = 3900

CARD_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(<[^>]*scryfall\.com[^>]*>\)")

logger = logging.getLogger(__name__)


def format_response(cards: list[ScryQueryCard], site_url: str = "") -> ScryQueryBotResponse:
    files: list[discord.File] = []
    embed: discord.Embed | None = None

    if not cards:
        response_message = f"No data found for query {site_url}".strip()
        return {"response_message": response_message, "files": files, "embed": embed}

    if len(cards) == 1:
        card = cards[0]
        embed = discord.Embed(
            title=card["name"],
            url=card["scryfall_url"],
            description=get_formatted_card_info(card),
            color=discord.Color.blue(),
        )
        # Let Discord's CDN serve the card art instead of downloading, resizing,
        # and re-uploading a single image.
        if card["image_uri"]:
            embed.set_image(url=card["image_uri"])
        return {"response_message": "", "files": files, "embed": embed}

    response_message = f">>> ### ScryQuery Results: {len(cards)} cards"
    if len(cards) > RESPONSE_LIMIT:
        response_message += f"\nDisplaying first {RESPONSE_LIMIT} results..."
    if site_url:
        response_message += f"\n{site_url}"

    for start in range(0, min(len(cards), RESPONSE_LIMIT), GRID_BATCH_SIZE):
        batch = cards[start : start + GRID_BATCH_SIZE]
        grid_image = generate_grid(
            [card["image_uri"] for card in batch],
            [card["name"] for card in batch],
        )
        files.append(discord.File(grid_image, filename=f"cards_{start}.jpg"))

    return {"response_message": response_message, "files": files, "embed": embed}


async def get_reply_query(ctx: commands.Context, command_prefix: str) -> str:
    """Collect query fragments from the reply chain, nearest message first."""

    message = await _fetch_referenced_message(ctx, ctx.message)
    if message is None:
        return ""

    prefix = f"{command_prefix} "
    fragments: list[str] = []
    total_length = 0

    for _ in range(MAX_REPLY_DEPTH):
        if message is None:
            break

        content = message.content or ""
        if content.lower().startswith(prefix.lower()):
            fragment = content[len(prefix) :].strip()
            if fragment and total_length + len(fragment) <= MAX_REPLY_QUERY_LENGTH:
                fragments.append(fragment)
                total_length += len(fragment)

        message = await _fetch_referenced_message(ctx, message)

    return " ".join(fragments).strip()


async def get_reply_card_name(ctx: commands.Context) -> str | None:
    """Return the card name from a replied bot message, if there is one.

    Single-card responses put the name in the embed title; multi-card responses
    put it in a Markdown link in the content. Both are checked, and the reply
    chain is walked with an explicit depth cap.
    """

    message = await _fetch_referenced_message(ctx, ctx.message)
    bot_user = ctx.bot.user
    if message is None or bot_user is None:
        return None

    for _ in range(MAX_REPLY_DEPTH):
        if message is None:
            return None
        if message.author.id != bot_user.id:
            return None

        for embed in message.embeds:
            if embed.title and embed.url and "scryfall.com" in embed.url:
                return embed.title.strip()

        match = CARD_LINK_PATTERN.search(message.content or "")
        if match:
            return match.group(1).strip()

        message = await _fetch_referenced_message(ctx, message)

    return None


async def _fetch_referenced_message(
    ctx: commands.Context, message: discord.Message
) -> discord.Message | None:
    reference = message.reference
    if reference is None or reference.message_id is None:
        return None
    try:
        return await ctx.channel.fetch_message(reference.message_id)
    except discord.NotFound, discord.Forbidden, discord.HTTPException:
        logger.info("Could not fetch replied message %s", reference.message_id)
        return None


def get_formatted_card_info(card: ScryQueryCard) -> str:
    price = _format_price(card["price"])
    price_foil = _format_price(card["price_foil"])
    type_and_cost = replace_emojis(
        " ".join(part for part in (card["type_line"], card["mana_cost"]) if part)
    )
    oracle_text = replace_emojis(card["oracle_text"]).strip() or "*No oracle text.*"
    if len(oracle_text) > EMBED_DESCRIPTION_LIMIT:
        oracle_text = f"{oracle_text[: EMBED_DESCRIPTION_LIMIT - 3]}..."

    lines = []
    if type_and_cost:
        lines.append(f"*{type_and_cost}*")
    lines.append(oracle_text)
    lines.append("")
    lines.append(f"Price: {emojis.get('card')} {price}\t{emojis.get('cardfoil')} {price_foil}")
    return "\n" + "\n".join(lines)


def pick_winners(entries: Sequence[ClashEntry]) -> list[ClashEntry]:
    """Return every entry tied for the highest mana value."""

    if not entries:
        return []
    highest = max(entry["cmc"] for entry in entries)
    return [entry for entry in entries if entry["cmc"] == highest]


def replace_emojis(text: str) -> str:
    return re.sub(r"\{(.*?)\}", _replace_emoji_match, text)


def get_card_name_with_link(card: ScryQueryCard) -> str:
    return f"**[{card['name']}](<{card['scryfall_url']}>)**"


def _format_price(value: float | None) -> str:
    return f"${value:.2f}" if value is not None else "N/A"


def _replace_emoji_match(match: re.Match[str]) -> str:
    symbol = match.group(1).lower()
    # Hybrid/Phyrexian symbols use slashes (``{W/U}``, ``{W/P}``, ``{G/W/P}``)
    # but Discord emoji names cannot, so the guild names them ``manawu``,
    # ``manawp``, ``managwp``, etc.
    lookup = symbol.replace("/", "")
    return emojis.get(f"mana{lookup}", f"{{{symbol.upper()}}}")

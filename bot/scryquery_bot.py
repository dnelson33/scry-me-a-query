"""Discord command definitions and the bot instance."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from random import randint

import discord
from discord.ext import commands

import bot.emojis as emojis
from bot.config import load_settings
from bot.types import ClashEntry, ScryQueryBotResponse
from bot.utils import (
    format_response,
    get_card_name_with_link,
    get_reply_card_name,
    get_reply_query,
    pick_winners,
    replace_emojis,
)
from edhrec.service import get_edhrec_stats
from image_utils import generate_grid
from scryfall.api import ScryfallUnique
from scryfall.exceptions import NoCardsFound, ScryfallError
from scryfall.service import card_search, get_random_card_ruling, random_card

logger = logging.getLogger(__name__)

settings = load_settings()

EXPIRE_AFTER = 30
MAX_CLASH_PLAYERS = 16
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
NO_MENTIONS = discord.AllowedMentions.none()
MENTION_USERS_ONLY = discord.AllowedMentions(users=True)

# Per-user command cooldowns. These are deliberately generous: outbound HTTP
# already retries on 429/5xx, and the bot is small enough that throttling is not
# needed yet. Tighten them (or add a global limit) if spam starts causing
# latency or upstream rate limits. ``?clash`` is tighter because each use draws
# and renders up to 16 cards.
DEFAULT_COOLDOWN_RATE = 10
DEFAULT_COOLDOWN_PERIOD = 10.0
CLASH_COOLDOWN_RATE = 5
CLASH_COOLDOWN_PERIOD = 15.0

default_cooldown = commands.cooldown(
    DEFAULT_COOLDOWN_RATE, DEFAULT_COOLDOWN_PERIOD, commands.BucketType.user
)
clash_cooldown = commands.cooldown(
    CLASH_COOLDOWN_RATE, CLASH_COOLDOWN_PERIOD, commands.BucketType.user
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=settings.command_prefix,
    intents=intents,
    case_insensitive=True,
    allowed_mentions=NO_MENTIONS,
)


@bot.event
async def on_ready() -> None:
    if settings.emoji_guild_id is None:
        logger.warning("EMOJI_GUILD_ID is not set; mana symbols will render as text")
    else:
        guild = bot.get_guild(settings.emoji_guild_id)
        if guild is None:
            logger.warning(
                "Emoji guild %s not found; falling back to text mana symbols",
                settings.emoji_guild_id,
            )
        else:
            emojis.load(guild.emojis)
            logger.info("Loaded %d emoji(s) from guild %s", len(guild.emojis), guild.id)
            if not guild.emojis:
                logger.warning(
                    "Emoji guild %s has no emojis; falling back to text mana symbols",
                    guild.id,
                )

    user = bot.user
    logger.info("Logged in as %s (id=%s)", user, user.id if user else "unknown")


@bot.before_invoke
async def log_command(ctx: commands.Context) -> None:
    logger.info(
        "command=%s user=%s guild=%s",
        ctx.command.qualified_name if ctx.command else ctx.invoked_with,
        ctx.author.id,
        ctx.guild.id if ctx.guild else "dm",
    )


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.CommandNotFound):
        return

    prefix = ctx.prefix or settings.command_prefix
    command_name = ctx.command.qualified_name if ctx.command else ctx.invoked_with

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"Missing `{error.param.name}`. Try `{prefix}help {command_name}`.",
            allowed_mentions=NO_MENTIONS,
        )
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send(
            f"That argument did not look right. Try `{prefix}help {command_name}`.",
            allowed_mentions=NO_MENTIONS,
        )
        return

    if isinstance(error, commands.CommandOnCooldown):
        logger.info(
            "Command %s cooldown hit by user %s in guild %s (retry_after=%.2fs)",
            command_name,
            ctx.author.id,
            ctx.guild.id if ctx.guild else "dm",
            error.retry_after,
        )
        await ctx.send(
            f"Slow down a little — try again in {error.retry_after:.1f}s.",
            allowed_mentions=NO_MENTIONS,
        )
        return

    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            "You do not have permission to run that command.",
            allowed_mentions=NO_MENTIONS,
        )
        return

    original = error.original if isinstance(error, commands.CommandInvokeError) else error
    logger.error("Command %s failed: %s", command_name, error, exc_info=original)
    await ctx.send(
        "Well, this is embarrassing, but apparently you found a bug...",
        allowed_mentions=NO_MENTIONS,
    )


async def _send_card_response(ctx: commands.Context, response: ScryQueryBotResponse) -> None:
    """Send a formatted card response, omitting empty optional payloads."""

    if response["embed"] is not None:
        await ctx.send(
            response["response_message"],
            embed=response["embed"],
            files=response["files"],
            reference=ctx.message,
            mention_author=False,
            allowed_mentions=NO_MENTIONS,
        )
    else:
        await ctx.send(
            response["response_message"],
            files=response["files"],
            reference=ctx.message,
            mention_author=False,
            allowed_mentions=NO_MENTIONS,
        )


@bot.command()
@default_cooldown
async def sq(ctx: commands.Context, *, query: str = "") -> None:
    reply_query = await get_reply_query(ctx, f"{settings.command_prefix}sq")
    query = f"{reply_query} {query}".strip()

    if not query:
        await ctx.send(
            f"Give me something to search for, e.g. `{ctx.prefix}sq t:elf otag:manadork`.",
            allowed_mentions=NO_MENTIONS,
        )
        return

    async with ctx.typing():
        try:
            card_response = await asyncio.to_thread(card_search, query)
            bot_response = await asyncio.to_thread(
                format_response,
                card_response["cards"],
                card_response["scryfall_url"],
            )
        except ScryfallError:
            logger.exception("Scryfall search failed for %r", query)
            await ctx.send(
                "Scryfall is having trouble right now. Try again in a moment.",
                allowed_mentions=NO_MENTIONS,
            )
            return
        except Exception:
            logger.exception("Unexpected error building search response for %r", query)
            await ctx.send(
                "An unexpected error occurred while building that response.",
                allowed_mentions=NO_MENTIONS,
            )
            return

        await _send_card_response(ctx, bot_response)


@bot.command()
@default_cooldown
async def mycaptain(ctx: commands.Context) -> None:
    await sqrandom(ctx, query="is:commander")


@bot.command()
@default_cooldown
async def sqrandom(ctx: commands.Context, *, query: str = "") -> None:
    async with ctx.typing():
        try:
            card = await asyncio.to_thread(random_card, query)
        except NoCardsFound:
            await ctx.send(
                f"No cards found for `{query}`.",
                allowed_mentions=NO_MENTIONS,
            )
            return
        except ScryfallError:
            logger.exception("Random card lookup failed for %r", query)
            await ctx.send(
                "Scryfall is having trouble right now. Try again in a moment.",
                allowed_mentions=NO_MENTIONS,
            )
            return

        bot_response = format_response([card], card["scryfall_url"])
        await _send_card_response(ctx, bot_response)


@bot.command(aliases=["slivermetimbers"])
@default_cooldown
async def sliverme(ctx: commands.Context) -> None:
    await sqrandom(ctx, query="t:sliver")


@bot.command()
async def boo(ctx: commands.Context) -> None:
    await ctx.send(
        "https://tenor.com/view/hamster-ayasan-gif-24417561",
        allowed_mentions=NO_MENTIONS,
    )


@bot.command(aliases=["quoteme"])
@default_cooldown
async def flavortown(ctx: commands.Context) -> None:
    async with ctx.typing():
        try:
            card = await asyncio.to_thread(random_card, "has:flavor")
        except ScryfallError:
            logger.exception("Flavor lookup failed")
            await ctx.send(
                "Scryfall is having trouble right now. Try again in a moment.",
                allowed_mentions=NO_MENTIONS,
            )
            return

        flavor_text = card["flavor_text"]
        if not flavor_text:
            await ctx.send(
                "Couldn't find flavor text this time — try again.",
                allowed_mentions=NO_MENTIONS,
            )
            return

        embed = discord.Embed(
            description=f"{flavor_text}\n\n— {get_card_name_with_link(card)}",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed, allowed_mentions=NO_MENTIONS)


@bot.command()
@default_cooldown
async def edhrec(ctx: commands.Context, *, query: str) -> None:
    async with ctx.typing():
        commander_stats = await asyncio.to_thread(get_edhrec_stats, query)
        if not commander_stats:
            await ctx.send(
                f"No EDHRec data found for {query}.",
                reference=ctx.message,
                mention_author=False,
                allowed_mentions=NO_MENTIONS,
            )
            return

        lines = []
        rank = commander_stats["rank"]
        deck_count = commander_stats["commander_deck_count"]
        salt = commander_stats["salt"]
        if rank is not None:
            lines.append(f"Rank: #{rank}")
        if deck_count is not None:
            lines.append(f"Commander decks: {deck_count:,}")
        if salt is not None:
            lines.append(f"Salt score: {float(salt):.3f}")

        embed = discord.Embed(
            title=f"EDHRec Commander Stats: {query}",
            description="\n".join(lines) or "No stats available.",
            color=discord.Color.blue(),
        )
        await ctx.send(
            embed=embed,
            reference=ctx.message,
            mention_author=False,
            allowed_mentions=NO_MENTIONS,
        )


@bot.command(aliases=["randnum", "random"])
async def gamble(ctx: commands.Context, *, query: str = "7") -> None:
    try:
        sides = int(query)
    except ValueError:
        await ctx.send(
            "Please provide a positive integer > 1",
            reference=ctx.message,
            mention_author=False,
            allowed_mentions=NO_MENTIONS,
        )
        return

    if sides <= 1:
        message = "Please provide a positive integer > 1"
    elif sides > 250:
        message = "What game are you even playing?!?"
    else:
        message = f"🎲 You rolled: {randint(1, sides)}"

    await ctx.send(
        message,
        reference=ctx.message,
        mention_author=False,
        allowed_mentions=NO_MENTIONS,
    )


@bot.command(aliases=["datapriest", "edhtrack"])
async def arcaneoculus(ctx: commands.Context) -> None:
    await ctx.send(
        "https://arcane-oculus-edh.base44.app/",
        allowed_mentions=NO_MENTIONS,
    )


@bot.command()
@default_cooldown
async def asktheoracle(ctx: commands.Context, *, query: str = "") -> None:
    async with ctx.typing():
        try:
            ruling_response = await asyncio.to_thread(get_random_card_ruling, query)
        except NoCardsFound:
            ruling_response = None
        except ScryfallError:
            logger.exception("Oracle ruling lookup failed for %r", query)
            ruling_response = None

        if ruling_response and ruling_response["ruling"]:
            card = ruling_response["card"]
            ruling = ruling_response["ruling"]["ruling_text"] or "No ruling text."
            embed = discord.Embed(
                title="The Oracle has spoken",
                description=f"{get_card_name_with_link(card)}\n{ruling}",
                color=discord.Color.blue(),
            )
            if card["image_uri"]:
                embed.set_image(url=card["image_uri"])
            await ctx.send(
                embed=embed,
                reference=ctx.message,
                mention_author=False,
                allowed_mentions=NO_MENTIONS,
            )
            return

        oracle = discord.File(ASSETS_DIR / "oracle_pondering_orb.jpg", filename="oracle.jpg")
        embed = discord.Embed(
            title="The Oracle is pondering the orb and gives no response",
            color=discord.Color.blue(),
        )
        embed.set_image(url="attachment://oracle.jpg")
        await ctx.send(
            embed=embed,
            file=oracle,
            reference=ctx.message,
            mention_author=False,
            allowed_mentions=NO_MENTIONS,
        )


@bot.command(aliases=["thoughtclash"])
@clash_cooldown
async def clash(ctx: commands.Context) -> None:
    contestants: list[str] = []
    seen: set[int] = set()
    for user in [ctx.author, *ctx.message.mentions]:
        if user.id in seen:
            continue
        seen.add(user.id)
        contestants.append(user.mention)

    async with ctx.typing():
        if len(contestants) == 1:
            await ctx.send(
                "You need friends to play ThoughtClash, nerd!",
                allowed_mentions=NO_MENTIONS,
            )
            return

        if len(contestants) > MAX_CLASH_PLAYERS:
            await ctx.send(
                f"You have too many friends. Pick your {MAX_CLASH_PLAYERS} closest",
                allowed_mentions=NO_MENTIONS,
            )
            return

        await ctx.send(
            f"Highest CMC wins. Good luck! {' '.join(contestants)}",
            allowed_mentions=MENTION_USERS_ONLY,
        )

        entries: list[ClashEntry] = []
        drawn_cmcs: list[float] = []
        entry_message = ""

        try:
            for contestant in contestants:
                exclude = " ".join(f"mv!={cmc:g}" for cmc in drawn_cmcs)
                card = await asyncio.to_thread(random_card, exclude)
                cmc = card["cmc"]
                drawn_cmcs.append(cmc)
                entries.append(
                    {
                        "user": contestant,
                        "card_name": card["name"],
                        "card_image_url": card["image_uri"],
                        "cmc": cmc,
                    }
                )
                entry_message += (
                    f"{contestant}: {get_card_name_with_link(card)} "
                    f"({replace_emojis(card['mana_cost'])})\n"
                )
        except ScryfallError:
            logger.exception("ThoughtClash draw failed")
            await ctx.send(
                "Couldn't draw cards for that clash. Try again in a moment.",
                allowed_mentions=NO_MENTIONS,
            )
            return

        winners = pick_winners(entries)
        if len(winners) == 1:
            result = f"Congrats {winners[0]['user']}!!"
        else:
            result = f"It's a tie! Congrats {', '.join(w['user'] for w in winners)}!!"

        card_image = await asyncio.to_thread(
            generate_grid,
            [entry["card_image_url"] for entry in entries],
            [entry["card_name"] for entry in entries],
        )
        message = replace_emojis(f">>> {entry_message}\n\n{result}")

        embed = discord.Embed(
            title="ThoughtClash Results",
            description=message,
            color=discord.Color.magenta(),
        )
        file = discord.File(card_image, filename="grid.jpg")
        embed.set_image(url="attachment://grid.jpg")
        await ctx.send(
            file=file,
            embed=embed,
            allowed_mentions=MENTION_USERS_ONLY,
        )


@bot.command()
@default_cooldown
async def momir(ctx: commands.Context, *, query: str | None = None) -> None:
    cmc = randint(0, 16)
    if query is not None and query.strip():
        try:
            cmc = int(query)
        except ValueError:
            await ctx.send(
                "Please enter an integer between 0 and 16",
                reference=ctx.message,
                mention_author=False,
                allowed_mentions=NO_MENTIONS,
            )
            return

    if not 0 <= cmc <= 16:
        await ctx.send(
            "Please enter an integer between 0 and 16",
            reference=ctx.message,
            mention_author=False,
            allowed_mentions=NO_MENTIONS,
        )
        return

    await sqrandom(ctx, query=f"t:creature mv={cmc}")


@bot.command(aliases=["prints", "art", "arts"])
@default_cooldown
async def cards(ctx: commands.Context, *, query: str = "") -> None:
    invoked = (ctx.invoked_with or "cards").lower()
    invoked = "art" if invoked == "arts" else invoked

    try:
        unique = ScryfallUnique(invoked)
    except ValueError:
        await ctx.send(
            "Unknown card lookup mode.",
            allowed_mentions=NO_MENTIONS,
        )
        return

    card_name = query.strip() or await get_reply_card_name(ctx)
    previous_query = "" if card_name else await get_reply_query(ctx, f"{settings.command_prefix}sq")

    if not card_name and not previous_query:
        await ctx.send(
            f"Reply to a card or query, or provide a card name (`{ctx.prefix}{invoked} Sol Ring`).",
            reference=ctx.message,
            mention_author=False,
            allowed_mentions=NO_MENTIONS,
            delete_after=EXPIRE_AFTER,
        )
        return

    search_query = f"{card_name} f:any" if card_name else previous_query

    async with ctx.typing():
        try:
            card_response = await asyncio.to_thread(card_search, search_query, unique=unique)
            response = await asyncio.to_thread(
                format_response,
                card_response["cards"],
                card_response["scryfall_url"],
            )
        except ScryfallError:
            logger.exception("Card lookup failed for %r", search_query)
            await ctx.send(
                "Scryfall is having trouble right now. Try again in a moment.",
                allowed_mentions=NO_MENTIONS,
            )
            return

        await _send_card_response(ctx, response)

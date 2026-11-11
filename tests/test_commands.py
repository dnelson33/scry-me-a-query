from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import pytest
from discord.ext import commands

import bot.scryquery_bot as scryquery_bot
from bot.scryquery_bot import bot

EXPECTED_COMMANDS = {
    "sq",
    "sqrandom",
    "mycaptain",
    "sliverme",
    "boo",
    "flavortown",
    "edhrec",
    "gamble",
    "arcaneoculus",
    "asktheoracle",
    "clash",
    "momir",
    "cards",
    "help",
}


class FakeContext:
    def __init__(self, *, content: str = "", mentions: list[Any] | None = None) -> None:
        self.prefix = "?"
        self.invoked_with = "test"
        self.command: Any = None
        self.guild = SimpleNamespace(id=123)
        self.author = SimpleNamespace(id=1, mention="@tester")
        self.message = SimpleNamespace(
            content=content,
            reference=None,
            mentions=mentions or [],
        )
        self.sent: list[dict[str, Any]] = []

    async def send(self, content: str = "", **kwargs: Any) -> None:
        self.sent.append({"content": content, **kwargs})

    def typing(self) -> Any:
        class _Typing:
            async def __aenter__(self) -> None:
                return None

            async def __aexit__(self, *args: Any) -> None:
                return None

        return _Typing()


def test_expected_commands_are_registered() -> None:
    registered = {command.name for command in bot.commands}

    assert registered >= EXPECTED_COMMANDS


def test_aliases_are_registered() -> None:
    for alias, command_name in (
        ("slivermetimbers", "sliverme"),
        ("quoteme", "flavortown"),
        ("randnum", "gamble"),
        ("random", "gamble"),
        ("datapriest", "arcaneoculus"),
        ("edhtrack", "arcaneoculus"),
        ("thoughtclash", "clash"),
        ("prints", "cards"),
        ("art", "cards"),
        ("arts", "cards"),
    ):
        command = bot.get_command(alias)
        assert command is not None, alias
        assert command.name == command_name


def test_bot_has_no_mention_permissions_by_default() -> None:
    assert not bot.allowed_mentions.everyone
    assert not bot.allowed_mentions.users
    assert not bot.allowed_mentions.roles


def test_oracle_asset_is_present() -> None:
    assert (scryquery_bot.ASSETS_DIR / "oracle_pondering_orb.jpg").is_file()


@pytest.mark.asyncio
async def test_gamble_rolls_within_range() -> None:
    ctx = FakeContext()

    await scryquery_bot.gamble.callback(ctx, query="20")

    assert len(ctx.sent) == 1
    message = ctx.sent[0]["content"]
    assert message.startswith("🎲 You rolled: ")
    assert 1 <= int(message.removeprefix("🎲 You rolled: ")) <= 20


@pytest.mark.asyncio
async def test_gamble_rejects_non_numbers() -> None:
    ctx = FakeContext()

    await scryquery_bot.gamble.callback(ctx, query="lots")

    assert ctx.sent[0]["content"] == "Please provide a positive integer > 1"


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["0", "1", "-4"])
async def test_gamble_rejects_small_values(value: str) -> None:
    ctx = FakeContext()

    await scryquery_bot.gamble.callback(ctx, query=value)

    assert ctx.sent[0]["content"] == "Please provide a positive integer > 1"


@pytest.mark.asyncio
async def test_gamble_rejects_absurd_values() -> None:
    ctx = FakeContext()

    await scryquery_bot.gamble.callback(ctx, query="251")

    assert ctx.sent[0]["content"] == "What game are you even playing?!?"


@pytest.mark.asyncio
async def test_momir_rejects_out_of_range_mana_value() -> None:
    ctx = FakeContext()

    await scryquery_bot.momir.callback(ctx, query="17")

    assert ctx.sent[0]["content"] == "Please enter an integer between 0 and 16"


@pytest.mark.asyncio
async def test_momir_rejects_non_numbers() -> None:
    ctx = FakeContext()

    await scryquery_bot.momir.callback(ctx, query="cheese")

    assert ctx.sent[0]["content"] == "Please enter an integer between 0 and 16"


@pytest.mark.asyncio
async def test_clash_requires_an_opponent() -> None:
    ctx = FakeContext()

    await scryquery_bot.clash.callback(ctx)

    assert ctx.sent[0]["content"] == "You need friends to play ThoughtClash, nerd!"


@pytest.mark.asyncio
async def test_sq_without_query_asks_for_one() -> None:
    ctx = FakeContext(content="?sq")

    await scryquery_bot.sq.callback(ctx, query="")

    assert "Give me something to search for" in ctx.sent[0]["content"]


@pytest.mark.asyncio
async def test_command_not_found_is_ignored() -> None:
    ctx = FakeContext()

    await scryquery_bot.on_command_error(ctx, commands.CommandNotFound("nope"))

    assert ctx.sent == []


@pytest.mark.asyncio
async def test_missing_argument_gets_help_hint() -> None:
    ctx = FakeContext()
    ctx.command = SimpleNamespace(qualified_name="edhrec")
    error = commands.MissingRequiredArgument(SimpleNamespace(name="query", displayed_name="query"))

    await scryquery_bot.on_command_error(ctx, error)

    assert ctx.sent[0]["content"] == "Missing `query`. Try `?help edhrec`."


@pytest.mark.asyncio
async def test_cooldown_gets_friendly_message(caplog: pytest.LogCaptureFixture) -> None:
    ctx = FakeContext()
    ctx.command = SimpleNamespace(qualified_name="sq")
    error = commands.CommandOnCooldown(
        commands.Cooldown(2, 10),
        retry_after=4.24,
        type=commands.BucketType.user,
    )

    with caplog.at_level(logging.INFO, logger="bot.scryquery_bot"):
        await scryquery_bot.on_command_error(ctx, error)

    assert "4.2s" in ctx.sent[0]["content"]
    assert "Command sq cooldown hit by user 1 in guild 123" in caplog.text
    assert "retry_after=4.24s" in caplog.text


@pytest.mark.asyncio
async def test_unexpected_error_is_reported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    ctx = FakeContext()
    ctx.command = SimpleNamespace(qualified_name="sq")

    await scryquery_bot.on_command_error(ctx, RuntimeError("boom"))

    assert "found a bug" in ctx.sent[0]["content"]
    assert "boom" in caplog.text


@pytest.mark.asyncio
async def test_send_card_response_omits_embed_when_missing() -> None:
    ctx = FakeContext()

    await scryquery_bot._send_card_response(
        ctx,
        {"response_message": "hello", "files": [], "embed": None},
    )

    assert ctx.sent[0]["content"] == "hello"
    assert "embed" not in ctx.sent[0]
    assert ctx.sent[0]["mention_author"] is False

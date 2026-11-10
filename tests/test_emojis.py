from __future__ import annotations

from types import SimpleNamespace

import pytest

import bot.emojis as emojis


@pytest.fixture(autouse=True)
def _reset_emojis() -> None:
    emojis.load([])
    yield
    emojis.load([])


def test_lookup_is_case_insensitive() -> None:
    emojis.load(
        [
            SimpleNamespace(name="manaW", id=1),
            SimpleNamespace(name="card", id=2),
        ]
    )

    assert emojis.get("manaw") == "<:manaW:1>"
    assert emojis.get("manaW") == "<:manaW:1>"
    assert emojis.get("card") == "<:card:2>"


def test_missing_emoji_uses_fallback() -> None:
    emojis.load([SimpleNamespace(name="card", id=2)])

    assert emojis.get("manaU", "{U}") == "{U}"
    assert emojis.get("manaU") == ""


def test_is_loaded_reflects_state() -> None:
    assert emojis.is_loaded() is False

    emojis.load([SimpleNamespace(name="card", id=1)])

    assert emojis.is_loaded() is True

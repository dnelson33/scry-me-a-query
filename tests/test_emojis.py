from __future__ import annotations

from types import SimpleNamespace

import pytest

import bot.emojis as emojis
from bot.utils import replace_emojis


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


def test_replace_emojis_handles_hybrid_and_phyrexian_symbols() -> None:
    emojis.load(
        [
            SimpleNamespace(name="manaw", id=1),
            SimpleNamespace(name="manawu", id=2),
            SimpleNamespace(name="manawp", id=3),
            SimpleNamespace(name="managwp", id=4),
        ]
    )

    assert replace_emojis("{W}{W/U}{W/P}{G/W/P}") == (
        "<:manaw:1><:manawu:2><:manawp:3><:managwp:4>"
    )


def test_replace_emojis_keeps_text_when_symbol_is_unknown() -> None:
    emojis.load([SimpleNamespace(name="manaw", id=1)])

    assert replace_emojis("{2/W}") == "{2/W}"
    assert replace_emojis("{10}") == "{10}"


def test_is_loaded_reflects_state() -> None:
    assert emojis.is_loaded() is False

    emojis.load([SimpleNamespace(name="card", id=1)])

    assert emojis.is_loaded() is True

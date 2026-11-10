from __future__ import annotations

from io import BytesIO
from typing import Any

import pytest

import bot.utils as utils
from bot.utils import format_response, get_formatted_card_info, pick_winners
from scryfall.service.service import _map_card
from tests.helpers import CARD_IMAGE_URI, make_card


@pytest.fixture
def fake_grid(monkeypatch: pytest.MonkeyPatch) -> list[tuple[list[str], list[str]]]:
    calls: list[tuple[list[str], list[str]]] = []

    def _generate(urls: list[str], labels: list[str] | None = None) -> BytesIO:
        calls.append((list(urls), list(labels or [])))
        return BytesIO(b"\xff\xd8\xff\xe0fake-jpeg")

    monkeypatch.setattr(utils, "generate_grid", _generate)
    return calls


def _cards(count: int) -> list[dict[str, Any]]:
    return [
        _map_card(
            make_card(
                name=f"Card {index}",
                image_uris={"normal": f"https://cards.scryfall.io/normal/{index}.jpg"},
            )
        )
        for index in range(count)
    ]


def test_empty_result_has_message_only(fake_grid: list[Any]) -> None:
    response = format_response([], "https://scryfall.com/search?q=nothing")

    assert "No data found" in response["response_message"]
    assert response["files"] == []
    assert response["embed"] is None
    assert fake_grid == []


def test_single_card_uses_embed_not_upload(fake_grid: list[Any]) -> None:
    response = format_response(_cards(1))

    assert response["files"] == []
    assert response["embed"] is not None
    assert response["embed"].image.url == "https://cards.scryfall.io/normal/0.jpg"
    assert fake_grid == []


def test_single_card_without_image_has_no_image(fake_grid: list[Any], card_factory: Any) -> None:
    card = _map_card(card_factory(image_uris={}))

    response = format_response([card])

    assert response["embed"] is not None
    assert response["embed"].image.url is None


def test_multi_card_batches_images(fake_grid: list[Any]) -> None:
    response = format_response(_cards(2), "https://scryfall.com/search?q=t%3Aelf")

    assert len(response["files"]) == 1
    assert response["files"][0].filename == "cards_0.jpg"
    assert fake_grid[0][1] == ["Card 0", "Card 1"]
    assert "ScryQuery Results: 2 cards" in response["response_message"]


def test_response_limit_splits_into_two_grids(fake_grid: list[Any]) -> None:
    response = format_response(_cards(32))

    assert [file.filename for file in response["files"]] == ["cards_0.jpg", "cards_16.jpg"]
    assert [len(call[0]) for call in fake_grid] == [16, 16]
    assert "Displaying first 32 results" not in response["response_message"]


def test_response_limit_truncates_larger_results(fake_grid: list[Any]) -> None:
    response = format_response(_cards(40))

    assert [file.filename for file in response["files"]] == ["cards_0.jpg", "cards_16.jpg"]
    assert "Displaying first 32 results" in response["response_message"]


def test_missing_image_is_forwarded_to_grid(fake_grid: list[Any], card_factory: Any) -> None:
    cards = [
        _map_card(card_factory(name="With Art")),
        _map_card(card_factory(name="No Art", image_uris={})),
    ]

    format_response(cards)

    assert fake_grid[0][0][1] == ""
    assert fake_grid[0][1] == ["With Art", "No Art"]


def test_formatted_card_info_falls_back_for_missing_fields(card_factory: Any) -> None:
    card = _map_card(
        card_factory(
            mana_cost="",
            type_line="",
            oracle_text="",
            prices={},
        )
    )

    info = get_formatted_card_info(card)

    assert "No oracle text" in info
    assert "$" not in info
    assert "N/A" in info


def test_formatted_card_info_replaces_mana_symbols(card_factory: Any) -> None:
    info = get_formatted_card_info(_map_card(card_factory()))

    assert "{T}" in info
    assert "{C}" in info


def test_formatted_card_info_truncates_long_text(card_factory: Any) -> None:
    card = _map_card(card_factory(oracle_text="A" * 5000))

    info = get_formatted_card_info(card)

    assert len(info) < utils.EMBED_DESCRIPTION_LIMIT + 200
    assert info.count("...") >= 1


def test_pick_winners_returns_all_ties() -> None:
    entries = [
        {"user": "a", "card_name": "A", "card_image_url": CARD_IMAGE_URI, "cmc": 3.0},
        {"user": "b", "card_name": "B", "card_image_url": CARD_IMAGE_URI, "cmc": 5.0},
        {"user": "c", "card_name": "C", "card_image_url": CARD_IMAGE_URI, "cmc": 5.0},
    ]

    assert [entry["user"] for entry in pick_winners(entries)] == ["b", "c"]


def test_pick_winners_handles_empty_input() -> None:
    assert pick_winners([]) == []

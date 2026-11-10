from __future__ import annotations

from typing import Any

from scryfall.service.service import _get_pages, _map_card


def test_maps_single_faced_card(card_factory: Any) -> None:
    card = _map_card(card_factory())

    assert card["name"] == "Sol Ring"
    assert card["image_uri"].endswith("ab.jpg")
    assert card["mana_cost"] == "{1}"
    assert card["price"] == 1.5
    assert card["price_foil"] == 9.99
    assert card["cmc"] == 1.0


def test_maps_multi_face_card_using_face_images() -> None:
    card = _map_card(
        {
            "id": "dfc",
            "name": "Delver of Secrets // Insectile Aberration",
            "scryfall_uri": "https://scryfall.com/card/isd/51",
            "cmc": 1.0,
            "prices": {"usd": "0.25"},
            "card_faces": [
                {
                    "name": "Delver of Secrets",
                    "mana_cost": "{U}",
                    "type_line": "Creature — Human Insect",
                    "oracle_text": "At the beginning of your upkeep, look at the top card.",
                    "image_uris": {"normal": "https://cards.scryfall.io/normal/front/delver.jpg"},
                },
                {
                    "name": "Insectile Aberration",
                    "mana_cost": "",
                    "type_line": "Creature — Human Insect",
                    "oracle_text": "Flying",
                    "image_uris": {"normal": "https://cards.scryfall.io/normal/back/insect.jpg"},
                },
            ],
        }
    )

    assert card["image_uri"].endswith("delver.jpg")
    assert card["mana_cost"] == "{U}"
    assert card["type_line"] == "Creature — Human Insect // Creature — Human Insect"
    assert "//" in card["oracle_text"]
    assert card["price"] == 0.25


def test_maps_prepare_layout_from_top_level_images() -> None:
    card = _map_card(
        {
            "id": "prepare",
            "name": "Emeritus of Woe // Emeritus of Abundance",
            "scryfall_uri": "https://scryfall.com/card/prepare/1",
            "cmc": 4.0,
            "prices": {},
            "image_uris": {"normal": "https://cards.scryfall.io/normal/front/top.jpg"},
            "card_faces": [
                {"name": "Emeritus of Woe", "oracle_text": "Front text"},
                {"name": "Emeritus of Abundance", "oracle_text": "Back text"},
            ],
        }
    )

    # Faces have no image_uris; the top-level fallback must be used.
    assert card["image_uri"] == "https://cards.scryfall.io/normal/front/top.jpg"


def test_missing_image_becomes_empty_string() -> None:
    card = _map_card(
        {
            "id": "no-art",
            "name": "Mystery Card",
            "scryfall_uri": "https://scryfall.com/card/x/1",
            "prices": {},
        }
    )

    assert card["image_uri"] == ""
    assert card["price"] is None
    assert card["mana_cost"] == ""
    assert card["oracle_text"] == ""


def test_flavor_text_falls_back_to_card_faces() -> None:
    card = _map_card(
        {
            "id": "flavor",
            "name": "Delver of Secrets // Insectile Aberration",
            "scryfall_uri": "https://scryfall.com/card/isd/51",
            "prices": {},
            "card_faces": [
                {
                    "name": "Delver of Secrets",
                    "flavor_text": "In laboratories, vermin are dissected.",
                },
                {"name": "Insectile Aberration"},
            ],
        }
    )

    assert card["flavor_text"] == "In laboratories, vermin are dissected."


def test_bad_price_is_ignored(card_factory: Any) -> None:
    card = _map_card(card_factory(prices={"usd": "not-a-number", "usd_foil": ""}))

    assert card["price"] is None
    assert card["price_foil"] is None


def test_pages_include_every_page(card_factory: Any) -> None:
    data = [card_factory(name=f"Card {index}") for index in range(175)]
    response = {
        "url": "https://scryfall.com/search?q=t%3Aelf",
        "total_cards": 176,
        "has_more": True,
        "next_page": "https://api.scryfall.com/cards/search?page=2&q=t%3Aelf",
        "data": data,
    }

    pages = _get_pages(response)

    assert [page["page_number"] for page in pages] == [1, 2]
    assert all("page=" in page["page_url"] for page in pages)


def test_pages_for_single_page(card_factory: Any) -> None:
    response = {
        "url": "https://scryfall.com/search?q=sol",
        "total_cards": 1,
        "has_more": False,
        "data": [card_factory()],
    }

    assert _get_pages(response) == [
        {"page_number": 1, "page_url": "https://scryfall.com/search?q=sol"}
    ]

"""Internal (already mapped) shapes returned by the service layer."""

from __future__ import annotations

from typing import TypedDict


class ScryQueryCard(TypedDict):
    scryfall_url: str
    image_uri: str
    name: str
    mana_cost: str
    type_line: str
    oracle_text: str
    price: float | None
    price_foil: float | None
    flavor_text: str | None
    rulings_url: str | None
    cmc: float


class PageInfo(TypedDict):
    page_number: int
    page_url: str


class CardSearchResponse(TypedDict):
    scryfall_url: str
    total_cards: int
    pages: list[PageInfo]
    cards: list[ScryQueryCard]


class CardRuling(TypedDict):
    ruling_text: str | None
    source: str | None
    published_at: str | None


class CardRulingsResponse(TypedDict):
    card: ScryQueryCard
    rulings: list[CardRuling]


class RandomCardRulingResponse(TypedDict):
    card: ScryQueryCard
    ruling: CardRuling | None

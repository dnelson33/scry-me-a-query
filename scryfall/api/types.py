"""Shapes for Scryfall's HTTP API.

Scryfall omits fields that do not apply to a given card (for example
``image_uris`` is usually only present on the top level for single-faced
cards), so optional keys are marked with :class:`~typing.NotRequired`.
"""

from __future__ import annotations

from enum import Enum
from typing import NotRequired, TypedDict


class ScryfallImageUris(TypedDict):
    small: str
    normal: str
    large: str
    png: str
    art_crop: str
    border_crop: str


class ScryfallPrices(TypedDict):
    usd: NotRequired[str | None]
    usd_foil: NotRequired[str | None]
    usd_etched: NotRequired[str | None]
    eur: NotRequired[str | None]
    eur_foil: NotRequired[str | None]
    tix: NotRequired[str | None]


class ScryfallPurchaseUris(TypedDict):
    tcgplayer: NotRequired[str]
    cardmarket: NotRequired[str]
    cardhoarder: NotRequired[str]


class ScryfallCardFace(TypedDict):
    name: str
    mana_cost: NotRequired[str]
    type_line: NotRequired[str]
    oracle_text: NotRequired[str]
    flavor_text: NotRequired[str]
    colors: NotRequired[list[str]]
    power: NotRequired[str]
    toughness: NotRequired[str]
    image_uris: NotRequired[ScryfallImageUris]


class ScryfallUnique(Enum):
    CARDS = "cards"
    ART = "art"
    PRINTS = "prints"


class ScryfallOrder(Enum):
    NAME = "name"
    RELEASED = "released"
    COLOR = "color"
    TYPE = "type"
    CMC = "cmc"
    POWER = "power"
    TOUGHNESS = "toughness"
    EDHREC = "edhrec"


class ScryfallOrderDir(Enum):
    AUTO = "auto"
    ASC = "asc"
    DESC = "desc"


class ScryfallCard(TypedDict):
    id: str
    name: str
    scryfall_uri: str
    uri: NotRequired[str]
    released_at: NotRequired[str]
    image_uris: NotRequired[ScryfallImageUris]
    mana_cost: NotRequired[str]
    cmc: NotRequired[float]
    type_line: NotRequired[str]
    oracle_text: NotRequired[str]
    flavor_text: NotRequired[str]
    power: NotRequired[str | None]
    toughness: NotRequired[str | None]
    colors: NotRequired[list[str]]
    color_identity: NotRequired[list[str]]
    keywords: NotRequired[list[str]]
    legalities: NotRequired[dict[str, str]]
    reserved: NotRequired[bool]
    foil: NotRequired[bool]
    nonfoil: NotRequired[bool]
    game_changer: NotRequired[bool]
    reprint: NotRequired[bool]
    set_id: NotRequired[str]
    set_name: NotRequired[str]
    set_uri: NotRequired[str]
    set_search_uri: NotRequired[str]
    scryfall_set_uri: NotRequired[str]
    rulings_uri: NotRequired[str]
    prints_search_uri: NotRequired[str]
    collector_number: NotRequired[str]
    rarity: NotRequired[str]
    artist: NotRequired[str]
    prices: NotRequired[ScryfallPrices]
    purchase_uris: NotRequired[ScryfallPurchaseUris]
    produced_mana: NotRequired[list[str] | None]
    card_faces: NotRequired[list[ScryfallCardFace]]


class ScryfallCardSearchRequest(TypedDict, total=False):
    q: str | None
    order: str | None
    unique: str | None
    dir: str | None
    include_extras: bool | None
    include_multilingual: bool | None
    include_variations: bool | None
    page: int | None
    format: str | None
    pretty: bool | None


class ScryfallCardSearchResponse(TypedDict):
    url: str
    total_cards: int
    has_more: bool
    data: list[ScryfallCard]
    next_page: NotRequired[str]


class ScryfallRandomCardRequest(TypedDict, total=False):
    q: str | None
    format: str | None
    face: str | None
    version: str | None
    pretty: bool | None


class ScryfallRuling(TypedDict):
    oracle_id: str
    source: str
    published_at: str
    comment: str


class ScryfallRulingsResponse(TypedDict):
    has_more: bool
    data: list[ScryfallRuling]

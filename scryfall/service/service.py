"""Business logic for Scryfall queries.

The API layer deals with HTTP and raw JSON; this module turns raw cards into
the flatter :class:`ScryQueryCard` shape used by Discord commands, and adds
query handling that Scryfall itself does not do (default format filtering).
"""

from __future__ import annotations

import math
import re
from random import randrange
from typing import cast

from scryfall.api import card_rulings_request, card_search_request, random_card_request
from scryfall.api.types import (
    ScryfallCard,
    ScryfallCardFace,
    ScryfallCardSearchRequest,
    ScryfallCardSearchResponse,
    ScryfallImageUris,
    ScryfallOrder,
    ScryfallUnique,
)
from scryfall.exceptions import NoCardsFound
from scryfall.service.types import (
    CardRuling,
    CardRulingsResponse,
    CardSearchResponse,
    PageInfo,
    RandomCardRulingResponse,
    ScryQueryCard,
)

ORDER_PATTERN = re.compile(r"(?<!\w)order:(\S+)", re.IGNORECASE)
FORMAT_PATTERN = re.compile(r"(?<!\w)(?:f|format|legal):\S+", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s+")
VALID_ORDERS = {order.value for order in ScryfallOrder}

DEFAULT_ORDER = ScryfallOrder.EDHREC.value
DEFAULT_FORMAT = "f:edh"


def _prepare_query(search_text: str) -> tuple[str, str]:
    """Split Scryfall modifiers out of a user query before it is encoded.

    Modifiers must be parsed from the raw text: once the query is URL-encoded,
    tokens like ``order:cmc`` become ``order%3Acmc`` and no longer match.
    """

    query = (search_text or "").strip()
    order = DEFAULT_ORDER

    match = ORDER_PATTERN.search(query)
    if match:
        candidate = match.group(1).lower()
        if candidate in VALID_ORDERS:
            order = candidate
        query = (query[: match.start()] + query[match.end() :]).strip()

    # Respect any explicit format/legality filter, including f:any. Otherwise
    # default searches to Commander-legal cards.
    if not FORMAT_PATTERN.search(query):
        query = f"{query} {DEFAULT_FORMAT}".strip()

    return WHITESPACE_PATTERN.sub(" ", query).strip(), order


def card_search(
    search_text: str,
    page: int | None = None,
    unique: ScryfallUnique | None = None,
) -> CardSearchResponse:
    query, order = _prepare_query(search_text)

    request: ScryfallCardSearchRequest = {
        "q": query,
        "order": order,
        "page": page,
        "unique": unique.value if unique else None,
    }
    api_response = card_search_request(request)

    return {
        "scryfall_url": api_response["url"],
        "total_cards": api_response["total_cards"],
        "pages": _get_pages(api_response),
        "cards": [_map_card(card) for card in api_response["data"]],
    }


def random_card(search_text: str) -> ScryQueryCard:
    api_response = random_card_request({"q": search_text or ""})
    if api_response is None:
        raise NoCardsFound(search_text)
    return _map_card(api_response)


def get_rulings(card: ScryQueryCard) -> CardRulingsResponse:
    rulings_url = card["rulings_url"]
    api_response = card_rulings_request(rulings_url) if rulings_url else None

    rulings_data = api_response["data"] if api_response else []
    rulings: list[CardRuling] = [
        {
            "ruling_text": ruling.get("comment"),
            "published_at": ruling.get("published_at"),
            "source": ruling.get("source"),
        }
        for ruling in rulings_data
    ]

    return {"card": card, "rulings": rulings}


def get_random_card_ruling(search_text: str) -> RandomCardRulingResponse:
    card = random_card(search_text)
    rulings = get_rulings(card)["rulings"]
    if not rulings:
        return {"card": card, "ruling": None}
    return {"card": card, "ruling": rulings[randrange(len(rulings))]}


def _get_pages(api_response: ScryfallCardSearchResponse) -> list[PageInfo]:
    data = api_response.get("data") or []
    next_page = api_response.get("next_page")
    if not next_page or not data:
        return [{"page_number": 1, "page_url": api_response["url"]}]

    per_page = len(data)
    total_cards = api_response.get("total_cards", per_page)
    total_pages = max(1, math.ceil(total_cards / per_page))

    return [
        {
            "page_number": page_number,
            "page_url": re.sub(r"page=\d+", f"page={page_number}", next_page),
        }
        for page_number in range(1, total_pages + 1)
    ]


def _parse_price(value: str | None) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _join_face_field(faces: list[ScryfallCardFace], key: str, separator: str = " // ") -> str:
    values = [str(face.get(key, "")).strip() for face in faces]
    return separator.join(value for value in values if value)


def _map_card(scryfall_card: ScryfallCard) -> ScryQueryCard:
    faces = scryfall_card.get("card_faces") or []
    top_level_images = cast(ScryfallImageUris, scryfall_card.get("image_uris") or {})

    flavor_text: str | None
    if faces:
        front = faces[0]
        front_images = cast(ScryfallImageUris, front.get("image_uris") or {})
        image_uri = front_images.get("normal") or top_level_images.get("normal", "")

        oracle_text = _join_face_field(faces, "oracle_text", separator="\n//\n")
        type_line = _join_face_field(faces, "type_line")
        mana_cost = _join_face_field(faces, "mana_cost")
        # Multi-face cards keep flavor text on the faces, not the top level.
        flavor_text = (
            scryfall_card.get("flavor_text")
            or _join_face_field(faces, "flavor_text", separator="\n//\n")
            or None
        )
    else:
        image_uri = top_level_images.get("normal", "")
        oracle_text = scryfall_card.get("oracle_text") or ""
        type_line = scryfall_card.get("type_line") or ""
        mana_cost = scryfall_card.get("mana_cost") or ""
        flavor_text = scryfall_card.get("flavor_text")

    prices = scryfall_card.get("prices") or {}

    return {
        "scryfall_url": scryfall_card.get("scryfall_uri") or scryfall_card.get("uri") or "",
        "image_uri": image_uri,
        "name": scryfall_card.get("name") or "Unknown card",
        "mana_cost": mana_cost,
        "type_line": type_line,
        "oracle_text": oracle_text,
        "price": _parse_price(prices.get("usd") or prices.get("usd_foil")),
        "price_foil": _parse_price(prices.get("usd_foil")),
        "flavor_text": flavor_text or None,
        "rulings_url": scryfall_card.get("rulings_uri"),
        "cmc": float(scryfall_card.get("cmc") or 0),
    }

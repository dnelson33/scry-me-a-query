"""Raw HTTP wrappers around the Scryfall REST API."""

from __future__ import annotations

import logging
from typing import cast

import requests

import http_client
from scryfall.api.types import (
    ScryfallCard,
    ScryfallCardSearchRequest,
    ScryfallCardSearchResponse,
    ScryfallRandomCardRequest,
    ScryfallRulingsResponse,
)
from scryfall.exceptions import ScryfallAPIError

BASE_URL = "https://api.scryfall.com"
SCRYFALL_URL = "https://scryfall.com/search"
JSON_HEADERS = {"Accept": "application/json"}

logger = logging.getLogger(__name__)


def _params(request: dict[str, object]) -> dict[str, str]:
    return {
        key: str(value).strip()
        for key, value in request.items()
        if value is not None and str(value).strip()
    }


def _raise_for_status(response: requests.Response, url: str) -> None:
    if response.status_code >= 400:
        raise ScryfallAPIError(response.status_code, url, response.text[:300])


def card_search_request(request: ScryfallCardSearchRequest) -> ScryfallCardSearchResponse:
    endpoint = "cards/search"

    response = http_client.get(
        f"{BASE_URL}/{endpoint}",
        params=_params(cast(dict[str, object], request)),
        headers=JSON_HEADERS,
    )
    scryfall_url = response.url.replace(f"{BASE_URL}/{endpoint}", SCRYFALL_URL)

    if response.status_code == 404:
        return {
            "url": scryfall_url,
            "total_cards": 0,
            "has_more": False,
            "data": [],
        }

    _raise_for_status(response, scryfall_url)
    data = cast(ScryfallCardSearchResponse, response.json())
    data["url"] = scryfall_url
    return data


def random_card_request(request: ScryfallRandomCardRequest) -> ScryfallCard | None:
    endpoint = "cards/random"

    response = http_client.get(
        f"{BASE_URL}/{endpoint}",
        params=_params(cast(dict[str, object], request)),
        headers=JSON_HEADERS,
    )
    if response.status_code == 404:
        return None
    _raise_for_status(response, response.url)
    return cast(ScryfallCard, response.json())


def card_rulings_request(url: str) -> ScryfallRulingsResponse | None:
    response = http_client.get(url, headers=JSON_HEADERS)
    if response.status_code == 404:
        return None
    _raise_for_status(response, url)
    return cast(ScryfallRulingsResponse, response.json())

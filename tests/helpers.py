"""Shared test helpers (not a pytest plugin)."""

from __future__ import annotations

import json
from typing import Any

import requests

CARD_IMAGE_URI = "https://cards.scryfall.io/normal/front/a/b/ab.jpg"


class FakeResponse:
    """Small stand-in for ``requests.Response`` used by HTTP tests."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: Any = None,
        content: bytes = b"",
        url: str = "https://api.scryfall.com/cards/search",
        reason: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.status = status_code
        self._json = json_data
        self.content = content
        self.url = url
        self.reason = reason or ("OK" if status_code < 400 else "Error")
        self.headers = headers or {}

    def json(self) -> Any:
        return self._json

    @property
    def text(self) -> str:
        if self._json is not None:
            return json.dumps(self._json)
        return self.content.decode("utf-8", errors="replace")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(
                f"{self.status_code} error",
                response=self,  # type: ignore[arg-type]
            )


def make_card(**overrides: Any) -> dict[str, Any]:
    card: dict[str, Any] = {
        "id": "card-id",
        "name": "Sol Ring",
        "scryfall_uri": "https://scryfall.com/card/lea/1",
        "mana_cost": "{1}",
        "type_line": "Artifact",
        "oracle_text": "{T}: Add {C}{C}.",
        "cmc": 1.0,
        "prices": {"usd": "1.50", "usd_foil": "9.99"},
        "image_uris": {
            "small": CARD_IMAGE_URI,
            "normal": CARD_IMAGE_URI,
            "large": CARD_IMAGE_URI,
            "png": CARD_IMAGE_URI,
            "art_crop": CARD_IMAGE_URI,
            "border_crop": CARD_IMAGE_URI,
        },
        "rulings_uri": "https://api.scryfall.com/cards/card-id/rulings",
    }
    card.update(overrides)
    return card

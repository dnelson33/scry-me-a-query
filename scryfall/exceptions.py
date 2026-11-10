"""Domain exceptions raised by the Scryfall integration."""

from __future__ import annotations


class ScryfallError(Exception):
    """Base class for errors the bot can present to users."""


class ScryfallAPIError(ScryfallError):
    """Scryfall returned a non-success HTTP status."""

    def __init__(self, status_code: int, url: str, body: str = "") -> None:
        self.status_code = status_code
        self.url = url
        self.body = body
        super().__init__(f"Scryfall returned HTTP {status_code} for {url}")


class NoCardsFound(ScryfallError):
    """A query returned no cards."""

    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__(f"No cards found for query: {query!r}")

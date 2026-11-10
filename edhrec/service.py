"""Minimal EDHRec client.

EDHRec exposes the page data used by its Next.js frontend at
``https://json.edhrec.com/pages/commanders/<slug>.json``. Fetching that
directly is a single request with no build-id negotiation, which is both faster
and less brittle than scraping the rendered page.
"""

from __future__ import annotations

import logging
import re
import unicodedata

import http_client
from edhrec.types import EDHRecCommander

JSON_BASE_URL = "https://json.edhrec.com/pages/commanders"
REQUEST_TIMEOUT: tuple[float, float] = (5.0, 20.0)

SLUG_SEPARATOR = re.compile(r"[\s-]+")
SLUG_ALLOWED = re.compile(r"[^a-z0-9\s-]")

logger = logging.getLogger(__name__)


def _slugify(card_name: str) -> str:
    """Convert a Scryfall card name into EDHRec's URL slug.

    EDHRec uses the front face of multi-face cards, transliterates accents to
    ASCII (``Éowyn`` → ``eowyn``), drops punctuation (including ``&``), and
    joins words with single hyphens.
    """

    front_face = card_name.split("//", 1)[0]
    ascii_name = (
        unicodedata.normalize("NFKD", front_face).encode("ascii", "ignore").decode("ascii").lower()
    )
    without_punctuation = SLUG_ALLOWED.sub("", ascii_name)
    return SLUG_SEPARATOR.sub("-", without_punctuation).strip("-")


def get_edhrec_stats(card_name: str) -> EDHRecCommander | None:
    """Return rank/deck count/salt for ``card_name``, or ``None`` if unknown."""

    slug = _slugify(card_name)
    if not slug:
        return None

    url = f"{JSON_BASE_URL}/{slug}.json"
    try:
        response = http_client.get(
            url,
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
    except Exception:
        logger.exception("Failed to fetch EDHRec data for %s", card_name)
        return None

    card = data.get("container", {}).get("json_dict", {}).get("card", {})
    if not card:
        logger.info("EDHRec returned no card data for %s", card_name)
        return None

    return {
        "rank": card.get("rank"),
        "commander_deck_count": card.get("num_decks"),
        "salt": card.get("salt"),
    }

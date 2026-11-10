"""Types for EDHRec responses."""

from __future__ import annotations

from typing import TypedDict


class EDHRecCommander(TypedDict):
    salt: float | None
    rank: int | None
    commander_deck_count: int | None

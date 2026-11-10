from __future__ import annotations

from typing import Any

import pytest

import http_client
from edhrec import service
from tests.helpers import FakeResponse


@pytest.mark.parametrize(
    ("name", "slug"),
    [
        ("Atraxa, Praetors' Voice", "atraxa-praetors-voice"),
        ("Krenko, Mob Boss", "krenko-mob-boss"),
        ("  Muldrotha, the Gravetide  ", "muldrotha-the-gravetide"),
        ("Éowyn, Fearless Knight", "eowyn-fearless-knight"),
        ("Minsc & Boo, Timeless Heroes", "minsc-boo-timeless-heroes"),
        ("Mr. Orfeo, the Boulder", "mr-orfeo-the-boulder"),
        ("K-9, Mark I", "k-9-mark-i"),
        (
            "Tamiyo, Inquisitive Student // Tamiyo, Seasoned Scholar",
            "tamiyo-inquisitive-student",
        ),
        ("   ", ""),
    ],
)
def test_slugify(name: str, slug: str) -> None:
    assert service._slugify(name) == slug


def test_stats_are_mapped(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        return FakeResponse(
            json_data={
                "container": {
                    "json_dict": {
                        "card": {"rank": 4, "num_decks": 46056, "salt": 1.77},
                    }
                }
            }
        )

    monkeypatch.setattr(http_client, "get", fake_get)

    stats = service.get_edhrec_stats("Atraxa, Praetors' Voice")

    assert stats == {"rank": 4, "commander_deck_count": 46056, "salt": 1.77}
    assert captured["url"].endswith("/commanders/atraxa-praetors-voice.json")


def test_unknown_commander_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        http_client,
        "get",
        lambda *args, **kwargs: FakeResponse(status_code=404),
    )

    assert service.get_edhrec_stats("Not A Commander") is None


def test_empty_name_returns_none_without_request(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(*args: Any, **kwargs: Any) -> FakeResponse:
        raise AssertionError("should not make a request")

    monkeypatch.setattr(http_client, "get", fake_get)

    assert service.get_edhrec_stats("   ") is None


def test_payload_without_card_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        http_client,
        "get",
        lambda *args, **kwargs: FakeResponse(json_data={"container": {}}),
    )

    assert service.get_edhrec_stats("Sol Ring") is None


def test_network_errors_are_logged_and_return_none(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def fake_get(*args: Any, **kwargs: Any) -> FakeResponse:
        raise OSError("network down")

    monkeypatch.setattr(http_client, "get", fake_get)

    assert service.get_edhrec_stats("Sol Ring") is None
    assert "Failed to fetch EDHRec data" in caplog.text

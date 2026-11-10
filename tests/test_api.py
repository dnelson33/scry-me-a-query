from __future__ import annotations

from typing import Any

import pytest

import http_client
from scryfall.api import cards
from scryfall.exceptions import ScryfallAPIError
from tests.helpers import FakeResponse


def test_search_404_returns_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    response = FakeResponse(
        status_code=404,
        json_data={"object": "error"},
        url="https://api.scryfall.com/cards/search?q=nothing",
    )
    monkeypatch.setattr(http_client, "get", lambda *args, **kwargs: response)

    result = cards.card_search_request({"q": "nothing"})

    assert result["total_cards"] == 0
    assert result["data"] == []
    assert result["url"].startswith("https://scryfall.com/search")


def test_search_rewrites_api_url(monkeypatch: pytest.MonkeyPatch, card_factory: Any) -> None:
    response = FakeResponse(
        json_data={
            "object": "list",
            "total_cards": 1,
            "has_more": False,
            "data": [card_factory()],
        },
        url="https://api.scryfall.com/cards/search?q=t%3Aelf&order=edhrec",
    )
    monkeypatch.setattr(http_client, "get", lambda *args, **kwargs: response)

    result = cards.card_search_request({"q": "t:elf", "order": "edhrec"})

    assert result["url"] == "https://scryfall.com/search?q=t%3Aelf&order=edhrec"
    assert result["total_cards"] == 1


def test_search_raises_on_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    response = FakeResponse(status_code=500, json_data={"object": "error"})
    monkeypatch.setattr(http_client, "get", lambda *args, **kwargs: response)

    with pytest.raises(ScryfallAPIError) as exc_info:
        cards.card_search_request({"q": "t:elf"})

    assert exc_info.value.status_code == 500


def test_random_404_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    response = FakeResponse(status_code=404, json_data={"object": "error"})
    monkeypatch.setattr(http_client, "get", lambda *args, **kwargs: response)

    assert cards.random_card_request({"q": "nothing"}) is None


def test_rulings_404_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    response = FakeResponse(status_code=404, json_data={"object": "error"})
    monkeypatch.setattr(http_client, "get", lambda *args, **kwargs: response)

    assert cards.card_rulings_request("https://api.scryfall.com/cards/x/rulings") is None


def test_request_omits_empty_parameters(monkeypatch: pytest.MonkeyPatch, card_factory: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured.update(kwargs)
        return FakeResponse(
            json_data={"total_cards": 0, "has_more": False, "data": []},
            url=url,
        )

    monkeypatch.setattr(http_client, "get", fake_get)
    cards.card_search_request({"q": "t:elf", "page": None, "unique": None})

    assert captured["params"] == {"q": "t:elf"}

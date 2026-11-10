from __future__ import annotations

import logging
from io import BytesIO

import pytest
from PIL import Image

import http_client
import image_utils.cards as cards
from image_utils import generate_grid, get_card_image
from tests.helpers import CARD_IMAGE_URI, FakeResponse


def png_bytes(color: tuple[int, int, int] = (180, 40, 40)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (488, 680), color).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def _clear_image_cache() -> None:
    cards._download_image.cache_clear()


@pytest.mark.parametrize(
    ("count", "size"),
    [
        (1, (223, 310)),
        (2, (446, 310)),
        (3, (669, 310)),
        (9, (669, 930)),
        (10, (892, 930)),
        (16, (892, 1240)),
    ],
)
def test_grid_sizes(count: int, size: tuple[int, int], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "_download_image", lambda url: png_bytes())

    result = generate_grid([CARD_IMAGE_URI] * count)

    with Image.open(result) as image:
        assert image.size == size
        assert image.format == "JPEG"


def test_grid_truncates_to_sixteen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "_download_image", lambda url: png_bytes())

    result = generate_grid([CARD_IMAGE_URI] * 17)

    with Image.open(result) as image:
        assert image.size == (892, 1240)


def test_grid_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="No card images"):
        generate_grid([])


def test_labels_must_match_image_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "_download_image", lambda url: png_bytes())

    with pytest.raises(ValueError, match="labels"):
        generate_grid([CARD_IMAGE_URI], ["Sol Ring", "Black Lotus"])


def test_one_bad_image_does_not_fail_the_grid(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def fake_download(url: str) -> bytes:
        if "bad" in url:
            raise RuntimeError("boom")
        return png_bytes()

    monkeypatch.setattr(cards, "_download_image", fake_download)

    with caplog.at_level(logging.WARNING, logger="image_utils.cards"):
        result = generate_grid(
            [CARD_IMAGE_URI, "https://example.com/bad.jpg", CARD_IMAGE_URI],
            ["Sol Ring", "Broken Card", "Arcane Signet"],
        )

    with Image.open(result) as image:
        assert image.size == (669, 310)

    assert "Broken Card" in caplog.text
    assert "Failed to load card image" in caplog.text


def test_missing_url_gets_placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cards, "_download_image", lambda url: png_bytes())

    result = generate_grid([CARD_IMAGE_URI, ""], ["Sol Ring", "No Art"])

    with Image.open(result) as image:
        assert image.size == (446, 310)


def test_downloads_are_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        calls.append(url)
        return FakeResponse(content=png_bytes())

    monkeypatch.setattr(http_client, "get", fake_get)

    get_card_image(CARD_IMAGE_URI)
    get_card_image(CARD_IMAGE_URI)

    assert calls == [CARD_IMAGE_URI]

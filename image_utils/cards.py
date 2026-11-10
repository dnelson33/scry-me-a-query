"""Build the card image grids posted by the bot.

Images are downloaded in parallel, resized to a uniform tile size, and combined
into a single JPEG per batch. A failed or missing image becomes a visible
placeholder tile instead of failing the whole response.
"""

from __future__ import annotations

import logging
import math
import textwrap
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

import http_client

DEFAULT_IMAGE_SIZE = (223, 310)
MAX_GRID_IMAGES = 16
MAX_PARALLEL_DOWNLOADS = 8
IMAGE_CACHE_SIZE = 128
REQUEST_TIMEOUT: tuple[float, float] = (5.0, 20.0)

PLACEHOLDER_BACKGROUND = (40, 42, 48)
PLACEHOLDER_FOREGROUND = (205, 208, 215)
GRID_JPEG_QUALITY = 88

logger = logging.getLogger(__name__)


def generate_grid(
    card_images: Sequence[str],
    labels: Sequence[str] | None = None,
) -> BytesIO:
    """Combine up to 16 card image URLs into a single grid image.

    ``labels`` is optional; when provided (and the same length as
    ``card_images``) it is used in placeholder tiles and error logs.
    """

    urls = list(card_images)
    names = list(labels) if labels is not None else []
    if names and len(names) != len(urls):
        raise ValueError("labels must be the same length as card_images")

    if len(urls) > MAX_GRID_IMAGES:
        logger.warning(
            "Received %d images; only the first %d will be used",
            len(urls),
            MAX_GRID_IMAGES,
        )
        urls = urls[:MAX_GRID_IMAGES]
        names = names[:MAX_GRID_IMAGES]

    if not urls:
        raise ValueError("No card images provided")

    grid_width, grid_height = _calculate_grid_size(len(urls))

    with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL_DOWNLOADS, len(urls))) as executor:
        tiles = list(
            executor.map(
                _load_card_image,
                urls,
                names or [None] * len(urls),
            )
        )

    tile_width, tile_height = DEFAULT_IMAGE_SIZE
    grid_image = Image.new("RGB", (grid_width * tile_width, grid_height * tile_height))
    for index, tile in enumerate(tiles):
        x = (index % grid_width) * tile_width
        y = (index // grid_width) * tile_height
        grid_image.paste(tile, (x, y))

    grid_bytes = BytesIO()
    grid_image.save(
        grid_bytes,
        format="JPEG",
        quality=GRID_JPEG_QUALITY,
        optimize=True,
    )
    grid_bytes.seek(0)
    return grid_bytes


def _load_card_image(url: str, label: str | None = None) -> Image.Image:
    if not url:
        logger.warning("Card image URL missing%s", f" for {label}" if label else "")
        return _placeholder_tile(label)

    try:
        with Image.open(get_card_image(url)) as image:
            return image.convert("RGB").resize(DEFAULT_IMAGE_SIZE, Image.Resampling.LANCZOS)
    except Exception:
        logger.warning(
            "Failed to load card image%s from %s",
            f" for {label}" if label else "",
            url,
            exc_info=True,
        )
        return _placeholder_tile(label)


def _placeholder_tile(label: str | None) -> Image.Image:
    tile = Image.new("RGB", DEFAULT_IMAGE_SIZE, PLACEHOLDER_BACKGROUND)
    draw = ImageDraw.Draw(tile)

    text = (label or "Image unavailable").strip() or "Image unavailable"
    lines = textwrap.wrap(text, width=20)[:4]
    lines.append("")
    lines.append("Image unavailable")

    try:
        font = ImageFont.load_default(size=16)
        footer_font = ImageFont.load_default(size=12)
    except TypeError:  # pragma: no cover - Pillow < 10.1
        font = ImageFont.load_default()
        footer_font = font

    y = 16
    for line in lines[:-2]:
        draw.text((12, y), line, fill=PLACEHOLDER_FOREGROUND, font=font)
        y += 20
    draw.text(
        (12, DEFAULT_IMAGE_SIZE[1] - 28),
        lines[-1],
        fill=PLACEHOLDER_FOREGROUND,
        font=footer_font,
    )
    draw.rectangle(
        (0, 0, DEFAULT_IMAGE_SIZE[0] - 1, DEFAULT_IMAGE_SIZE[1] - 1),
        outline=(90, 94, 102),
    )
    return tile


@lru_cache(maxsize=IMAGE_CACHE_SIZE)
def _download_image(url: str) -> bytes:
    response = http_client.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.content


def get_card_image(url: str) -> BytesIO:
    return BytesIO(_download_image(url))


def _calculate_grid_size(image_count: int) -> tuple[int, int]:
    if image_count < 1:
        raise ValueError("image_count must be positive")
    if image_count < 3:
        grid_width = image_count  # 1x1 or 1x2
    elif image_count < 10:
        grid_width = 3  # 3x3
    else:
        grid_width = 4  # 4x4

    grid_height = math.ceil(image_count / grid_width)
    return grid_width, grid_height

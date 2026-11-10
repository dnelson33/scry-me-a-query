from __future__ import annotations

import pytest

from scryfall.service.service import _prepare_query


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("t:elf", ("t:elf f:edh", "edhrec")),
        ("t:elf f:standard", ("t:elf f:standard", "edhrec")),
        ("t:elf legal:modern", ("t:elf legal:modern", "edhrec")),
        ("t:elf format:commander", ("t:elf format:commander", "edhrec")),
        ("t:elf f:any", ("t:elf f:any", "edhrec")),
        ("t:elf order:cmc", ("t:elf f:edh", "cmc")),
        ("order:cmc t:elf", ("t:elf f:edh", "cmc")),
        ("t:elf order:cmc f:standard", ("t:elf f:standard", "cmc")),
        ("t:elf ORDER:CMC", ("t:elf f:edh", "cmc")),
        ("order:bogus t:elf", ("t:elf f:edh", "edhrec")),
        ("Black Lotus f:any", ("Black Lotus f:any", "edhrec")),
        ("   t:elf    c:green   ", ("t:elf c:green f:edh", "edhrec")),
        ("", ("f:edh", "edhrec")),
    ],
)
def test_prepare_query(raw: str, expected: tuple[str, str]) -> None:
    assert _prepare_query(raw) == expected


def test_prepare_query_does_not_treat_word_prefix_as_format() -> None:
    # "foo:bar" should not suppress the default format filter.
    assert _prepare_query("foo:bar") == ("foo:bar f:edh", "edhrec")

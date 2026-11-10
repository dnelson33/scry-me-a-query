from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from tests.helpers import make_card


@pytest.fixture
def card_factory() -> Callable[..., dict[str, Any]]:
    return make_card

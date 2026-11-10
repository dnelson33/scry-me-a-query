"""Shared HTTP plumbing for outbound requests.

Every outbound call in the bot goes through this module so that timeouts,
retries, and connection reuse behave the same way everywhere. ``requests`` is
used instead of a fully async client because all call sites run inside worker
threads (``asyncio.to_thread``) for Discord commands, while the image grid also
downloads in parallel.

A thread-local ``Session`` is used because ``requests.Session`` is not
documented as thread-safe; each worker thread gets its own connection pool.
"""

from __future__ import annotations

import threading
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "ScryQueryBot/2.0 (+https://github.com/scry-me-a-query)"
DEFAULT_TIMEOUT: tuple[float, float] = (5.0, 20.0)
MAX_RETRIES = 3
BACKOFF_MAX_SECONDS = 10.0

_local = threading.local()


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    retry = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        status=MAX_RETRIES,
        backoff_factor=0.5,
        backoff_max=BACKOFF_MAX_SECONDS,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        # Let callers inspect the final response and raise our own error type.
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=16)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_session() -> requests.Session:
    """Return the session belonging to the current thread."""

    session = getattr(_local, "session", None)
    if session is None:
        session = _build_session()
        _local.session = session
    return session


def get(url: str, **kwargs: Any) -> requests.Response:
    """Perform a GET request with the default timeout applied."""

    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    return get_session().get(url, **kwargs)

# Scry Me a Query — Improvement Backlog

Last updated: **2026-10-31**

This document tracks what has been fixed and what is intentionally deferred. It
is not a to-do list for basic production readiness: the bot now has tests, CI,
pinned dependencies, hardened Docker packaging, and structured logging.

## Completed

### Correctness and reliability

- **Blocking the event loop.** All Scryfall/EDHRec/image work runs through
  `asyncio.to_thread` in `bot/scryquery_bot.py`.
- **One bad card no longer kills a response.** Failed or missing images become
  labelled placeholder tiles; `generate_grid` logs the card name and URL and
  keeps the rest of the batch.
- **`None`-assumption crashes.** `NoCardsFound` and `ScryfallAPIError` are
  explicit exceptions. Rulings handle 404s, face fields use `.get()`, and
  `_map_card` falls back to top-level images for layouts such as `prepare`.
- **Reply parsing.** `get_reply_query` and `get_reply_card_name` have a depth
  cap, length cap, case-insensitive prefix matching, non-greedy link parsing,
  bot-author validation, and embed-title support. Deleted references are
  handled.
- **`?clash`.** Returns immediately above 16 players, deduplicates by user ID,
  preserves mention order, formats fractional mana values with `%g`, and
  announces all tied winners.
- **Command errors.** Missing/bad arguments and cooldowns get friendly messages;
  unexpected errors are logged with a traceback and do not claim to be Scryfall
  failures.
- **`allowed_mentions`.** Card and text responses suppress all mentions;
  ThoughtClash allows user mentions only.

### Performance

- **Image pipeline.** Uses Scryfall `normal` images (≈488×680 JPG) instead of
  PNG, downloads in parallel (max 8), caches 128 URLs in-process, and emits JPEG
  grids at quality 88.
- **Single-card responses.** The embed points at the Scryfall image URL; no
  download, resize, or re-upload.
- **Query handling.** `order:` and explicit format filters are parsed before
  encoding; `f:edh` is only appended when no filter exists; requests use
  `params` rather than manual string concatenation.

Measured on the development machine (network-dependent):

| Path | Before | After |
| --- | --- | --- |
| 16-image grid | ≈9.6 s | ≈0.47 s |
| Repeat grid, cached | — | ≈0.08 s |
| 32-card `?sq` | ≈19 s | ≈1.03 s |
| Single-card response | download + resize + upload | no upload |

### Platform and operations

- **HTTP layer.** Thread-local `requests.Session` with connection pooling,
  `(5, 20)` timeouts, retries for `429`/`5xx`, exponential backoff, and
  `Retry-After`.
- **EDHRec.** Replaced unmaintained `pyedhrec` with a direct request to
  `https://json.edhrec.com/pages/commanders/<slug>.json`.
- **Configuration.** `DISCORD_TOKEN`, `COMMAND_PREFIX`, `EMOJI_GUILD_ID`,
  `LOG_LEVEL`, and `LOG_FILE` are environment-backed; the hardcoded guild ID is
  gone and emoji lookup has text fallbacks.
- **Logging.** Root logger writes to stdout and an optional rotating file
  (5 MB, 3 backups). Discord.py deliberately owns no handler, so logs are not
  duplicated or truncated on restart.
- **Packaging.** `pyproject.toml`, Python 3.13 toolchain file, pinned
  `requirements.txt`, `ruff`, `mypy`, and `pytest`.
- **CI.** `.github/workflows/ci.yml` runs lint, format check, type check, tests
  on Python 3.12/3.13, and a Docker build.
- **Docker.** Multi-stage build, non-root user, read-only root filesystem,
  tmpfs `/tmp`, `.dockerignore` excluding secrets and caches, pinned base image
  tag, and graceful `SIGINT` shutdown.
- **Tests.** 105 tests cover query rewriting, card mapping, API error handling,
  image grids and placeholders, response formatting, reply chains, EDHRec,
  settings, command registration, and error handling. No token or live network
  is required.

## Deferred

### P1 — pagination

`_get_pages` is now correct, and `card_search` accepts `page`, but no command
exposes paging. A large search only shows the first 32 cards. Options: a
`page:N` modifier, Prev/Next buttons, or a “more results” link. Decide whether
“page” means Scryfall’s 175-card pages or 32-image response batches.

### P1 — accessible multi-card responses

Multi-card responses are image-only. Add card names/links in the message or
embed fields, truncated to Discord’s 2000-character limit, as a fallback for
screen readers and clients that cannot load images.

### P2 — `?asktheoracle` hit rate

With no query the command picks a random card, and most cards have no rulings.
Retry a bounded number of times or bias toward cards known to have rulings.
Verify whether Scryfall supports a `has:ruling` filter before relying on it.

### P2 — image polish and cache policy

Tiles are resized to an exact 223×310, which can distort art with a different
aspect ratio. Consider `ImageOps.fit` (crop) or `ImageOps.contain` with padding.
The cache is process-local; a disk cache would help across restarts if
measurements justify it.

### P3 — observability

Command logs include name, user, guild, and failures, but not query text,
duration, or card count. If hosted monitoring is added, emit timing metrics and
consider a `/health` sidecar or heartbeat log.

## Verification

```bash
# Full local gate
ruff check . && ruff format --check . && mypy . && pytest

# Query rewriting (no network)
.venv/bin/python -c "from scryfall.service.service import _prepare_query; print(_prepare_query('t:elf order:cmc f:standard'))"

# Live search; should not force f:edh
.venv/bin/python -c "from scryfall.service.service import card_search; print(card_search('t:elf f:standard')['scryfall_url'])"

# Single-card response has no files and uses the image URL
.venv/bin/python -c "from scryfall.service.service import card_search; from bot.utils import format_response; r=format_response(card_search('Sol Ring f:any')['cards'][:1]); print(len(r['files']), r['embed'].image.url)"

# Docker smoke test
docker compose config
docker build -t scry-me-a-query:local .
docker run --rm --entrypoint sh scry-me-a-query:local -c 'ls -a /app'
```

## Known risks

- Rotate the Discord token if a local `.env`/`.env.dev` was ever shared or
  committed. The files are gitignored and excluded from Docker, but rotation is
  still the safe move after any exposure.
- Scryfall asks clients to be conservative. The retry policy and per-grid
  download cap are polite, but there is no global rate limiter across
  concurrent commands.
- The image cache can add roughly 13–20 MB of RSS at 128 `normal` images. The
  bot measured ≈48 MB idle and ≈100 MB peak on the development machine.

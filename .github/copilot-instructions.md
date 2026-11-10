# Copilot / AI Agent Instructions for Scry Me a Query

A small Discord bot that queries Scryfall and EDHRec, builds image grids, and
posts results to Discord. This file is for coding agents working in the repo.

## Run and test

- Primary runner: `main.py` loads `.env`, validates `DISCORD_TOKEN`, configures
  logging, then runs the bot.
- Local setup:
  `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
  then `cp env.example .env` and set `DISCORD_TOKEN`.
- Quality gate: `ruff check . && ruff format --check . && mypy . && pytest`.
- Docker: `docker compose up --build -d` (see `Dockerfile`,
  `docker-compose.yml`). Secrets come from the environment; `.env*` is excluded
  from the image.

## Architecture

- `bot/` — Discord layer. Commands in `bot/scryquery_bot.py`, formatting and
  reply-chain helpers in `bot/utils.py`, environment settings in
  `bot/config.py`, emoji lookup in `bot/emojis.py`.
- `scryfall/api/` — raw HTTP wrappers and Scryfall response `TypedDict`s.
- `scryfall/service/` — query rewriting, card mapping, rulings, paging, and
  internal types. Prefer adding logic here.
- `edhrec/` — direct client for `json.edhrec.com`.
- `image_utils/` — parallel image fetching, placeholder tiles, and JPEG grids.
- `http_client.py` — thread-local `requests.Session`, retries, and timeouts.
- `assets/` — static images used by `?asktheoracle`.

## Conventions

- Commands use `discord.ext.commands`; the default prefix is `?` and comes from
  `COMMAND_PREFIX`. Commands are case-insensitive.
- Blocking work (HTTP, Pillow) must run through `asyncio.to_thread` in command
  handlers. Never call service functions directly on the event loop.
- All outbound HTTP should go through `http_client.get` so retries, timeouts,
  and the user agent stay consistent.
- Service functions are synchronous and typed; commands are async. Keep that
  split.
- Response shapes are `TypedDict`s in `bot/types.py`, `scryfall/api/types.py`,
  and `scryfall/service/types.py`. Use `.get()` for optional Scryfall fields.
- One bad image must never fail a grid: return a labelled placeholder from
  `_load_card_image` instead of raising.
- Card/text responses must pass `allowed_mentions=NO_MENTIONS`; ThoughtClash
  permits user mentions only.
- Secrets are environment-only. Do not hardcode tokens or guild IDs; use
  `bot/config.py` settings.
- Manage dependencies in `pyproject.toml`, then update the pinned
  `requirements.txt`. `pyedhrec` was deliberately removed.

## Adding things

- **New command:** add it to `bot/scryquery_bot.py`, reuse
  `bot.utils.format_response`, and send through `_send_card_response` for card
  results.
- **New Scryfall logic:** add request/response shapes in `scryfall/api/types.py`,
  raw calls in `scryfall/api/cards.py`, and mapping/business logic in
  `scryfall/service/service.py`.
- **New tests:** put them in `tests/` and use `tests/helpers.py`
  (`FakeResponse`, `make_card`). Mock `http_client.get`; never require a token
  or live network.

## Common problems

- Logs: stdout by default; set `LOG_FILE` for a rotating file. Do not add a
  second handler to discord.py; `main.py` owns logging.
- Emoji fallbacks: custom emojis require the bot to be in `EMOJI_GUILD_ID`;
  otherwise mana symbols render as text.
- Image failures: reproduce with `generate_grid()` and inspect the placeholder
  and warning log containing the card name and URL.
- Large result sets: only the first 32 cards are shown; pagination is a known
  deferred improvement (see `IMPROVEMENTS.md`).

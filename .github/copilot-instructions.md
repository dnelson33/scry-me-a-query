# Copilot / AI Agent Instructions for Scry Me a Query

This repo is a small Discord bot that queries Scryfall and EDHRec, builds image grids, and posts results to Discord. Below are focused, actionable notes to make an AI coding agent immediately productive.

1. Project entry points and run commands
- Primary runner: `main.py` — loads `.env` and runs the bot using `DISCORD_TOKEN`.
- Local dev (venv): `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python main.py`
- Docker: build/run with `docker-compose up --build` (see `Dockerfile` and `docker-compose.yml`).

2. High-level architecture (why and how)
- `bot/` — Discord command handlers and small helpers. Main commands live in `bot/scryquery_bot.py` and common helpers in `bot/utils.py`.
- `scryfall/` — two-layer Scryfall integration: `scryfall/api/` contains raw HTTP request wrappers, `scryfall/service/` contains mapping and business logic (e.g., `_map_card`, paging logic).
- `edhrec/` — thin wrapper around `pyedhrec` in `edhrec/service.py` returning a small typed dict.
- `image_utils/` — image fetching and grid generation (`image_utils/cards.py`) returning a BytesIO suitable for Discord uploads.
- `assets/` — static images (used by `asktheoracle`).

3. Important conventions and patterns (project-specific)
- Commands use `?` prefix and are defined with `discord.ext.commands` in `bot/scryquery_bot.py`.
- Service vs API split: prefer adding new logic to `scryfall/service/` and raw HTTP changes to `scryfall/api/`.
- Typed dicts are used heavily (see `scryfall/api/types.py` and `bot/types.py`) — return values should conform to these shapes.
- Image files for Discord are created as `discord.File(BytesIO(...), filename=...)` (see `bot/utils.format_response`).
- Emojis: guild emojis are fetched on startup in `bot/scryquery_bot.on_ready()` and assigned to `bot/emojis.EMOJIS`. The `GUILD_ID` is hard-coded there — update when running in a different guild.
- Sync network calls in async context: most service functions (e.g., `scryfall.service.card_search`) are synchronous and called inside async handlers. Be conservative when changing to avoid blocking the event loop; convert to async only if you also adjust call sites.

4. Integration and external deps
- Scryfall: `scryfall/api/cards.py` calls `https://api.scryfall.com` with `requests`.
- EDHRec: uses `pyedhrec` in `edhrec/service.py`.
- Discord bot: `discord.py` (see `requirements.txt`).

5. Debugging and common developer tasks
- To see bot logs: main uses a `FileHandler` at `discord.log` (configured in `main.py`).
- To test a command locally: start the bot with a valid `DISCORD_TOKEN` in `.env` and invoke commands in a test server.
- If image grid generation fails, reproduce by calling `image_utils.generate_grid()` with card `image_uri` values; network image fetching happens via `requests`.

6. Where to implement changes (quick pointers)
- New command: add to `bot/scryquery_bot.py` and reuse `bot/utils.format_response`.
- New Scryfall logic: add request shapes to `scryfall/api/types.py`, raw calls to `scryfall/api/cards.py`, and mapping/logic to `scryfall/service/service.py`.
- Long-running or blocking work: consider delegating to threads or converting to async `aiohttp` and `discord.py`-compatible async callers.

7. Safety and config
- Secrets: `DISCORD_TOKEN` must be provided via environment (see `.env`/`docker-compose.yml`). Do not hardcode tokens.
- Guild-specific IDs: `GUILD_ID` in `bot/scryquery_bot.py` is environment-specific — update before deployment.

8. Examples and quick references
- Format single-card response: `bot/utils.format_response(cards, site_url)` uses `discord.Embed` and attaches images from `image_utils.generate_grid()`.
- Add a unique search type: use `scryfall.api.ScryfallUnique` via the `card_search(..., unique=...)` parameter (see `cards` command in `bot/scryquery_bot.py`).

If any section is unclear or you'd like examples expanded (e.g., converting a synchronous service call to an async implementation), tell me which area and I will update the file accordingly.

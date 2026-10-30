# Scry Me a Query — Improvement Backlog

Last updated: **2026-10-30**

This document captures the remaining issues and opportunities identified during the October 2026 code review. It is written so that each item can be picked up cold: what is wrong, where it lives, how to reproduce it, and what “done” looks like.

> The first round of fixes (event-loop blocking, image pipeline, and query parsing) was implemented in the working tree around 2026-10-29/30. Confirm `git log` / `git status` before relying on the “Already addressed” section below.

---

## Already addressed

Do not redo these unless a regression appears.

- **Blocking the event loop.** All synchronous Scryfall/EDHRec/image work now runs through `asyncio.to_thread` in `bot/scryquery_bot.py` (`?sq`, `?sqrandom`, `?flavortown`, `?edhrec`, `?asktheoracle`, `?clash`, `?cards`/`?prints`/`?art`/`?arts`).
- **Image pipeline cost.** `scryfall/service/service.py` now uses Scryfall’s `normal` image variant (≈488×680 JPG) instead of `png` (≈745×1040, ~0.9 MB each). `image_utils/cards.py` downloads in parallel (max 8), caches 128 URLs in-process, uses timeouts, and calls `raise_for_status()`.
- **Single-card images.** `bot/utils.py:format_response` no longer builds a grid for a one-card result; the embed points at the Scryfall image URL. `?asktheoracle` does the same. `?cards`/`?prints` now forward single-card embeds, which were previously dropped.
- **Query parsing.** `scryfall/service/service.py:_prepare_query` parses `order:` and `f:`/`format:`/`legal:` filters from the raw query before encoding. `f:edh` is only appended when no explicit filter exists. `scryfall/api/cards.py` now uses `requests` `params` instead of manual string concatenation, and all requests have `(5, 20)` timeouts.
- **Grid sizing.** `generate_grid` now recalculates the grid after truncating to 16 images.

Measured on the development machine (network-dependent):

| Path | Before | After |
| --- | --- | --- |
| 16-image grid | ≈9.6 s (4.5 s download + 5.1 s render) | ≈0.47 s |
| Repeat grid, cached | — | ≈0.08 s |
| 32-card `?sq` | ≈19 s | ≈1.03 s |
| Single-card response | download + resize + upload | no upload |

Known deliberate choices:

- `f:any` is kept in the query and suppresses the default `f:edh` (verified against Scryfall).
- `normal` is a compromise between quality and bandwidth; `large` may be preferable for single-card embeds later.
- The image cache is process-local and does not survive restarts; 128 `normal` images is roughly 13–20 MB depending on the art.

---

## P1 — next up

### P1-1. One bad card should never kill a whole response

**Problem.** A single missing/failed image still fails the entire multi-card response. After `scryfall/service/service.py:_map_card`, a card can still have `image_uri == ""` (unknown layout, missing art, Scryfall anomaly). `image_utils/cards.py:_load_card_image` raises `ValueError`, `generate_grid` propagates it, `bot/utils.py:format_response` does not filter or catch, and `?sq` replaces everything with `"An error occurred while querying Scryfall."`

**Reproduce.** Call `format_response` with a card whose `image_uri` is `""` alongside valid cards. The whole call raises. The prior `?sq Emeritus of Woe` bug was one instance of this class.

**Proposed.**

- In `format_response`, decide per card: render a placeholder tile (card name on a neutral background) or drop the card from the grid and note it in the message.
- In `_load_card_image`, catch per-URL failures, log the URL/card, and return the placeholder instead of re-raising.
- Keep `generate_grid`’s empty-input guard, but make it impossible for one URL to abort the batch.
- Keep the top-level `?sq` catch as a last resort, but make it log the real exception and avoid blaming Scryfall for image/upload failures.

**Acceptance.**

- A 32-card response with one bad URI still posts the remaining 31 cards.
- The failure is visible in logs with the card name and URL.
- A test covers mixed valid/invalid URIs.

---

### P1-2. Fix reply parsing for `?prints` / `?cards` / `?art`

**Problem.** `bot/utils.py:get_reply_card_name` only looks for Markdown links in `message.content`, then walks references without checking `message.reference is None`.

- Replying `?prints` to a **multi-card** `?sq` result raises `AttributeError: 'NoneType' object has no attribute 'message_id'` (verified with a mocked reply chain). Multi-card responses contain a bare Scryfall URL (`bot/utils.py:format_response`), not `[name](<url>)`.
- Replying to a **single-card** result silently returns `None` because the message content is empty (the link is in the embed), so `?prints` falls back to rerunning the original query rather than using the card’s exact name.
- The regex `\[(.*)\]\(<.*scryfall.com.*>\)` is greedy and can capture the wrong name when a message contains several links (e.g. `?clash`).

**Proposed.**

- Add a depth cap (e.g. 10) and stop when `message.reference is None`.
- Return `None` immediately if the replied message is not from the bot.
- Accept a card name from either content **or** a single-card embed (`embed.url`, `embed.title`).
- Use a non-greedy/explicit regex: `\[([^\]]+)\]\(<[^>]*scryfall\.com[^>]*>\)`.
- Add an explicit `?prints <name>` / `?cards <name>` / `?art <name>` argument so the command does not depend on reply parsing.
- Consider exact-name search (`!"<name>"`) to avoid fuzzy matches such as `Black Lotus` also returning `Blacker Lotus`; verify multi-face names (`//`) before switching.

**Acceptance.**

- Reply chains covered by tests: user command → single-card bot reply; user command → multi-card bot reply; non-bot replied message; broken/deleted reference.
- `?prints` works both as a reply and with an explicit name.
- No `AttributeError` escapes the helper.

---

### P1-3. Keep secrets and build junk out of the Docker image

**Problem.** There is no `.dockerignore`, and `Dockerfile` uses `COPY . .`. A local build bakes `.env` (the Discord token), `.venv`, `.git`, and `discord.log` into the image. `docker-compose.yml` also bind-mounts `./:/app`, which masks the image contents and makes production behaviour differ from the build.

**Proposed.**

- Add `.dockerignore` at minimum:

  ```gitignore
  .env*
  .venv/
  .git/
  *.log
  __pycache__/
  *.py[cod]
  .pytest_cache/
  .ruff_cache/
  .mypy_cache/
  .vscode/
  ```

- Run the container as a non-root user.
- Do not bind-mount the source tree in production; use a separate `compose.dev.yml` or an env-selected override.
- Pass `DISCORD_TOKEN` only via the environment/secret, never via a copied `.env`.
- Verify with `docker build` then `docker run --rm <image> sh -c 'ls -a /app'`.

**Acceptance.** The built image contains no `.env*`, `.git`, `.venv`, or log files; the container starts with an env-provided token.

---

### P1-4. `?clash`: enforce the 16-player limit and handle ties

**Problem.** `bot/scryquery_bot.py:clash` only returns when there is exactly one contestant. With more than 16 it sends “You have too many friends. Pick your 16 closest” and then continues to draw cards for everyone. `generate_grid` truncates to 16 images, so the image and the listed contestants disagree. Additional issues:

- Contestants are a `set`, so draw order is nondeterministic.
- Ties pick the first entry arbitrarily and still announce one winner.
- `mv!={int(cmc)}` truncates fractional CMCs, so duplicate mana values can slip through.

**Proposed.**

- Return after sending the “too many” message (or cap before drawing).
- Deduplicate by user ID, preserve mention/insertion order, and cap at 16.
- Handle ties explicitly (announce all tied players, or reroll between them).
- Compare/format CMCs without lossy `int()` where fractional values are possible.
- `?clash` currently sends the initial and result messages without `reference`; decide whether that is intentional.

**Acceptance.** 17 contestants produce one explanatory message and no draw; ties are deterministic and explained; 2–16 contestants still work.

---

### P1-5. Remove the remaining `None`-assumption crashes

**Problem.** Several paths assume Scryfall always returns non-`None` data:

- `scryfall/api/cards.py:random_card_request` returns `None` on 404, but `service.random_card` passes it straight to `_map_card(None)` (`TypeError`).
- `card_rulings_request` returns `None` on 404 while typed as non-optional; `service.get_rulings` then calls `.get` on it.
- `service._map_card` directly indexes `front['oracle_text']` and `front['mana_cost']`; those face fields are optional in Scryfall’s schema.
- Multi-face flavor text lives on the faces, not the top level (e.g. `Delver of Secrets`), so `_map_card` returns `flavor_text=None` and `?flavortown` can post “None”.
- `bot/utils.py:get_formatted_card_info` assumes `oracle_text` / `mana_cost` are strings; most missing values are `""` today, but this is not guaranteed.
- `?edhrec` assumes `rank`, `num_decks`, and `salt` are present; `f"{commander_decks:,}"` raises on `None`.
- `?momir` uses `raise "..."` (a `TypeError` swallowed by a bare `except`), and `?gamble` also uses a bare `except` plus an `input` variable that shadows the builtin.

**Proposed.**

- Define a small `NoCardsFound`/`ScryfallNotFound` exception (or return `Optional` consistently) and handle it in commands with a friendly message.
- Make `get_rulings` return `{card, rulings: []}` when the request returns `None`.
- Use `.get()` for face fields and fall back to face flavor text (front, then back).
- Add `Optional`/`NotRequired` to `scryfall/service/types.py`, `scryfall/api/types.py`, and `bot/types.py`; run `mypy` to find the rest.
- Replace bare `except` with specific exceptions; replace `raise "..."` with `raise ValueError(...)`; rename `input` to `value`.
- Guard EDHRec fields before formatting.

**Acceptance.** `?sqrandom` for a query with no matches returns a friendly message instead of a traceback; `?flavortown` on Delver of Secrets shows the back-face flavor (or falls back gracefully); `mypy`/`ruff` no longer flag these paths.

---

### P1-6. Add regression tests and CI

**Problem.** There are no tests and no CI workflow. The October image regression and the `?prints` reply crash both shipped without detection.

**Proposed.** Add `pytest` with mocked HTTP (`responses` or `requests-mock`). Minimum coverage:

- `_prepare_query`: default `f:edh`, explicit `f:standard`, `legal:modern`, `f:any`, `order:` at start/middle/end, invalid order, whitespace normalization.
- `_map_card`: normal card, multi-face card with face images, `prepare` layout with top-level images only, missing images, missing face fields, face-only flavor.
- `format_response`: zero cards, one card (no files, embed URL), multiple cards (batch count), one bad URI (after P1-1).
- `get_reply_card_name` / `get_reply_query`: mocked reply chains, including the cases in P1-2.
- `generate_grid`: 0, 1, 16, 17 images; one failing URL (after P1-1); cache hit.

Add `ruff` and `mypy` (or `pyright`) and a GitHub Actions workflow that runs `ruff check`, `mypy`, and `pytest` on push/PR.

**Acceptance.** CI fails on the old `_map_card` bug and on the `?prints` reply crash; `pytest` does not require a Discord token or live network.

---

## P2 — reliability and product quality

### P2-1. Pagination (and fix `_get_pages`)

`scryfall/service/service.py:_get_pages` computes pages but nothing consumes them. It is also wrong: `total_pages = total_cards // cards_per_page` truncates, and `range(1, total_pages)` never includes the last page (and can omit page 2 entirely when there are 176 results). `card_search` already accepts `page`, but no command exposes it.

Suggested work:

- Fix the math with `math.ceil`, or derive page links from Scryfall’s `next_page` / `has_more` instead of guessing.
- Decide what “page” means for the bot (Scryfall’s 175-card pages vs. the 32 images shown per response).
- Add a `page:N` modifier or Prev/Next buttons that re-run `card_search(..., page=N)`.
- Cache repeated searches if pagination makes them common.

**Acceptance.** A 200-result search can reach results beyond the first 32; `_get_pages` has tests; no dead code remains.

### P2-2. Names and accessibility in multi-card responses

Multi-card responses are images only: no card names, no links, no text fallback for screen readers or users who cannot load images. Add the first N names as links under the header (truncate to Discord’s 2000-character message limit), or use embeds/fields per batch. Consider making the first result the embed image so link previews are useful.

**Acceptance.** Every displayed card has an accessible name/link; long result sets truncate cleanly.

### P2-3. Cooldowns and upstream rate limiting

Image-heavy commands can be spammed, queueing many blocked worker threads and Scryfall/CDN requests. Add per-user (and optionally per-guild) cooldowns to `?sq`, `?sqrandom`, `?clash`, `?cards`/`?prints`/`?art`, and `?edhrec`. Consider a global semaphore around Scryfall/CDN requests (the image grid already limits to 8 parallel downloads per grid, but concurrent commands multiply that).

**Acceptance.** A user cannot trigger more than one expensive query per short window; cooldown errors produce a friendly “try again in Ns” message.

### P2-4. Error handler, usage, and help text

`bot/scryquery_bot.py:on_command_error` currently prints and sends “Well, this is embarassing…” for every `CommandError`, including missing arguments, bad arguments, cooldowns, and permissions. Improvements:

- Handle `MissingRequiredArgument` and `BadArgument` with usage text.
- Handle `CommandOnCooldown` with the retry window.
- Handle `CheckFailure` / `BotMissingPermissions`.
- Unwrap `CommandInvokeError` and log the underlying exception with `logging.exception`.
- Add `help=` / `brief=` metadata and a short usage message for `?sq` with no query.
- Use `ctx.invoke(sqrandom, ...)` in `?mycaptain`, `?sliverme`, and `?momir` so they go through checks/cooldowns consistently.

**Acceptance.** User mistakes no longer look like bot bugs; unexpected errors include a traceback in the log.

### P2-5. Configuration and emoji resilience

`GUILD_ID` is hardcoded in `on_ready`, and `guild.emojis` raises if the bot is not in that guild (leaving `EMOJIS = []`). Move the guild ID and command prefix to environment variables, guard `guild is None`, and build a name→emoji dict once instead of scanning the list for every mana symbol. Also validate `DISCORD_TOKEN` in `main.py` before calling `bot.run`.

**Acceptance.** The bot starts in a guild without the emoji guild; mana symbols fall back to `{W}`-style text; missing token produces a clear error.

### P2-6. HTTP retries, `Retry-After`, and connection reuse

Timeouts were added, but 429/5xx responses still fail immediately. Scryfall asks clients to be polite and to cache. Add a small request helper (or `HTTPAdapter` with `Retry`) that:

- Retries 429/5xx with exponential backoff and a cap.
- Honors `Retry-After`.
- Logs the status and URL.
- Uses a shared `Session` for connection pooling if thread-safety is handled (one session per worker thread, or keep per-call requests).

**Acceptance.** A simulated 429 then 200 succeeds; repeated failures surface a clear log entry.

### P2-7. Logging and observability

The app uses `print`, and `main.py` attaches a `DEBUG` handler to discord.py’s logger with `mode='w'` (truncates every restart). This is why `discord.log` had no traceback for the image bug. Configure the root logger with a rotating file handler and stdout, at `INFO` in production, and log:

- Command name, user/guild, query, card count, duration.
- Failures with `logging.exception` and the card/URL involved.
- Do not log tokens or full message payloads.

**Acceptance.** A forced image failure appears in `discord.log` with a traceback; logs rotate instead of being truncated.

### P2-8. `allowed_mentions`

Card text, flavor text, and user queries are echoed into messages. Set `allowed_mentions=discord.AllowedMentions.none()` on card/text responses so content cannot ping `@everyone`/roles/users. For `?clash`, allow user mentions only.

**Acceptance.** A query/card text containing `@everyone` does not ping.

### P2-9. Reproducible deployment

`requirements.txt` is unpinned, the base image tag is floating, and the compose bind mount shadows the image. Pin dependencies (or add a lockfile such as `uv.lock`/`pip-tools`), pin the base image, add a healthcheck, and decide on a graceful shutdown strategy for `SIGTERM`.

**Acceptance.** Two builds from the same commit install identical dependency versions; `docker compose up` runs the built image, not the host tree.

---

## P3 — polish and cleanup

### P3-1. Image quality and cache policy

`_load_card_image` uses `resize` to an exact 223×310, which distorts art with a different aspect ratio. Use `ImageOps.fit` (crop) or `ImageOps.contain` with padding. Consider JPEG/WebP for grids (the 4×4 PNG is ~2 MB) and a disk cache if restarts cause repeated downloads. Revisit `IMAGE_CACHE_SIZE` once real memory usage is measured.

### P3-2. Improve `?asktheoracle` hit rate

With no query, the command picks a random card; most cards have no rulings, so users often get the orb fallback. Retry a few times (bounded) until a ruling is found, or bias the query toward cards known to have rulings. Verify whether Scryfall supports a `has:rulings`-style filter before relying on it.

### P3-3. Documentation

`README.md` is missing `?momir`, `?cards`, `?prints`, `?art`, and `?arts`. It also does not document:

- The implicit `f:edh` default for `?sq`.
- That `f:any` disables the default format filter.
- That `?cards`/`?prints`/`?art` require a reply (or, after P1-2, an explicit name).
- The `?clash` 16-player limit.
- The `?sq` reply-chain behaviour (replying to a query appends its filters).

Link this backlog from the README when convenient.

### P3-4. Dead code and consistency

- `bot/scryquery_bot.py:sq` sets `global last_sq`, which is never read.
- `pages` is unused until P2-1.
- `bot/utils.py` imports `randint` but does not use it.
- `scryfall/api/types.py` marks many optional Scryfall fields as required; tighten alongside P1-5.
- Nested same-quote f-strings require Python 3.12+; Docker uses 3.13, but document the requirement or add `requires-python`/`pyproject.toml`.
- Normalize `?BOO`/command naming style if desired (case-insensitivity already handles it).

### P3-5. Reply-chain limits and exact-name queries

`get_reply_query` walks the entire reference chain, concatenating every matching command, with no depth or length cap. It is also case-sensitive (`?SQ ...` is ignored). Cap the depth/length, compare case-insensitively, and decide whether concatenating multiple queries is desired or whether only the nearest query should win. Test exact-name syntax for multi-face cards before changing `?prints` (P1-2).

---

## Suggested order

1. **P1-3** (.dockerignore/secret leak) — smallest change, highest security impact.
2. **P1-1** (failure isolation) — removes the class of bug that started this review.
3. **P1-6** (tests/CI) — locks in the recent fixes before more refactoring.
4. **P1-2** (reply parsing) — restores `?prints` functionality.
5. **P1-4** and **P1-5** — remaining user-facing crashes/boundaries.
6. **P2-1**, **P2-2**, **P2-3** — the biggest UX improvements.
7. Everything else as time allows.

## Verification notes

Useful manual checks while working in this area:

```bash
# Query rewriting (no network)
.venv/bin/python -c "from scryfall.service.service import _prepare_query; print(_prepare_query('t:elf order:cmc f:standard'))"

# Live search; should not force f:edh
.venv/bin/python -c "from scryfall.service.service import card_search; print(card_search('t:elf f:standard')['scryfall_url'])"

# Single-card response has no files and uses the image URL
.venv/bin/python -c "from scryfall.service.service import card_search; from bot.utils import format_response; r=format_response(card_search('Sol Ring f:any')['cards'][:1]); print(len(r['files']), r['embed'].image.url)"

# Grid timing / cache
.venv/bin/python -c "import time; from scryfall.service.service import card_search; from image_utils import generate_grid; u=[c['image_uri'] for c in card_search('f:any t:elf')['cards'][:16]]; t=time.perf_counter(); generate_grid(u); print(time.perf_counter()-t)"
```

There is no test suite yet, so these checks are the current safety net. Add them to `pytest` as part of P1-6.

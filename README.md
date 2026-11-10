# Scry Me a Query (Discord Bot)

A Discord bot that adds multi-card Scryfall search, EDHRec stats, and a few
Magic-themed toys to a server.

## Commands

| Command | Aliases | Description |
| --- | --- | --- |
| `?sq <query>` | | Search Scryfall and return up to 32 cards as image grids. |
| `?sqrandom <query>` | | Return one random card matching `<query>`. |
| `?mycaptain` | | Return a random commander. |
| `?sliverme` | `?slivermetimbers` | Return a random Sliver. |
| `?cards <name>` | `?prints` | Show every printing of a card. |
| `?art <name>` | `?arts` | Show every unique illustration of a card. |
| `?edhrec <commander>` | | Rank, deck count, and salt score from EDHRec. |
| `?asktheoracle [query]` | | Show a random ruling for a card. |
| `?flavortown` | `?quoteme` | Post a random card's flavor text. |
| `?clash` | `?thoughtclash` | Draw a card per mentioned user; highest mana value wins. |
| `?momir [0-16]` | | Return a random creature with the given mana value. |
| `?gamble [n]` | `?randnum`, `?random` | Roll from 1 to `n` (default 7). |
| `?arcaneoculus` | `?datapriest`, `?edhtrack` | Link to the Arcane Oculus EDH site. |
| `?boo` | | Go for the Eyes? |

### Behaviour notes

- Commands are case-insensitive.
- `?sq` adds `f:edh` (Commander legality) unless the query already includes
  `f:`, `format:`, or `legal:`. Use `f:any` to search every printing.
- `order:<name|released|color|type|cmc|power|toughness|edhrec>` is understood
  by `?sq`; results default to EDHRec rank order.
- Replying to a `?sq` message with another `?sq` appends the replied query.
- `?cards`, `?prints`, and `?art` accept a card name directly or can be used as
  a reply to a card result.
- `?clash` accepts at most 16 contestants (author included). Ties are announced
  for every tied player.
- Mana symbols use custom emojis when `EMOJI_GUILD_ID` is configured; otherwise
  they fall back to text such as `{W}`.

## Configuration

Copy `env.example` to `.env` and fill in the values:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DISCORD_TOKEN` | yes | — | Bot token from the Discord developer portal. |
| `COMMAND_PREFIX` | no | `?` | Command prefix. |
| `EMOJI_GUILD_ID` | no | — | Guild whose custom emojis are used for mana symbols. |
| `LOG_LEVEL` | no | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `LOG_FILE` | no | — | Also write logs here (5 MB rotation, 3 backups). |

The bot needs the **Message Content** intent enabled in the Discord developer
portal so it can read command arguments and replied messages.

## Local development

Requires Python 3.15 or newer; CI and Docker use 3.15.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install "pytest>=9" "pytest-asyncio>=1.4" "ruff>=0.17" "mypy>=2.4" "types-requests>=2.33"
cp env.example .env   # then set DISCORD_TOKEN
python main.py
```

Quality checks:

```bash
ruff check .
ruff format --check .
mypy .
pytest
```

Tests use mocked HTTP and do not require a Discord token or network access.
CI runs lint, formatting, type checks, tests on Python 3.15, and a Docker
build.

## Docker

```bash
cp env.example .env   # set DISCORD_TOKEN
docker compose up --build -d
docker compose logs -f
```

The runtime image:

- uses a multi-stage build, so build tools and pip caches stay out of the final
  image;
- runs as the unprivileged `app` user with a read-only root filesystem and a
  writable `/tmp` tmpfs;
- receives `.env` only through the environment (it is excluded by
  `.dockerignore`), so no secrets are baked into the image;
- uses `STOPSIGNAL SIGINT` so `docker stop` triggers a graceful gateway close.

## Architecture

```
main.py              config validation, logging, bot startup
bot/
  config.py          environment-backed settings
  scryquery_bot.py   command handlers, error handler, bot instance
  utils.py           response formatting and reply-chain helpers
  emojis.py          guild emoji lookup with text fallbacks
scryfall/
  api/               raw HTTP wrappers and Scryfall response types
  service/           query rewriting, card mapping, rulings
edhrec/              direct json.edhrec.com client
image_utils/         parallel image download, placeholders, JPEG grids
http_client.py       thread-local sessions, retries, timeouts
```

Outbound requests share a thread-local `requests.Session` with urllib3 retries
for `429`/`5xx`, `Retry-After` support, connection pooling, and `(5, 20)`
timeouts. Blocking work is offloaded with `asyncio.to_thread`, so the Discord
event loop is never blocked by Scryfall or image processing.

## Operations

- Logs go to stdout by default, which works with `docker logs` and most hosted
  log collectors. Set `LOG_FILE` for a rotating file as well.
- A missing `DISCORD_TOKEN` exits with a clear error instead of starting a
  broken gateway connection.
- Ephemeral state (the image cache) is process-local and cleared on restart.
- See [`IMPROVEMENTS.md`](IMPROVEMENTS.md) for known limitations and ideas that
  were intentionally deferred.

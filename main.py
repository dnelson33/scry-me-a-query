"""Application entry point."""

from __future__ import annotations

import logging
import logging.handlers
import sys

from dotenv import load_dotenv

# Load .env before importing the bot package: module import builds the Bot
# instance from environment variables such as COMMAND_PREFIX and EMOJI_GUILD_ID.
load_dotenv()

from bot import bot  # noqa: E402
from bot.config import load_settings  # noqa: E402

LOGGER = logging.getLogger("main")
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
MAX_LOG_BYTES = 5_000_000
LOG_BACKUP_COUNT = 3


def configure_logging(level_name: str, log_file: str | None) -> None:
    level = logging.getLevelNamesMapping().get(level_name.upper(), logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    log_file_error: str | None = None

    if log_file:
        try:
            handlers.append(
                logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=MAX_LOG_BYTES,
                    backupCount=LOG_BACKUP_COUNT,
                    encoding="utf-8",
                )
            )
        except OSError as error:
            # A read-only or unwritable volume should not stop the bot; stdout
            # logging is still available to the container runtime.
            log_file_error = str(error)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        format=LOG_FORMAT,
        force=True,
    )
    if log_file_error is not None:
        LOGGER.warning("Could not open LOG_FILE %s: %s", log_file, log_file_error)
    # discord.py's DEBUG output is extremely noisy; keep it at INFO unless the
    # operator explicitly asked for DEBUG.
    logging.getLogger("discord").setLevel(level if level <= logging.DEBUG else logging.INFO)


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level, settings.log_file)

    if not settings.token:
        LOGGER.error("DISCORD_TOKEN is not set. Add it to .env or the environment before starting.")
        raise SystemExit(1)

    LOGGER.info(
        "Starting bot (prefix=%r, log_level=%s, file_logging=%s)",
        settings.command_prefix,
        settings.log_level,
        bool(settings.log_file),
    )

    try:
        bot.run(settings.token, log_handler=None)
    except KeyboardInterrupt:
        LOGGER.info("Shutdown requested")
    except Exception:
        LOGGER.exception("Bot terminated unexpectedly")
        raise


if __name__ == "__main__":
    main()

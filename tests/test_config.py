from __future__ import annotations

import pytest

from bot.config import Settings, load_settings


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DISCORD_TOKEN",
        "COMMAND_PREFIX",
        "EMOJI_GUILD_ID",
        "LOG_LEVEL",
        "LOG_FILE",
    ):
        monkeypatch.delenv(name, raising=False)


def test_defaults() -> None:
    assert load_settings() == Settings(
        token=None,
        command_prefix="?",
        emoji_guild_id=None,
        log_level="INFO",
        log_file=None,
    )


def test_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISCORD_TOKEN", "abc")
    monkeypatch.setenv("COMMAND_PREFIX", "!")
    monkeypatch.setenv("EMOJI_GUILD_ID", "12345")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("LOG_FILE", "bot.log")

    settings = load_settings()

    assert settings.token == "abc"
    assert settings.command_prefix == "!"
    assert settings.emoji_guild_id == 12345
    assert settings.log_level == "DEBUG"
    assert settings.log_file == "bot.log"


def test_blank_values_fall_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISCORD_TOKEN", "")
    monkeypatch.setenv("EMOJI_GUILD_ID", "  ")
    monkeypatch.setenv("LOG_FILE", "")

    settings = load_settings()

    assert settings.token is None
    assert settings.emoji_guild_id is None
    assert settings.log_file is None


def test_invalid_guild_id_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMOJI_GUILD_ID", "not-a-number")

    assert load_settings().emoji_guild_id is None


def test_settings_are_immutable() -> None:
    settings = load_settings()

    with pytest.raises(AttributeError):
        settings.token = "new"  # type: ignore[misc]

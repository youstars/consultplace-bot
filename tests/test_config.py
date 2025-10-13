import pytest

from consultplace_bot.config import Settings


def test_settings_load_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "secret-token")
    monkeypatch.delenv("TELEGRAM_WEBHOOK_URL", raising=False)

    settings = Settings.load()

    assert settings.bot_token == "secret-token"
    assert settings.webhook_url is None


def test_settings_load_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    with pytest.raises(RuntimeError):
        Settings.load()

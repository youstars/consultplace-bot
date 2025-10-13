"""Application configuration for the ConsultPlace Telegram bot."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    """Settings loaded from environment variables."""

    bot_token: str
    webhook_url: str | None = None

    @classmethod
    def load(cls) -> "Settings":
        """Create settings by reading environment variables."""

        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise RuntimeError("Environment variable TELEGRAM_BOT_TOKEN is required")
        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        return cls(bot_token=token, webhook_url=webhook_url)


__all__ = ["Settings"]

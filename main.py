"""Entry point for running the ConsultPlace Telegram bot."""
from __future__ import annotations

import asyncio
import contextlib
import logging

try:  # pragma: no cover - aiogram is required in production
    from aiogram import Bot, Dispatcher
    from aiogram.enums import ParseMode
except ModuleNotFoundError as exc:  # pragma: no cover
    Bot = Dispatcher = ParseMode = None  # type: ignore[assignment]
    _AIOGRAM_IMPORT_ERROR = exc
else:
    _AIOGRAM_IMPORT_ERROR = None

try:  # pragma: no cover - structlog is optional in tests
    import structlog
except ModuleNotFoundError:  # pragma: no cover
    structlog = None  # type: ignore[assignment]

from consultplace_bot.config import Settings
from consultplace_bot.handlers import router
from consultplace_bot.logging import setup_logging

if structlog is None:  # pragma: no cover - fallback when structlog is missing
    logger = logging.getLogger(__name__)
else:  # pragma: no cover - executed in production
    logger = structlog.get_logger(__name__)


async def _run_bot() -> None:
    if _AIOGRAM_IMPORT_ERROR is not None:  # pragma: no cover - guard for missing dependency
        raise RuntimeError("aiogram must be installed to run the bot") from _AIOGRAM_IMPORT_ERROR

    settings = Settings.load()

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)  # type: ignore[misc]
    dp = Dispatcher()  # type: ignore[call-arg]
    dp.include_router(router)

    logger.info("bot.start", extra={"webhook_url": settings.webhook_url})
    await dp.start_polling(bot)


def main() -> None:
    """Synchronously configure logging and run the bot."""

    setup_logging()
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_run_bot())
    logger.info("bot.stop")


if __name__ == "__main__":
    main()

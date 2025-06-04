"""
Пакет `consultplace_bot.bot`.

•  При обычном импорте мы просто экспортируем подпакет
   `consultplace_bot.bot.routers`, чтобы тесты могли писать
   `from consultplace_bot.bot.routers import orders_list`.

•  «Тяжёлые» зависимости (aiogram, Redis-FSM и т.д.) загружаются
   только внутри функции `main`, поэтому при запуске unit-тестов
   никаких лишних побочных эффектов нет.
"""

from __future__ import annotations

import asyncio
import importlib
from typing import Final
from types import ModuleType


# ---------------------------------------------------------------------------
# Делаем реальный импорт подпакета routers (он не зависит от `bot` обратно,
# поэтому круговой зависимости не возникает)
routers: Final[ModuleType] = importlib.import_module(__name__ + ".routers")

__all__ = ["routers", "main"]
# ---------------------------------------------------------------------------


async def main() -> None:
    """Запустить Telegram-бота (long-polling)."""

    # ── Импортируем тяжёлые вещи только здесь ────────────────────────────
    from aiogram import Bot, Dispatcher

    from consultplace_bot.api.backend import backend
    from consultplace_bot.bot.storage import storage
    from consultplace_bot.config import settings

    # Роутеры внутри подпакета .routers:
    from consultplace_bot.bot.routers.registration import router as registration_router
    from consultplace_bot.bot.routers.new_order import router as new_order_router
    from consultplace_bot.bot.routers.order_ai import router as order_ai_router
    from consultplace_bot.bot.routers.orders_list import router as orders_list_router

    # Получаем JWT для запросов к backend-CRM
    await backend.login()

    # Создаём Dispatcher и регистрируем роутеры
    dp = Dispatcher(storage=storage)
    dp.include_router(registration_router)
    dp.include_router(new_order_router)
    dp.include_router(order_ai_router)
    dp.include_router(orders_list_router)

    # Запускаем polling
    bot = Bot(settings.telegram_token, parse_mode="HTML")
    await dp.start_polling(bot)


# Позволяет запускать файл напрямую:  python -m consultplace_bot.bot
if __name__ == "__main__":  # pragma: no cover – не попадает под покрытие
    asyncio.run(main())
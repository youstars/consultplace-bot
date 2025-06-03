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

    await backend.login()

    # сами роутеры берём из подпакета, который уже импортировали выше
    dp = Dispatcher(storage=storage)
    dp.include_router(routers.registration.router)
    dp.include_router(routers.new_order.router)
    dp.include_router(routers.order_ai.router)
    dp.include_router(routers.orders_list.router)

    # получаем JWT для запросов к backend-CRM


    # запускаем polling
    bot = Bot(settings.telegram_token, parse_mode="HTML")
    await dp.start_polling(bot)


# Позволяет запускать файл напрямую:  python -m consultplace_bot.bot
if __name__ == "__main__":  # pragma: no cover – не попадает под покрытие
    asyncio.run(main())
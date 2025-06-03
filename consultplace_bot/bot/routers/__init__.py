# consultplace_bot/bot/__init__.py

import asyncio

from aiogram import Bot, Dispatcher

from consultplace_bot.config import settings
from consultplace_bot.bot.storage import storage
from consultplace_bot.api.backend import backend
from consultplace_bot.bot.routers.registration import router as reg_router
from consultplace_bot.bot.routers.new_order import router as order_router
from consultplace_bot.bot.routers.order_ai import router as ai_router
from consultplace_bot.bot.routers.orders_list   import router as list_router # <-- добавили  ✅  noqa: F401

from . import registration     # noqa: F401
from . import new_order        # noqa: F401
from . import order_ai         # noqa: F401
from . import orders_list      # ← главное!  # noqa: F401

__all__ = [
    "registration",
    "new_order",
    "order_ai",
    "orders_list",   # чтобы   from … import orders_list   работало
]

async def main() -> None:
    # Сначала логинимся в CRM, чтобы получить JWT для всех запросов
    await backend.login()

    # Инициализируем объект Bot и Dispatcher с Redis-FSM
    bot = Bot(settings.telegram_token, parse_mode="HTML")
    dp = Dispatcher(storage=storage)

    # Регистрируем роутер регистрации
    dp.include_router(reg_router)
    dp.include_router(order_router)
    dp.include_router(ai_router)
    dp.include_router(list_router)

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
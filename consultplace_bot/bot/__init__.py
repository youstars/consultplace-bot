"""
Модуль bot: содержит функцию main() и подключает роутеры.
"""

import asyncio
from aiogram import Bot, Dispatcher

from consultplace_bot.config import settings
from consultplace_bot.bot.storage import storage
from consultplace_bot.api.backend import backend

# ⬇ сюда позже будем добавлять новые роутеры
from consultplace_bot.bot.routers.registration import router as reg_router
from consultplace_bot.bot.routers.new_order import router as order_router  # Day 2
from consultplace_bot.bot.routers.order_ai import router as ai_router

async def main() -> None:
    await backend.login()  # JWT перед запуском

    bot = Bot(settings.telegram_token, parse_mode="HTML")
    dp = Dispatcher(storage=storage)
    dp.include_router(reg_router)
    dp.include_router(order_router)
    dp.include_router(ai_router)

    await dp.start_polling(bot)

# для удобства: python -m consultplace_bot.bot тоже запустит
if __name__ == "__main__":
    asyncio.run(main())
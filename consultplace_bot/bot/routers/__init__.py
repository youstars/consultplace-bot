# consultplace_bot/bot/__init__.py

import asyncio

from aiogram import Bot, Dispatcher

from consultplace_bot.config import settings
from consultplace_bot.bot.storage import storage
from consultplace_bot.api.backend import backend
from consultplace_bot.bot.routers.registration import router as reg_router
from consultplace_bot.bot.routers.new_order import router as order_router
from consultplace_bot.bot.routers.order_ai import router as ai_router

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

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
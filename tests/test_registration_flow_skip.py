# ruff: noqa
import pytest
pytest.skip("e2e-тест временно отключён: библиотека aiogram_tests ≠ aiogram-3", allow_module_level=True)

from aiogram_tests import TestBot, TestDispatcher
from aiogram_tests.types.dataset import CALLBACK_QUERY
from consultplace_bot.bot.storage import storage
from consultplace_bot.bot.routers.registration import router


@pytest.mark.asyncio
async def test_registration_flow(respx_mock):
    # ─── мокаем CRM ──────────────────────────────────────────────────────────
    respx_mock.post("/api/auth/jwt/create/").respond(
        200, json={"access": "a", "refresh": "r"}
    )
    respx_mock.post("/api/telegram/register/").respond(
        201, json={"user_id": 99}
    )

    bot = TestBot()
    dp  = TestDispatcher(bot, storage=storage)
    dp.include_router(router)

    # ─── /start ─────────────────────────────────────────────────────────────
    updates = await dp.feed_update(bot.get_me(), text="/start")
    assert updates[-1].text.startswith("Выберите роль")

    # ─── выбираем роль «Клиент» ─────────────────────────────────────────────
    callback_data = updates[-1].reply_markup.inline_keyboard[0][0].callback_data
    # создаём CallbackQuery-объект
    callback = CALLBACK_QUERY.as_object(data=callback_data)
    updates = await dp.feed_callback_query(callback)
    assert updates[-1].text.startswith("Опишите ваш запрос")

    # ─── вводим order_goal ──────────────────────────────────────────────────
    updates = await dp.feed_update(bot.get_me(), text="Нужна аналитика рынка")
    assert "Регистрация завершена" in updates[-1].text
import pytest
# from aiogram_tests import TestBot, TestDispatcher
from consultplace_bot.bot.storage import storage
from consultplace_bot.bot.routers.new_order import router

pytest.skip("e2e test requires aiogram_tests (aiogram v2). Skipped for aiogram 3.", allow_module_level=True)

@pytest.mark.asyncio
async def test_new_order_flow(respx_mock):
    respx_mock.post("/api/auth/jwt/create/").respond(200, json={"access":"a","refresh":"r"})
    respx_mock.post("/api/orders/").respond(201, json={"order_id": 123})

    bot = TestBot()
    dp  = TestDispatcher(bot, storage=storage)
    dp.include_router(router)

    upd = await dp.feed_update(bot.get_me(), text="/new_order")
    assert upd[-1].text.startswith("Опишите ваш запрос")

    upd = await dp.feed_update(bot.get_me(), text="Нужен аналитический дашборд")
    upd = await dp.feed_update(bot.get_me(), text="В2В SaaS для HR")
    upd = await dp.feed_update(bot.get_me(), text="30.06.2025")
    upd = await dp.feed_update(bot.get_me(), text="150000")

    assert "Заявка №123" in upd[-1].text
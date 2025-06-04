# # tests/test_handlers_smoke.py
# import asyncio
# from types import SimpleNamespace
#
# import pytest
#
# from consultplace_bot.bot.routers import orders_list
#
#
# # ---------------------------- helpers ---------------------------------
#
#
# class FakeMessage(SimpleNamespace):
#     """Мини-Message с text и answer()."""
#
#     def __init__(self, text: str = "") -> None:
#         super().__init__()
#         self.text = text
#         self.answers: list[str] = []
#
#     async def answer(self, text: str, **_) -> None:  # noqa: D401
#         self.answers.append(text)
#
#
# def _get_my_orders_handler():
#     """
#     Возвращает callback зарегистрированного хэндлера `/my_orders`.
#
#     Router хранит их в .message.handlers – берём первый,
#     чей фильтр содержит Command('my_orders').
#     """
#     for h in orders_list.router.message.handlers:
#         if any(
#             getattr(f, "commands", []) == {"my_orders"}
#             for f in h.filters
#         ):
#             return h.callback
#     raise RuntimeError("хэндлер /my_orders не найден")
#
#
# # ----------------------------- tests ----------------------------------
#
#
# @pytest.mark.asyncio
# async def test_cmd_my_orders(monkeypatch):
#     """Smoke: хэндлер отвечает и подставляет номер заказа."""
#     async def fake_list_orders(*_, **__):
#         return [{"id": 7, "order_goal": "Лендинг", "status": "NEW"}]
#
#     # подменяем функцию backend.list_orders, чтобы не делать HTTP-запрос
#     from consultplace_bot import api as _api  # noqa: WPS433
#     monkeypatch.setattr(_api.backend.backend, "list_orders", fake_list_orders)
#
#     msg = FakeMessage("/my_orders")
#     handler = _get_my_orders_handler()
#
#     # хэндлеры aiogram 3 – обычные coroutine-функции
#     await handler(msg)
#
#     assert msg.answers              # что-то ответили
#     assert "Лендинг" in msg.answers[0]
#     assert "№7" in msg.answers[0]
#
#
# @pytest.mark.asyncio
# async def test_ask_budget_validates_int(monkeypatch):
#     """
#     Проверяем шаг FSM, который спрашивает бюджет.
#
#     Передаём текст «не-число» – ждём, что значение в state не сохранится,
#     а пользователь получит просьбу ввести цифру.
#     """
#     from consultplace_bot.bot.routers.new_order import _ask_budget as ask_budget
#
#     saved: dict = {}
#
#     async def fake_update_data(**kw):
#         saved.update(kw)
#
#     state = SimpleNamespace(update_data=fake_update_data)
#     msg = FakeMessage("десять тысяч")
#
#     await ask_budget(msg, state=state)
#
#     assert not saved                # число не распарсилось
#     assert any("цифр" in a.lower() for a in msg.answers)
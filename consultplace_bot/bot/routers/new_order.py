from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
from consultplace_bot.api.backend import backend as be
import httpx

router = Router(name="new_order")


class Wizard(StatesGroup):
    order_goal = State()
    prod_serv = State()
    deadline = State()
    budget = State()


@router.message(Command("new_order"))
async def new_order_start(msg: Message, state: FSMContext):
    await msg.answer("Опишите ваш запрос (не более 200 символов):")
    await state.set_state(Wizard.order_goal)


@router.message(Wizard.order_goal)
async def step_prod(msg: Message, state: FSMContext):
    text = msg.text.strip()
    if len(text) > 200:
        await msg.answer("Слишком длинное описание: максимум 200 символов. Пожалуйста, попробуйте снова.")
        return  # оставляем состояние Wizard.order_goal, чтобы пользователь ввел заново

    await state.update_data(order_goal=text)  # уже не обрезаем, потому что выше проверили длину
    await msg.answer("Уточните продукт / услугу, ЦА (до 200 символов):")
    await state.set_state(Wizard.prod_serv)


@router.message(Wizard.prod_serv)
async def step_deadline(msg: Message, state: FSMContext):
    text = msg.text.strip()
    if len(text) > 200:
        await msg.answer("Слишком длинный текст: максимум 200 символов. Пожалуйста, попробуйте снова.")
        return  # остаёмся в Wizard.prod_serv

    await state.update_data(prod_serv=text)
    await msg.answer("Дедлайн (dd.mm.yyyy):")
    await state.set_state(Wizard.deadline)


@router.message(Wizard.deadline)
async def _ask_budget(msg: Message, state: FSMContext):
    try:
        # проверяем формат "dd.mm.yyyy"
        datetime.strptime(msg.text, "%d.%m.%Y")
        await state.update_data(deadline=msg.text)
        await msg.answer("Введите бюджет цифрой, пожалуйста (например, 50000):")
        await state.set_state(Wizard.budget)
    except ValueError:
        await msg.answer("Введите дедлайн в формате dd.mm.yyyy, пожалуйста.")


@router.message(Wizard.budget)
async def finish(msg: Message, state: FSMContext):
    # 1) Проверяем, что бюджет — это целое число
    try:
        budget_int = int(msg.text.replace(" ", ""))
    except ValueError:
        await msg.answer("Введите бюджет ЦИФРОЙ, пожалуйста (например, 50000).")
        return  # остаёмся в Wizard.budget

    # 2) Собираем всё из FSMContext
    data = await state.get_data()
    order_goal = data.get("order_goal")
    product_or_service = data.get("prod_serv")
    deadline_str = data.get("deadline")  # в формате "dd.mm.yyyy"

    # 3) Конвертируем дедлайн в ISO (или None, если не указан)
    iso_deadline = None
    if deadline_str:
        try:
            iso_deadline = datetime.strptime(deadline_str, "%d.%m.%Y").date().isoformat()
        except ValueError:
            await msg.answer("Ошибка в формате даты. Пожалуйста, начните заново с /new_order.")
            await state.clear()
            return

    # 4) Формируем payload
    payload = {
        "order_goal": order_goal,                      # длина ≤ 200
        "product_or_service": product_or_service,      # длина ≤ 200
        "project_deadline": iso_deadline,
        "estimated_budget": str(budget_int),
        # "telegram_id": msg.from_user.id,  # добавляйте, если точно ожидается бекендом
    }

    # 5) Вызываем BackendClient.create_order(...)
    try:
        order_id = await be.create_order(payload)
    except httpx.HTTPStatusError as exc:
        detail_json = exc.response.json()   # без await!
        await msg.answer(
            "❌ Ошибка при создании заказа (400 Bad Request).\n"
            f"Сервер вернул:\n<code>{detail_json!r}</code>",
            parse_mode="HTML"
        )
        return
    except Exception as exc:
        await msg.answer(f"❌ Непредвиденная ошибка при создании заказа: {exc}")
        return

    # 6) Успех: очищаем FSM и сообщаем № заказа
    await state.clear()
    await msg.answer(f"✅ Ваш заказ #{order_id} успешно создан!")
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from consultplace_bot.api.backend import backend

router = Router(name="new_order")


class OrderWizard(StatesGroup):
    order_goal        = State()
    product_service   = State()
    deadline          = State()
    budget            = State()


@router.message(Command("new_order"))
async def cmd_new_order(msg: Message, state: FSMContext):
    await msg.answer("Опишите ваш запрос (до 512 симв.):")
    await state.set_state(OrderWizard.order_goal)


@router.message(OrderWizard.order_goal)
async def q_product(msg: Message, state: FSMContext):
    await state.update_data(order_goal=msg.text[:512])
    await msg.answer("Уточните продукт / услугу, ЦА (до 512 симв.):")
    await state.set_state(OrderWizard.product_service)


@router.message(OrderWizard.product_service)
async def q_deadline(msg: Message, state: FSMContext):
    await state.update_data(product_service=msg.text[:512])
    await msg.answer("Дедлайн (dd.mm.yyyy):")
    await state.set_state(OrderWizard.deadline)


@router.message(OrderWizard.deadline)
async def q_budget(msg: Message, state: FSMContext):
    await state.update_data(deadline=msg.text)
    await msg.answer("На какой бюджет рассчитываете? (₽, цифрой)")
    await state.set_state(OrderWizard.budget)


@router.message(OrderWizard.budget)
async def finish(msg: Message, state: FSMContext):
    await state.update_data(budget=msg.text)
    data = await state.get_data()

    payload = {
        "telegram_id": msg.from_user.id,
        "order_goal": data["order_goal"],
        "product_or_service": data["product_service"],
        "project_deadline": data["deadline"],
        "estimated_budget": data["budget"],
    }
    order_id = await backend.create_order(payload)

    await msg.answer(f"✅ Заявка №<code>{order_id}</code> создана!")
    await state.clear()
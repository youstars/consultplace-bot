from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from consultplace_bot.api.backend import backend

router = Router(name="registration")

# ─────────────────────────────────────── FSM ──────────────────────────────────────
class Reg(StatesGroup):
    role        = State()
    order_goal  = State()

# ─────────────────────────────────────── handlers ─────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Клиент",     callback_data="role:client"),
        InlineKeyboardButton(text="Специалист", callback_data="role:specialist"),
    ]])
    await msg.answer("Выберите роль:", reply_markup=kb)
    await state.set_state(Reg.role)


@router.callback_query(F.data.startswith("role:"))
async def choose_role(cb: CallbackQuery, state: FSMContext) -> None:
    role = cb.data.split(":")[1]
    await state.update_data(role=role)
    await cb.message.edit_text("Опишите ваш запрос (одним предложением):")
    await state.set_state(Reg.order_goal)
    await cb.answer()


@router.message(Reg.order_goal)
async def collect_goal(msg: Message, state: FSMContext) -> None:
    await state.update_data(order_goal=msg.text)
    data = await state.get_data()

    payload = {
        "telegram_id":   msg.from_user.id,
        "first_name":    msg.from_user.first_name,
        "last_name":     msg.from_user.last_name,
        "username":      msg.from_user.username,
        "role":          data["role"],
        "order_goal":    data["order_goal"],
    }

    user_id = await backend.register_user(payload)

    await msg.answer(f"🎉 Регистрация завершена! Ваш ID: <code>{user_id}</code>")
    await state.clear()
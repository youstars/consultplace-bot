from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router(name="registration")


# ── простейшая версия ─────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer(
        "Привет! Я ConsultPlace-бот.\n"
        "Пока доступна одна команда: /new_order – создать заказ."
    )


# ── если хочешь сразу полноценный wizard с выбором роли ───────────
class RegFSM(StatesGroup):
    choose_role = State()
    order_goal  = State()

@router.message(CommandStart())
async def start_wizard(msg: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Клиент",     callback_data="role:client"),
            InlineKeyboardButton(text="Специалист", callback_data="role:specialist"),
        ]]
    )
    await msg.answer("Выберите роль:", reply_markup=kb)
    await state.set_state(RegFSM.choose_role)
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

from consultplace_bot.api.backend import backend


router = Router(name="new_order")


class Wizard(StatesGroup):
    order_goal  = State()
    prod_serv   = State()
    deadline    = State()
    budget      = State()


# ───────────── /new_order ─────────────
@router.message(Command("new_order"))
async def new_order_start(msg: Message, state: FSMContext):
    await msg.answer("Опишите ваш запрос (до 512 симв.):")
    await state.set_state(Wizard.order_goal)


@router.message(Wizard.order_goal)
async def step_prod(msg: Message, state: FSMContext):
    await state.update_data(order_goal=msg.text[:512])
    await msg.answer("Уточните продукт / услугу, ЦА (до 512 симв.):")
    await state.set_state(Wizard.prod_serv)


@router.message(Wizard.prod_serv)
async def step_deadline(msg: Message, state: FSMContext):
    await state.update_data(prod_serv=msg.text[:512])
    await msg.answer("Дедлайн (dd.mm.yyyy):")
    await state.set_state(Wizard.deadline)


@router.message(Wizard.deadline)
async def step_budget(msg: Message, state: FSMContext):
    await state.update_data(deadline=msg.text)
    await msg.answer("На какой бюджет рассчитываете? (₽, цифрой)")
    await state.set_state(Wizard.budget)


@router.message(Wizard.budget)
async def finish(msg: Message, state: FSMContext):
    await state.update_data(budget=msg.text)
    data = await state.get_data()

    # ── конвертируем дату dd.mm.yyyy → ISO "2025-06-30"
    iso_deadline = None
    if data["deadline"]:
        iso_deadline = datetime.strptime(data["deadline"], "%d.%m.%Y").date().isoformat()

    payload = {
        "order_goal":         data["order_goal"],
        "product_or_service": data["prod_serv"],
        "project_deadline":   iso_deadline,            # ↩︎ iso
        "estimated_budget":   str(data["budget"]),     # ↩︎ строкой
        "telegram_id":        msg.from_user.id,        # если CRM это принимает
    }

    order_id = await backend.create_order(payload)

    # ─── предлагаем сгенерировать ТЗ ────────────────────────
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="⚙️ Сгенерировать ТЗ",
                callback_data=f"order:tz:generate:{order_id}"
            )
        ]]
    )
    await msg.answer(
        f"✅ Заявка №<code>{order_id}</code> создана!\n"
        "Нажмите кнопку ниже, чтобы получить черновик ТЗ:",
        reply_markup=kb,
    )
    await state.clear()
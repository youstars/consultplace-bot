from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from consultplace_bot.api.backend import backend

router = Router(name="order_ai")

# ---------- CALLBACK after /new_order wizard finished ----------
@router.callback_query(F.data.startswith("order:tz:generate:"))
async def ai_generate_tz(cb: CallbackQuery):
    order_id = int(cb.data.split(":")[-1])

    # вызываем AI
    tz = await backend.request_tz(order_id, payload={})   # в MVP достаточно order_id
    text = f"<b>Черновик ТЗ</b>\n\n{tz}\n\nВсё верно?"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Всё верно", callback_data=f"order:tz:ok:{order_id}"),
            InlineKeyboardButton(text="✏️ Обсудить позже", callback_data="noop")
        ]]
    )

    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()

# ---------- CALLBACK "Всё верно" ----------
@router.callback_query(F.data.startswith("order:tz:ok:"))
async def ai_estimate(cb: CallbackQuery):
    order_id = int(cb.data.split(":")[-1])

    # на практике лучше кэшировать tz, но для MVP запрашиваем вновь
    tz = "cached tz"  # тут возьмём из БД/redis; опустим ради краткости

    cost = await backend.estimate_cost(order_id, tz)
    text = (
        f"💰 <b>Оценка стоимости</b>\n"
        f"Диапазон: {cost['min_price']:,}–{cost['max_price']:,} {cost['currency']}\n"
        f"Трудоёмкость: {cost['effort_hours']} ч.\n\n"
        "Подтверждаете бюджет?"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Подтвердить",     callback_data="noop"),
            InlineKeyboardButton(text="🔙 Обсудить позже", callback_data="noop")
        ]]
    )

    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()
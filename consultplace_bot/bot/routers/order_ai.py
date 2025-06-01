from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from html import escape
from consultplace_bot.api.backend import backend

router = Router(name="order_ai")

@router.callback_query(F.data.startswith("order:tz:generate:"))
async def ai_generate_tz(cb: CallbackQuery):
    order_id = int(cb.data.rsplit(":", 1)[-1])

    tz = await backend.request_tz(order_id, payload={})   # в MVP payload пустой
    if tz.startswith("🚧"):
        await cb.message.answer(tz)
        await cb.answer()
        return
    text = f"<b>Черновик ТЗ</b>\n\n{escape(tz)}\n\nВсё верно?"

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton("✅ Всё верно", callback_data=f"order:tz:ok:{order_id}"),
        InlineKeyboardButton("✏️ Обсудить позже", callback_data="noop")
    ]])
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data.startswith("order:tz:ok:"))
async def ai_estimate(cb: CallbackQuery):
    order_id = int(cb.data.rsplit(":", 1)[-1])

    cost = await backend.estimate_cost(order_id, tz="approved")   # tz можно передать при необходимости
    text = (
        f"💰 <b>Оценка стоимости</b>\n"
        f"Диапазон: {cost['min_price']:,}–{cost['max_price']:,} {cost['currency']}\n"
        f"Трудоёмкость: {cost['effort_hours']} ч.\n\n"
        "Подтверждаете бюджет?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton("✅ Подтвердить", callback_data="noop"),
        InlineKeyboardButton("🔙 Обсудить позже", callback_data="noop")
    ]])
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()
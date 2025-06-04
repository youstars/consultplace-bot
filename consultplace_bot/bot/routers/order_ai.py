from aiogram import Router, F, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
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

class GenTZ(CallbackData, prefix="gen_tz"):
    id: int

@router.callback_query(GenTZ.filter())
async def generate_tz(cb: types.CallbackQuery, callback_data: GenTZ):
    await cb.answer("Генерирую ТЗ…", show_alert=False)

    # 1️⃣ получаем все заявки (пагинированный dict c ключом "results")
    data = await backend.list_orders()
    if isinstance(data, dict) and "results" in data:
        orders = data["results"]
    elif isinstance(data, list):
        orders = data
    else:
        orders = []

    # 2️⃣ находим нужную заявку
    order = next((o for o in orders if o.get("id") == callback_data.id), None)
    if order is None:
        await cb.message.answer("❌ Заявка не найдена, обновите список.")
        await cb.answer()
        return

    # 3️⃣ LLM-генерация ТЗ (например, через свой метод ai_generate_tz)
    tz_text = await backend.ai_generate_tz(order)

    # 4️⃣ сохраняем черновик ТЗ в CRM (не ломаем пользователя, даже если упадёт)
    try:
        await backend.request_tz(order["id"], {"tz": tz_text})
    except Exception:
        # здесь можно залогировать ошибку, но продолжаем UX
        pass

    # 5️⃣ отправляем сгенерированный ТЗ пользователю
    from html import escape
    await cb.message.answer(
        f"✅ ТЗ для заказа *#{order['id']}* готово:\n\n{escape(tz_text)}",
        parse_mode="Markdown",
    )
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


@router.callback_query(lambda c: c.data and c.data.startswith("tz:"))
async def generate_tz_cb(query: CallbackQuery):
    # callback_data = "tz:<order_id>"
    _, order_id_str = query.data.split(":", maxsplit=1)
    try:
        order_id = int(order_id_str)
    except ValueError:
        await query.answer("❌ Неверный ID заказа", show_alert=True)
        return

    await query.answer("⏳ Генерирую ТЗ…", show_alert=False)

    try:
        tz_text = await backend.request_tz(order_id, {})
    except Exception:
        await query.message.answer("❌ Ошибка при генерации ТЗ, попробуйте позже.")
        return

    reply = f"📝 Техническое задание для заказа #{order_id}:\n\n{tz_text}"
    await query.message.answer(reply)
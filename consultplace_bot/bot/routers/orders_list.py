from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from consultplace_bot.api.backend import backend
from consultplace_bot.bot.routers.order_ai import GenTZ

router = Router(name="orders_list")


def _render_table(orders: list) -> str:
    if not orders:
        return "📭 У вас пока нет заказов."
    lines = ["<b>ID │ Статус │ Название</b>"]
    for o in orders:
        if isinstance(o, dict):
            order_id = o.get("id", "N/A")
            status = o.get("status", "N/A")
            goal = o.get("order_goal", "")[:35]
            lines.append(f"{order_id:>3} │ {status:<8} │ {goal}")
        else:
            lines.append(f"Ошибка: неожиданный тип данных: {type(o)}")
    return "\n".join(lines)


def _order_row(o: dict) -> str:
    return f"• #{o['id']} — {o['order_goal']} — *{o['status']}*"


def _order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Сгенерировать ТЗ",
                    callback_data=f"gen_tz:{order_id}",
                )
            ]
        ]
    )


@router.message(Command("my_orders"))
async def list_my_orders(msg: Message):
    try:
        data = await backend.list_orders()
    except Exception:
        await msg.answer("❌ Не удалось получить список заказов, попробуйте позже.")
        return

    if not isinstance(data, dict) or "results" not in data:
        await msg.answer("❌ Некорректный ответ от сервера.")
        return

    orders = data["results"]
    if not orders:
        await msg.answer("У вас нет активных заказов.")
        return

    rows: list[list[InlineKeyboardButton]] = []
    for o in orders:
        order_id = o.get("id")
        goal = o.get("order_goal", "—")
        status = o.get("status", "—")
        text = f"#{order_id}: {goal} ({status})"
        # вместо "tz:<id>" теперь упаковываем через GenTZ
        btn = InlineKeyboardButton(
            text=text,
            callback_data=GenTZ(id=order_id).pack()
        )
        rows.append([btn])

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    await msg.answer("Выберите заказ, чтобы сгенерировать ТЗ:", reply_markup=keyboard)
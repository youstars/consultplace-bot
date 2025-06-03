from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from consultplace_bot.api.backend import backend

router = Router(name="orders_list")

def _render_table(orders: list) -> str:
    if not orders:
        return "📭 У вас пока нет заказов."
    lines = ["<b>ID │ Статус │ Название</b>"]
    for o in orders:
        if isinstance(o, dict):
            order_id = o.get('id', 'N/A')
            status = o.get('status', 'N/A')
            goal = o.get('order_goal', '')[:35]
            lines.append(f"{order_id:>3} │ {status:<8} │ {goal}")
        else:
            lines.append(f"Ошибка: неожиданный тип данных: {type(o)}")
    return "\n".join(lines)

@router.message(Command("my_orders"))
async def my_orders(msg: Message):
    response = await backend.list_orders()
    # Извлекаем список заказов из ключа 'results'
    orders = response.get('results', []) if isinstance(response, dict) else response

    await msg.answer(_render_table(orders), parse_mode="HTML")
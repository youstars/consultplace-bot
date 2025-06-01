# consultplace_bot/bot/routers/new_order.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router(name="new_order")

@router.message(Command("new_order"))
async def cmd_new_order(msg: Message):
    await msg.answer("📝 Новый заказ — пока заглушка.")
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from consultplace_bot.api.backend import backend

router = Router(name="match_ai")

def _short_card(sp: dict) -> str:
    return (f"👤 <b>{sp['id']}</b>\n"
            f"Рейтинг: {sp['overall_rating']:.2%}\n"
            f"Ставка: {sp['approx_hourly_rate']} ₽/ч\n")

@router.callback_query(F.data.startswith("order:match:start:"))
async def ai_match(cb: CallbackQuery):
    order_id = int(cb.data.rsplit(":", 1)[-1])

    specialists = await backend.match_specialists(order_id)
    if not specialists:
        await cb.message.answer("🚧 Подбор специалистов пока недоступен.")
        await cb.answer()
        return

    # берём top-3
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(f"👤 {s['id']}", callback_data=f"order:match:choose:{order_id}:{s['id']}")]
            for s in specialists
        ]
    )
    cards = "\n\n".join(_short_card(s) for s in specialists)
    await cb.message.edit_text(f"<b>Подходящие специалисты:</b>\n\n{cards}\nВыберите кандидата:",
                               reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data.startswith("order:match:choose:"))
async def confirm_candidate(cb: CallbackQuery):
    parts = cb.data.split(":")
    order_id, sp_id = int(parts[-2]), int(parts[-1])
    await cb.message.edit_text(f"✅ Специалист {sp_id} приглашён! Ожидайте отклик.")
    await cb.answer()
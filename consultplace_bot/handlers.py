"""Message handlers for the ConsultPlace Telegram bot."""
from __future__ import annotations

from typing import Any, Callable

try:  # pragma: no cover - the real aiogram branch is exercised in production
    from aiogram import Router as AiogramRouter
    from aiogram.filters import Command as AiogramCommand
    from aiogram.filters import CommandStart as AiogramCommandStart
    from aiogram.types import Message
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without aiogram
    AiogramRouter = None
    AiogramCommand = None
    AiogramCommandStart = None

    class Message:  # type: ignore[too-many-ancestors]
        """Lightweight stand-in used during unit tests when aiogram is unavailable."""

        ...


def _no_op_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    return func


class _RouterStub:
    """Simplified router that keeps decorators functional during tests."""

    def message(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return _no_op_decorator


if AiogramRouter is None:  # pragma: no cover - executed only when aiogram is missing
    Router = _RouterStub  # type: ignore[assignment]

    def Command(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Fallback stub for :func:`aiogram.filters.Command`."""

        return _no_op_decorator

    def CommandStart(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Fallback stub for :func:`aiogram.filters.CommandStart`."""

        return _no_op_decorator
else:
    Router = AiogramRouter  # pragma: no cover - type alias for static checkers
    Command = AiogramCommand
    CommandStart = AiogramCommandStart


router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Greet a user who sends the /start command."""

    await message.answer(
        "Привет! Я бот ConsultPlace и помогу подобрать специалистов. "
        "Отправьте /help, чтобы узнать больше."
    )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Explain how the bot can help the user."""

    await message.answer(
        "Я могу связать вас с консультантами ConsultPlace. "
        "Просто расскажите, какая помощь нужна, и я передам информацию нашей команде."
    )


@router.message()
async def handle_default(message: Message) -> None:
    """Fallback handler for arbitrary messages."""

    await message.answer(
        "Спасибо за сообщение! Мы уже работаем над тем, чтобы помочь вам. "
        "Если хотите начать сначала, отправьте /start."
    )


__all__ = ["router", "handle_start", "handle_help", "handle_default"]

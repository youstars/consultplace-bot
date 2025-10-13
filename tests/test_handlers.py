from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock

from consultplace_bot.handlers import handle_default, handle_help, handle_start


@dataclass
class DummyMessage:
    """Minimal stand-in for :class:`aiogram.types.Message`."""

    text: str
    answer: AsyncMock = field(default_factory=AsyncMock)

    def __getattr__(self, item: str) -> Any:  # pragma: no cover - safety net for unexpected attrs
        raise AttributeError(item)


def test_handle_start_greets_user() -> None:
    message = DummyMessage(text="/start")

    asyncio.run(handle_start(message))

    message.answer.assert_awaited_once()
    args, _ = message.answer.await_args
    assert "Привет" in args[0]


def test_handle_help_describes_bot() -> None:
    message = DummyMessage(text="/help")

    asyncio.run(handle_help(message))

    message.answer.assert_awaited_once()
    args, _ = message.answer.await_args
    assert "ConsultPlace" in args[0]


def test_handle_default_acknowledges_message() -> None:
    message = DummyMessage(text="Расскажите мне о себе")

    asyncio.run(handle_default(message))

    message.answer.assert_awaited_once()
    args, _ = message.answer.await_args
    assert "Спасибо" in args[0]

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.metrics import BOT_ERRORS_TOTAL

logger = logging.getLogger("bot.errors")


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict,
    ):
        try:
            return await handler(event, data)
        except Exception as exc:
            BOT_ERRORS_TOTAL.inc()
            logger.exception("Unhandled error: %s", exc)

            if isinstance(event, CallbackQuery):
                await event.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
            elif isinstance(event, Message):
                await event.answer("Произошла ошибка. Попробуйте позже.")
            return None

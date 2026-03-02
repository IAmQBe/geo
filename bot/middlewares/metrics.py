from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.metrics import BOT_HANDLER_DURATION, BOT_REQUESTS_TOTAL


class MetricsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict,
    ):
        update_type = "other"
        if isinstance(event, Message):
            update_type = "message"
        elif isinstance(event, CallbackQuery):
            update_type = "callback"

        BOT_REQUESTS_TOTAL.labels(update_type=update_type).inc()
        with BOT_HANDLER_DURATION.time():
            return await handler(event, data)

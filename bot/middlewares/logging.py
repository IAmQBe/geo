from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger("bot.middleware")


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict,
    ):
        if isinstance(event, Message):
            logger.info("message user=%s text=%s", event.from_user.id if event.from_user else None, event.text)
        elif isinstance(event, CallbackQuery):
            logger.info(
                "callback user=%s data=%s",
                event.from_user.id if event.from_user else None,
                event.data,
            )
        return await handler(event, data)

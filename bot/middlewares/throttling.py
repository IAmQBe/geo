from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 5, period_seconds: int = 1) -> None:
        self.rate_limit = rate_limit
        self.period_seconds = period_seconds
        self._requests: dict[int, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict,
    ):
        user_id = self._resolve_user_id(event)
        if user_id is None:
            return await handler(event, data)

        now = time.monotonic()
        async with self._lock:
            window = self._requests[user_id]
            while window and now - window[0] > self.period_seconds:
                window.popleft()

            if len(window) >= self.rate_limit:
                if isinstance(event, CallbackQuery):
                    await event.answer("Слишком много запросов. Попробуй через секунду.", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer("Слишком много запросов. Попробуй через секунду.")
                return None

            window.append(now)

        return await handler(event, data)

    def _resolve_user_id(self, event: TelegramObject) -> int | None:
        if isinstance(event, Message) and event.from_user:
            return event.from_user.id
        if isinstance(event, CallbackQuery) and event.from_user:
            return event.from_user.id
        return None

from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from db.base import async_session_factory
from db.repositories.user_repository import UserRepository


class CityMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict,
    ):
        if self._is_bypass_event(event):
            return await handler(event, data)

        tg_user_id = self._resolve_user_id(event)
        if tg_user_id is None:
            return await handler(event, data)

        async with async_session_factory() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(tg_user_id)

        if user is None or user.preferred_city_id is not None:
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer("Сначала выбери город через /start", show_alert=True)
        elif isinstance(event, Message):
            await event.answer("Сначала выбери город через /start")
        return None

    def _is_bypass_event(self, event: TelegramObject) -> bool:
        if isinstance(event, Message):
            text = event.text or ""
            return text.startswith("/start")

        if isinstance(event, CallbackQuery):
            callback_data = event.data or ""
            return callback_data.startswith("city:")

        return False

    def _resolve_user_id(self, event: TelegramObject) -> int | None:
        if isinstance(event, Message) and event.from_user:
            return event.from_user.id
        if isinstance(event, CallbackQuery) and event.from_user:
            return event.from_user.id
        return None

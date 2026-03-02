from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from db.repositories import UserRepository


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def touch_user(self, tg_user: TgUser) -> User:
        return await self.repo.create_or_update(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language_code=tg_user.language_code,
        )

    async def set_city(self, user_id: int, city_id: int) -> None:
        await self.repo.set_preferred_city(user_id=user_id, city_id=city_id)

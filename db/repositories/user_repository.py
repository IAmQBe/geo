from datetime import datetime, UTC

from sqlalchemy import select

from db.models import User
from db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language_code: str | None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code or "ru",
                last_active_at=datetime.now(UTC),
            )
            self.session.add(user)
            await self.session.flush()
            return user

        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.language_code = language_code or user.language_code
        user.last_active_at = datetime.now(UTC)
        await self.session.flush()
        return user

    async def set_preferred_city(self, user_id: int, city_id: int) -> None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return
        user.preferred_city_id = city_id
        await self.session.flush()

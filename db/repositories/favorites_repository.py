from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Place, UserFavorite
from db.repositories.base_repository import BaseRepository


class FavoritesRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def is_favorite(self, user_id: int, place_id: int) -> bool:
        query = select(UserFavorite.id).where(
            UserFavorite.user_id == user_id,
            UserFavorite.place_id == place_id,
        )
        return (await self.session.execute(query)).scalar_one_or_none() is not None

    async def add(self, user_id: int, place_id: int) -> None:
        if await self.is_favorite(user_id=user_id, place_id=place_id):
            return
        self.session.add(UserFavorite(user_id=user_id, place_id=place_id))
        await self.session.flush()

    async def remove(self, user_id: int, place_id: int) -> None:
        query = select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.place_id == place_id,
        )
        favorite = (await self.session.execute(query)).scalar_one_or_none()
        if favorite is None:
            return
        await self.session.delete(favorite)
        await self.session.flush()

    async def toggle(self, user_id: int, place_id: int) -> bool:
        if await self.is_favorite(user_id=user_id, place_id=place_id):
            await self.remove(user_id=user_id, place_id=place_id)
            return False

        await self.add(user_id=user_id, place_id=place_id)
        return True

    async def list_places(self, user_id: int, limit: int, offset: int) -> tuple[list[Place], int]:
        total_query = select(func.count(UserFavorite.id)).where(UserFavorite.user_id == user_id)
        total = (await self.session.execute(total_query)).scalar_one()

        query = (
            select(Place)
            .join(UserFavorite, UserFavorite.place_id == Place.id)
            .options(selectinload(Place.category), selectinload(Place.city))
            .where(UserFavorite.user_id == user_id, Place.is_active.is_(True))
            .order_by(UserFavorite.added_at.desc(), Place.id.desc())
            .limit(limit)
            .offset(offset)
        )
        items = list((await self.session.execute(query)).scalars().all())
        return items, int(total)

    async def count(self, user_id: int) -> int:
        query = select(func.count(UserFavorite.id)).where(UserFavorite.user_id == user_id)
        return int((await self.session.execute(query)).scalar_one())

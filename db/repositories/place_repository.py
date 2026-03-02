from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Category, Place
from db.repositories.base_repository import BaseRepository


class PlaceRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_city_and_category(
        self,
        city_id: int,
        category_slug: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Place], int]:
        total_query = (
            select(func.count(Place.id))
            .join(Category, Place.category_id == Category.id)
            .where(
                Place.city_id == city_id,
                Category.slug == category_slug,
                Place.is_active.is_(True),
            )
        )
        total = (await self.session.execute(total_query)).scalar_one()

        items_query = (
            select(Place)
            .join(Category, Place.category_id == Category.id)
            .options(selectinload(Place.category), selectinload(Place.city))
            .where(
                Place.city_id == city_id,
                Category.slug == category_slug,
                Place.is_active.is_(True),
            )
            .order_by(Place.rating.desc().nullslast(), Place.review_count.desc(), Place.id.asc())
            .limit(limit)
            .offset(offset)
        )
        items = list((await self.session.execute(items_query)).scalars().all())
        return items, int(total)

    async def get_by_id(self, place_id: int) -> Place | None:
        query = (
            select(Place)
            .options(
                selectinload(Place.category),
                selectinload(Place.city),
                selectinload(Place.photos),
            )
            .where(Place.id == place_id)
        )
        return (await self.session.execute(query)).scalar_one_or_none()

    async def list_by_ids(self, place_ids: list[int]) -> list[Place]:
        if not place_ids:
            return []

        query = (
            select(Place)
            .options(selectinload(Place.category), selectinload(Place.city))
            .where(Place.id.in_(place_ids), Place.is_active.is_(True))
        )
        places = list((await self.session.execute(query)).scalars().all())
        index = {place_id: idx for idx, place_id in enumerate(place_ids)}
        return sorted(places, key=lambda item: index.get(item.id, 0))

    async def search(self, city_id: int, query_text: str, limit: int = 30) -> list[Place]:
        pattern = f"%{query_text.strip()}%"
        query = (
            select(Place)
            .options(selectinload(Place.category), selectinload(Place.city))
            .where(
                Place.city_id == city_id,
                Place.is_active.is_(True),
                or_(
                    Place.name.ilike(pattern),
                    Place.description.ilike(pattern),
                    Place.ai_description.ilike(pattern),
                    Place.address.ilike(pattern),
                ),
            )
            .order_by(Place.rating.desc().nullslast(), Place.review_count.desc(), Place.id.asc())
            .limit(limit)
        )
        return list((await self.session.execute(query)).scalars().all())

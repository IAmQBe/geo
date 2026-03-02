from sqlalchemy import select

from db.models import City
from db.repositories.base_repository import BaseRepository


class CityRepository(BaseRepository):
    async def list_active(self) -> list[City]:
        result = await self.session.execute(
            select(City).where(City.is_active.is_(True)).order_by(City.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, city_id: int) -> City | None:
        result = await self.session.execute(select(City).where(City.id == city_id))
        return result.scalar_one_or_none()

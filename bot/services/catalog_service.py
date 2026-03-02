from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Category, City
from db.repositories import CategoryRepository, CityRepository


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self.city_repo = CityRepository(session)
        self.category_repo = CategoryRepository(session)

    async def active_cities(self) -> list[City]:
        return await self.city_repo.list_active()

    async def active_categories(self) -> list[Category]:
        return await self.category_repo.list_active()

    async def city_by_id(self, city_id: int) -> City | None:
        return await self.city_repo.get_by_id(city_id)

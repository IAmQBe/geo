from sqlalchemy import select

from db.models import Category
from db.repositories.base_repository import BaseRepository


class CategoryRepository(BaseRepository):
    async def list_active(self) -> list[Category]:
        result = await self.session.execute(
            select(Category).where(Category.is_active.is_(True)).order_by(Category.sort_order)
        )
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

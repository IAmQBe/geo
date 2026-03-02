from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Place, VisitHistory
from db.repositories import FavoritesRepository, HistoryRepository, PlaceRepository, ReviewRepository


class PlaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.place_repo = PlaceRepository(session)
        self.favorites_repo = FavoritesRepository(session)
        self.history_repo = HistoryRepository(session)
        self.review_repo = ReviewRepository(session)

    async def list_places_by_category(
        self,
        city_id: int,
        category_slug: str,
        page: int,
        page_size: int,
    ) -> tuple[list[Place], int]:
        page = max(page, 1)
        offset = (page - 1) * page_size
        places, total = await self.place_repo.list_by_city_and_category(
            city_id=city_id,
            category_slug=category_slug,
            limit=page_size,
            offset=offset,
        )
        total_pages = max(1, ceil(total / page_size)) if total else 1
        return places, total_pages

    async def place_card(self, place_id: int) -> Place | None:
        return await self.place_repo.get_by_id(place_id)

    async def toggle_favorite(self, user_id: int, place_id: int) -> bool:
        return await self.favorites_repo.toggle(user_id=user_id, place_id=place_id)

    async def is_favorite(self, user_id: int, place_id: int) -> bool:
        return await self.favorites_repo.is_favorite(user_id=user_id, place_id=place_id)

    async def list_favorites(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[Place], int]:
        page = max(page, 1)
        offset = (page - 1) * page_size
        places, total = await self.favorites_repo.list_places(user_id=user_id, limit=page_size, offset=offset)
        total_pages = max(1, ceil(total / page_size)) if total else 1
        return places, total_pages

    async def add_visit(self, user_id: int, place_id: int) -> VisitHistory:
        return await self.history_repo.add_visit(user_id=user_id, place_id=place_id, is_confirmed=True)

    async def list_history(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[VisitHistory], int]:
        page = max(page, 1)
        offset = (page - 1) * page_size
        visits, total = await self.history_repo.list_visits(user_id=user_id, limit=page_size, offset=offset)
        total_pages = max(1, ceil(total / page_size)) if total else 1
        return visits, total_pages

    async def search_places(self, city_id: int, query: str, limit: int = 30) -> list[Place]:
        return await self.place_repo.search(city_id=city_id, query_text=query, limit=limit)

    async def places_by_ids(self, place_ids: list[int]) -> list[Place]:
        return await self.place_repo.list_by_ids(place_ids)

    async def rate_place(self, user_id: int, place_id: int, rating: int, text: str | None) -> None:
        await self.review_repo.upsert_review(user_id=user_id, place_id=place_id, rating=rating, text=text)
        await self.history_repo.add_visit(
            user_id=user_id,
            place_id=place_id,
            rating=rating,
            comment=text,
            is_confirmed=True,
        )

    async def user_counters(self, user_id: int) -> dict[str, int]:
        return {
            "favorites": await self.favorites_repo.count(user_id=user_id),
            "history": await self.history_repo.count(user_id=user_id),
            "reviews": await self.review_repo.count(user_id=user_id),
        }

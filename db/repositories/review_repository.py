from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Place, PlaceReview
from db.repositories.base_repository import BaseRepository


class ReviewRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def upsert_review(self, user_id: int, place_id: int, rating: int, text: str | None) -> PlaceReview:
        query = select(PlaceReview).where(
            PlaceReview.user_id == user_id,
            PlaceReview.place_id == place_id,
        )
        review = (await self.session.execute(query)).scalar_one_or_none()
        if review is None:
            review = PlaceReview(user_id=user_id, place_id=place_id, rating=rating, text=text)
            self.session.add(review)
        else:
            review.rating = rating
            review.text = text
        await self.session.flush()
        await self._refresh_place_rating(place_id)
        return review

    async def count(self, user_id: int) -> int:
        query = select(func.count(PlaceReview.id)).where(PlaceReview.user_id == user_id)
        return int((await self.session.execute(query)).scalar_one())

    async def _refresh_place_rating(self, place_id: int) -> None:
        query = select(func.avg(PlaceReview.rating), func.count(PlaceReview.id)).where(
            PlaceReview.place_id == place_id,
            PlaceReview.is_visible.is_(True),
        )
        avg_rating, count_reviews = (await self.session.execute(query)).one()

        place = (await self.session.execute(select(Place).where(Place.id == place_id))).scalar_one_or_none()
        if place is None:
            return

        place.rating = float(avg_rating) if avg_rating is not None else None
        place.review_count = int(count_reviews)
        await self.session.flush()

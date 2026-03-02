from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Place, VisitHistory
from db.repositories.base_repository import BaseRepository


class HistoryRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add_visit(
        self,
        user_id: int,
        place_id: int,
        rating: int | None = None,
        comment: str | None = None,
        is_confirmed: bool = True,
    ) -> VisitHistory:
        visit = VisitHistory(
            user_id=user_id,
            place_id=place_id,
            visited_at=datetime.now(UTC),
            rating=rating,
            comment=comment,
            is_confirmed=is_confirmed,
        )
        self.session.add(visit)
        await self.session.flush()
        return visit

    async def list_visits(
        self,
        user_id: int,
        limit: int,
        offset: int,
    ) -> tuple[list[VisitHistory], int]:
        total_query = select(func.count(VisitHistory.id)).where(VisitHistory.user_id == user_id)
        total = (await self.session.execute(total_query)).scalar_one()

        query = (
            select(VisitHistory)
            .options(selectinload(VisitHistory.place).selectinload(Place.category), selectinload(VisitHistory.place).selectinload(Place.city))
            .where(VisitHistory.user_id == user_id)
            .order_by(desc(VisitHistory.visited_at), desc(VisitHistory.id))
            .limit(limit)
            .offset(offset)
        )
        visits = list((await self.session.execute(query)).scalars().all())
        return visits, int(total)

    async def count(self, user_id: int) -> int:
        query = select(func.count(VisitHistory.id)).where(VisitHistory.user_id == user_id)
        return int((await self.session.execute(query)).scalar_one())

from __future__ import annotations

import json

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ai.llm_router import LLMRouter
from ai.prompts.recommendations import recommendation_prompt
from db.models import AIRecommendation, Place, User, UserFavorite, VisitHistory


class RecommendationEngine:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.router = LLMRouter()

    async def recommend_for_user(self, user_id: int, top_k: int = 5) -> list[AIRecommendation]:
        user = await self._user(user_id)
        if user is None:
            return []

        history = await self._history_names(user_id)
        favorites = await self._favorite_names(user_id)
        available_places = await self._available_places(user.preferred_city_id)

        prompt = recommendation_prompt(
            history=history,
            favorites=favorites,
            ratings=[],
            city=user.preferred_city.name if user.preferred_city else "Неизвестный город",
            available_places=available_places,
        )
        response = await self.router.route("recommendations", prompt, temperature=0.1)

        recommendations = self._parse_response(response, available_places)[:top_k]

        await self.session.execute(delete(AIRecommendation).where(AIRecommendation.user_id == user_id))

        rows: list[AIRecommendation] = []
        for rec in recommendations:
            row = AIRecommendation(
                user_id=user_id,
                place_id=rec["place_id"],
                score=rec["score"],
                reason=rec["reason_ru"],
            )
            self.session.add(row)
            rows.append(row)

        await self.session.commit()
        return rows

    async def _user(self, user_id: int) -> User | None:
        query = (
            select(User)
            .options(selectinload(User.preferred_city))
            .where(User.id == user_id, User.is_active.is_(True))
        )
        return (await self.session.execute(query)).scalar_one_or_none()

    async def _history_names(self, user_id: int) -> list[str]:
        query = (
            select(Place.name)
            .join(VisitHistory, VisitHistory.place_id == Place.id)
            .where(VisitHistory.user_id == user_id)
            .order_by(VisitHistory.visited_at.desc())
            .limit(20)
        )
        return [name for name in (await self.session.execute(query)).scalars().all() if name]

    async def _favorite_names(self, user_id: int) -> list[str]:
        query = (
            select(Place.name)
            .join(UserFavorite, UserFavorite.place_id == Place.id)
            .where(UserFavorite.user_id == user_id)
            .limit(20)
        )
        return [name for name in (await self.session.execute(query)).scalars().all() if name]

    async def _available_places(self, city_id: int | None) -> list[Place]:
        if city_id is None:
            return []
        query = (
            select(Place)
            .where(Place.city_id == city_id, Place.is_active.is_(True))
            .order_by(Place.rating.desc().nullslast(), Place.review_count.desc(), Place.id.asc())
            .limit(100)
        )
        return list((await self.session.execute(query)).scalars().all())

    def _parse_response(self, response: str, available_places: list[Place]) -> list[dict]:
        allowed_ids = {place.id for place in available_places}
        try:
            payload = json.loads(response)
            if not isinstance(payload, list):
                raise ValueError
        except Exception:
            payload = [
                {"place_id": place.id, "score": 0.5, "reason_ru": "Подобрано по базовому ранжированию"}
                for place in available_places[:5]
            ]

        parsed: list[dict] = []
        for item in payload:
            place_id = int(item.get("place_id", 0))
            if place_id not in allowed_ids:
                continue
            parsed.append(
                {
                    "place_id": place_id,
                    "score": float(item.get("score", 0.0)),
                    "reason_ru": str(item.get("reason_ru", "Рекомендовано"))[:500],
                }
            )
        return parsed

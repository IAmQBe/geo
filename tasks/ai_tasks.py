from __future__ import annotations

import asyncio
import logging

from sqlalchemy import func, select

from ai.description_generator import DescriptionGenerator
from ai.recommendation_engine import RecommendationEngine
from db.models import Place, User
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.ai_tasks.generate_missing_descriptions")
def generate_missing_descriptions(batch_size: int = 50) -> dict:
    from db.base import async_session_factory

    async def _run() -> dict:
        async with async_session_factory() as session:
            generator = DescriptionGenerator(session)
            query = (
                select(Place)
                .where(Place.is_active.is_(True), Place.ai_description.is_(None))
                .order_by(Place.id.asc())
                .limit(batch_size)
            )
            places = list((await session.execute(query)).scalars().all())

            updated = 0
            for place in places:
                text = await generator.generate_for_place(place)
                if text:
                    place.ai_description = text
                    updated += 1

            await session.commit()
            return {"scanned": len(places), "updated": updated}

    payload = asyncio.run(_run())
    logger.info("Generated descriptions", extra=payload)
    return payload


@celery_app.task(name="tasks.ai_tasks.refresh_user_recommendations")
def refresh_user_recommendations(user_id: int, top_k: int = 5) -> dict:
    from db.base import async_session_factory

    async def _run() -> dict:
        async with async_session_factory() as session:
            engine = RecommendationEngine(session)
            recommendations = await engine.recommend_for_user(user_id=user_id, top_k=top_k)
            return {"user_id": user_id, "count": len(recommendations)}

    payload = asyncio.run(_run())
    logger.info("Refreshed recommendations", extra=payload)
    return payload


@celery_app.task(name="tasks.ai_tasks.generate_weekly_trends")
def generate_weekly_trends() -> dict:
    from db.base import async_session_factory

    async def _run() -> dict:
        async with async_session_factory() as session:
            users_count = int((await session.execute(select(func.count(User.id)))).scalar_one())
            return {"status": "ok", "users_analyzed": users_count}

    payload = asyncio.run(_run())
    logger.info("Weekly trends generated", extra=payload)
    return payload

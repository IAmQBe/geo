from __future__ import annotations

import asyncio
import logging

from bot.metrics import PARSER_PLACES_PROCESSED_TOTAL
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.parse_tasks.run_parse_job", bind=True, max_retries=2)
def run_parse_job(self, source: str, city_slug: str, category_slug: str, limit: int = 30) -> dict:
    from db.base import async_session_factory
    from parser.runner import ParseRunner

    async def _run() -> dict:
        async with async_session_factory() as session:
            runner = ParseRunner(session)
            result = await runner.run(source=source, city_slug=city_slug, category_slug=category_slug, limit=limit)
            return {
                "source": source,
                "city_slug": city_slug,
                "category_slug": category_slug,
                "found": result.found,
                "added": result.added,
                "updated": result.updated,
            }

    try:
        payload = asyncio.run(_run())
        PARSER_PLACES_PROCESSED_TOTAL.inc(payload["found"])
        logger.info("Parse job completed", extra=payload)
        return payload
    except Exception as exc:
        logger.exception("Parse job failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)

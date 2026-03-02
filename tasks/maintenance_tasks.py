from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from db.models import User
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.maintenance_tasks.cleanup_inactive_users")
def cleanup_inactive_users(days: int = 180) -> dict:
    from db.base import async_session_factory

    async def _run() -> dict:
        threshold = datetime.now(UTC) - timedelta(days=days)
        async with async_session_factory() as session:
            query = select(User).where(User.last_active_at.is_not(None), User.last_active_at < threshold)
            users = list((await session.execute(query)).scalars().all())
            for user in users:
                user.is_active = False
            await session.commit()
            return {"deactivated": len(users)}

    payload = asyncio.run(_run())
    logger.info("Maintenance completed", extra=payload)
    return payload

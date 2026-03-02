from __future__ import annotations

import asyncio

import redis.asyncio as redis
from sqlalchemy import text

from bot.config import get_settings
from db.base import async_session_factory
from storage.minio_client import MinioClient


async def check_db() -> bool:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_redis() -> bool:
    settings = get_settings()
    try:
        client = redis.from_url(settings.redis_url)
        await client.ping()
        await client.close()
        return True
    except Exception:
        return False


async def check_minio() -> bool:
    try:
        client = MinioClient()
        await client.ensure_bucket()
        return True
    except Exception:
        return False


async def main() -> None:
    db_ok, redis_ok, minio_ok = await asyncio.gather(check_db(), check_redis(), check_minio())
    status = {
        "database": db_ok,
        "redis": redis_ok,
        "minio": minio_ok,
        "ok": all([db_ok, redis_ok, minio_ok]),
    }
    print(status)


if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import async_session_factory

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.auth import require_admin
from admin.dependencies import TEMPLATES, get_db_session
from db.models import City

router = APIRouter(prefix="/admin/cities", tags=["admin-cities"])


@router.get("/")
async def list_cities(
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    cities = list((await session.execute(select(City).order_by(City.name.asc()))).scalars().all())
    return TEMPLATES.TemplateResponse("cities.html", {"request": request, "cities": cities})

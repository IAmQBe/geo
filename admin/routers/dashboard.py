from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.auth import require_admin
from admin.dependencies import TEMPLATES, get_db_session
from db.models import ParseJob, Place, User

router = APIRouter(prefix="/admin", tags=["admin-dashboard"])


@router.get("/")
async def dashboard(
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    places_count = int((await session.execute(select(func.count(Place.id)))).scalar_one())
    users_count = int((await session.execute(select(func.count(User.id)))).scalar_one())
    failed_jobs = int(
        (await session.execute(select(func.count(ParseJob.id)).where(ParseJob.status == "failed"))).scalar_one()
    )

    return TEMPLATES.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "places_count": places_count,
            "users_count": users_count,
            "failed_jobs": failed_jobs,
        },
    )

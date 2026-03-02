from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin.auth import require_admin
from admin.dependencies import TEMPLATES, get_db_session
from db.models import PlaceReview

router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"])


@router.get("/")
async def list_reviews(
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    reviews = list(
        (
            await session.execute(
                select(PlaceReview)
                .options(selectinload(PlaceReview.user), selectinload(PlaceReview.place))
                .order_by(PlaceReview.created_at.desc())
                .limit(300)
            )
        )
        .scalars()
        .all()
    )
    return TEMPLATES.TemplateResponse("reviews.html", {"request": request, "reviews": reviews})

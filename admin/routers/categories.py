from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.auth import require_admin
from admin.dependencies import TEMPLATES, get_db_session
from db.models import Category

router = APIRouter(prefix="/admin/categories", tags=["admin-categories"])


@router.get("/")
async def list_categories(
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    categories = list((await session.execute(select(Category).order_by(Category.sort_order.asc()))).scalars().all())
    return TEMPLATES.TemplateResponse(
        "categories.html",
        {"request": request, "categories": categories},
    )

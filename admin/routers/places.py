from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin.auth import require_admin
from admin.dependencies import TEMPLATES, get_db_session
from db.models import Place

router = APIRouter(prefix="/admin/places", tags=["admin-places"])


@router.get("/")
async def places_list(
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    query = (
        select(Place)
        .options(selectinload(Place.city), selectinload(Place.category))
        .order_by(Place.id.desc())
        .limit(200)
    )
    places = list((await session.execute(query)).scalars().all())
    return TEMPLATES.TemplateResponse("places/list.html", {"request": request, "places": places})


@router.get("/{place_id}")
async def place_detail(
    place_id: int,
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    query = (
        select(Place)
        .options(
            selectinload(Place.city),
            selectinload(Place.category),
            selectinload(Place.photos),
            selectinload(Place.reviews),
        )
        .where(Place.id == place_id)
    )
    place = (await session.execute(query)).scalar_one_or_none()
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found")

    return TEMPLATES.TemplateResponse("places/detail.html", {"request": request, "place": place})

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin.auth import require_admin
from admin.dependencies import TEMPLATES, get_db_session
from db.models import User

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("/")
async def users_list(
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    users = list(
        (
            await session.execute(
                select(User).options(selectinload(User.preferred_city)).order_by(User.id.desc()).limit(300)
            )
        )
        .scalars()
        .all()
    )
    return TEMPLATES.TemplateResponse("users/list.html", {"request": request, "users": users})


@router.get("/{user_id}")
async def user_detail(
    user_id: int,
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    user = (
        await session.execute(
            select(User)
            .options(
                selectinload(User.preferred_city),
                selectinload(User.favorites),
                selectinload(User.visits),
            )
            .where(User.id == user_id)
        )
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return TEMPLATES.TemplateResponse("users/detail.html", {"request": request, "user": user})

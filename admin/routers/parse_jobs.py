from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.auth import require_admin
from admin.dependencies import TEMPLATES, get_db_session
from db.models import ParseJob
from tasks.parse_tasks import run_parse_job

router = APIRouter(prefix="/admin/parse-jobs", tags=["admin-parse-jobs"])


@router.get("/")
async def list_parse_jobs(
    request: Request,
    _: str = Depends(require_admin),
    session: AsyncSession = Depends(get_db_session),
):
    jobs = list((await session.execute(select(ParseJob).order_by(ParseJob.id.desc()).limit(200))).scalars().all())
    return TEMPLATES.TemplateResponse("parse_jobs.html", {"request": request, "jobs": jobs})


@router.post("/run")
async def run_manual_parse(
    source: str = Form(...),
    city_slug: str = Form(...),
    category_slug: str = Form(...),
    limit: int = Form(30),
    _: str = Depends(require_admin),
) -> dict:
    task = run_parse_job.delay(source, city_slug, category_slug, limit)
    return {"task_id": task.id, "status": "queued"}

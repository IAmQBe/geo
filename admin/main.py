from __future__ import annotations

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from admin.auth import create_admin_token, require_admin, verify_password
from admin.dependencies import TEMPLATES
from admin.routers import (
    categories_router,
    cities_router,
    dashboard_router,
    parse_jobs_router,
    places_router,
    reviews_router,
    users_router,
)
from bot.config import get_settings

app = FastAPI(title="Jam Bot Admin")

app.include_router(dashboard_router)
app.include_router(places_router)
app.include_router(users_router)
app.include_router(parse_jobs_router)
app.include_router(categories_router)
app.include_router(cities_router)
app.include_router(reviews_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse("login.html", {"request": request})


@app.post("/admin/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    settings = get_settings()
    if username != settings.admin_username or not verify_password(password, settings.admin_password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_admin_token(username)
    response = RedirectResponse(url="/admin/", status_code=302)
    response.set_cookie("admin_token", token, httponly=True, samesite="lax", max_age=12 * 3600)
    return response


@app.post("/admin/logout")
async def logout(_: str = Depends(require_admin)):
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response

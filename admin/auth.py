from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from bot.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        # Development fallback only.
        return password == "admin"
    return pwd_context.verify(password, password_hash)


def create_admin_token(username: str) -> str:
    settings = get_settings()
    payload = {
        "sub": username,
        "role": "admin",
        "exp": datetime.now(UTC) + timedelta(hours=12),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.admin_secret_key, algorithm="HS256")


def decode_admin_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.admin_secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


async def require_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    token = None
    if credentials is not None:
        token = credentials.credentials
    if token is None:
        token = request.cookies.get("admin_token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    payload = decode_admin_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return str(payload.get("sub"))

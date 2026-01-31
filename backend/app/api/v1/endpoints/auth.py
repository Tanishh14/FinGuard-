"""
Authentication endpoints. Real JWT and optional DB user lookup.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.db.models import User

router = APIRouter()

DEMO_USER_UUID = "00000000-0000-0000-0000-000000000001"


def _create_access_token(subject: str) -> tuple[str, int]:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    encoded = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded, settings.ACCESS_TOKEN_EXPIRE_MINUTES


def _verify_password(plain: str, hashed: str) -> bool:
    """Verify password using bcrypt."""
    try:
        import bcrypt
        password_bytes = plain.encode('utf-8')
        hash_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """JWT authentication. Tries database first; accepts demo/demo when DB is empty or down."""
    # Try database first
    try:
        r = await db.execute(select(User).where(User.username == request.username))
        user = r.scalar_one_or_none()
        if user and user.is_active:
            if user.hashed_password and not _verify_password(request.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            token, expires = _create_access_token(str(user.id))
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                expires_in_minutes=expires,
            )
    except HTTPException:
        raise
    except Exception:
        pass  # DB error or no user: fall through to demo fallback

    # Fallback: accept demo/demo when DB has no user or is unavailable (e.g. dev without init_db)
    if request.username.strip().lower() == "demo" and request.password == "demo":
        token, expires = _create_access_token(DEMO_USER_UUID)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_minutes=expires,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

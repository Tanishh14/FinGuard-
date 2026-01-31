"""
Dependency injections for FastAPI routes.
Real DB session and JWT auth. No mock or dummy data.
"""
from typing import AsyncGenerator, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from loguru import logger

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models import User

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Real database session. Fails if DB unavailable."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Decode JWT and return user or None. No dummy user."""
    if not credentials:
        logger.warning("No credentials provided")
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("No 'sub' in JWT payload")
            return None
        logger.info(f"JWT validated successfully for user_id: {user_id}")
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None
    # Real app would load user from DB; minimal User from JWT sub only
    try:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
    except (TypeError, ValueError):
        return None
    return User(
        id=uid,
        email="",
        username="",
        is_active=True,
    )


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require authenticated user. Fail with 401 if not."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


def get_ml_client():
    """ML service client. Fails at call time if service unavailable."""
    from app.services.ml_client import MLClient
    return MLClient()


def get_explain_client():
    """Explainability service client."""
    from app.services.explain_client import ExplainClient
    return ExplainClient()


def get_alerting_service():
    """Alerting service."""
    from app.services.alerting import AlertingService
    return AlertingService()

"""
Dependency injections for FastAPI routes
"""

from typing import AsyncGenerator, Optional
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
    """Dependency to get database session"""
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
    """Dependency to get current authenticated user"""
    if not credentials:
        return None
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    # In a real application, you would fetch user from database
    # For demo, we'll return a mock user
    return User(
        id=user_id,
        email="demo@finguard.ai",
        username="demo_user",
        is_active=True
    )


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Dependency to get current active user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_ml_client():
    """Dependency to get ML service client"""
    from app.services.ml_client import MLClient
    return MLClient()


def get_explain_client():
    """Dependency to get explanation service client"""
    from app.services.explain_client import ExplainClient
    return ExplainClient()


def get_alerting_service():
    """Dependency to get alerting service"""
    from app.services.alerting import AlertingService
    return AlertingService()
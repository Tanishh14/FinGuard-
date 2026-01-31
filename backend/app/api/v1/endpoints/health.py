"""
Health check endpoints. Real component checks; fail or report actual status.
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/", tags=["Health"])
def health_check():
    """GET /api/v1/health - required for load balancers."""
    return {"status": "ok", "service": "FinGuard AI"}


@router.get("/detailed", tags=["Health"])
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health from real DB and service checks. Components report healthy/unhealthy."""
    components = {}
    status_val = "healthy"
    try:
        await db.execute(text("SELECT 1"))
        components["database"] = {"status": "healthy"}
    except Exception as e:
        components["database"] = {"status": "unhealthy", "error": str(e)}
        status_val = "degraded"
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        components["redis"] = {"status": "healthy"}
    except Exception as e:
        components["redis"] = {"status": "unhealthy", "error": str(e)}
        status_val = "degraded"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ML_SERVICE_URL}/health")
            components["ml_service"] = {"status": "healthy" if r.status_code == 200 else "unhealthy"}
    except Exception as e:
        components["ml_service"] = {"status": "unhealthy", "error": str(e)}
        status_val = "degraded"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.EXPLAIN_SERVICE_URL}/health")
            components["explain_service"] = {"status": "healthy" if r.status_code == 200 else "unhealthy"}
    except Exception as e:
        components["explain_service"] = {"status": "unhealthy", "error": str(e)}
        status_val = "degraded"
    return {
        "status": status_val,
        "timestamp": datetime.now().isoformat(),
        "components": components,
    }


@router.get("/metrics", tags=["Health"])
def get_metrics():
    """Metrics: real pipeline required; fail if not implemented."""
    from fastapi import HTTPException
    raise HTTPException(status_code=501, detail="Metrics pipeline not implemented")


@router.get("/status", tags=["Health"])
def service_status():
    """Service status from config only."""
    return {
        "service": "FinGuard AI Backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database_configured": bool(settings.DATABASE_URL),
    }

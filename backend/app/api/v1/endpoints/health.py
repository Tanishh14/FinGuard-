"""
Health check and monitoring endpoints
"""

import time
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis
from loguru import logger

from app.core.dependencies import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "FinGuard AI",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
):
    """Detailed health check with dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        start_time = time.time()
        await db.execute(text("SELECT 1"))
        db_latency = time.time() - start_time
        
        health_status["components"]["database"] = {
            "status": "healthy",
            "latency_ms": round(db_latency * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        start_time = time.time()
        redis_client.ping()
        redis_latency = time.time() - start_time
        
        health_status["components"]["redis"] = {
            "status": "healthy",
            "latency_ms": round(redis_latency * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check ML service
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = time.time()
            response = await client.get(f"{settings.ML_SERVICE_URL}/health")
            ml_latency = time.time() - start_time
            
            health_status["components"]["ml_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "latency_ms": round(ml_latency * 1000, 2),
                "response_code": response.status_code
            }
    except Exception as e:
        logger.error(f"ML service health check failed: {e}")
        health_status["components"]["ml_service"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check explanation service
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = time.time()
            response = await client.get(f"{settings.EXPLAIN_SERVICE_URL}/health")
            explain_latency = time.time() - start_time
            
            health_status["components"]["explain_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "latency_ms": round(explain_latency * 1000, 2),
                "response_code": response.status_code
            }
    except Exception as e:
        logger.error(f"Explanation service health check failed: {e}")
        health_status["components"]["explain_service"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/metrics")
async def get_metrics():
    """Get system metrics (for Prometheus integration)"""
    # In a real implementation, you would collect metrics from
    # Prometheus client or your monitoring system
    return {
        "requests_total": 1000,  # Example metrics
        "average_response_time_ms": 45.2,
        "error_rate_percent": 0.5,
        "active_connections": 25,
        "transactions_processed": 50000,
        "fraud_detected": 250,
        "false_positives": 15
    }


@router.get("/status")
async def service_status():
    """Get service status with configuration"""
    return {
        "service": "FinGuard AI Backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "database_configured": bool(settings.DATABASE_URL),
        "redis_configured": bool(settings.REDIS_URL),
        "ml_service_url": settings.ML_SERVICE_URL,
        "explain_service_url": settings.EXPLAIN_SERVICE_URL,
        "cors_origins": settings.BACKEND_CORS_ORIGINS,
        "rate_limit": f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}s"
    }
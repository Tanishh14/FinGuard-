"""
FinGuard AI - Backend Main Application
FastAPI application with ML-powered fraud detection.
Entry point: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import text

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.models import Base
from app.utils.logging import setup_logging, log_request

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan: verify DB, create tables if missing, then initialize patterns."""
    logger.info("Starting FinGuard AI Backend")
    logger.info("Environment: %s", settings.ENVIRONMENT)

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connectivity verified")
    except Exception as e:
        logger.warning("Database not reachable at startup: %s", e)
        yield
        await engine.dispose()
        return

    # Create tables if they don't exist (e.g. first run or fresh DB)
    tables_created = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1 FROM transactions LIMIT 0"))
        logger.info("Tables already exist")
    except Exception as e:
        err_msg = str(e).lower()
        if "does not exist" in err_msg or "undefinedtable" in err_msg or "relation" in err_msg:
            try:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                tables_created = True
                logger.info("Created missing database tables (transactions, users, merchants, etc.)")
            except Exception as create_err:
                logger.warning("Could not create tables: %s", create_err)
        else:
            logger.warning("Table check failed: %s", e)

    # If we just created tables, ensure demo user exists so login works
    if tables_created:
        try:
            from init_db import create_demo_user
            await create_demo_user()
            logger.info("Demo user ensured (username: demo, password: demo)")
        except Exception as e:
            logger.warning("Could not create demo user: %s (run python init_db.py if needed)", e)

    # Optional: initialize fraud patterns (non-destructive)
    try:
        from app.services.ingestion import initialize_fraud_patterns
        await initialize_fraud_patterns()
        logger.info("Fraud patterns initialized")
    except Exception as e:
        logger.warning("Could not initialize fraud patterns: %s", e)

    yield

    logger.info("Shutting down FinGuard AI Backend")
    await engine.dispose()


app = FastAPI(
    title="FinGuard AI API",
    description="AI-Powered Fraud Detection & Risk Management System",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Development CORS: allow all origins, headers, methods
_allow_origins = ["*"] if settings.ENVIRONMENT == "development" else list(settings.BACKEND_CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    await log_request(request, response, time.time() - start_time)
    return response


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error("Unhandled exception: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check for load balancers and monitoring.
    Returns status and database state and ML/explain service state.
    Does not crash if external services are unreachable.
    """
    db_status = "down"
    ml_status = "unknown"
    explain_status = "unknown"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:
        pass

    # Check ML and explain services (best-effort, short timeout)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=1.0) as client:
            try:
                r = await client.get(f"{settings.ML_SERVICE_URL}/health")
                ml_status = "up" if r.status_code == 200 else "down"
            except Exception:
                ml_status = "down"
            try:
                r = await client.get(f"{settings.EXPLAIN_SERVICE_URL}/health")
                explain_status = "up" if r.status_code == 200 else "down"
            except Exception:
                explain_status = "down"
    except Exception:
        ml_status = "unknown"
        explain_status = "unknown"

    return {
        "status": "ok",
        "database": db_status,
        "ml_service": ml_status,
        "explain_service": explain_status,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to FinGuard AI API",
        "documentation": "/docs" if settings.ENVIRONMENT != "production" else "Hidden in production",
        "version": "1.0.0",
        "status": "operational",
    }

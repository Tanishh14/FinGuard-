"""
Main API router combining all endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import transactions, explain, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["Transactions"]
)

api_router.include_router(
    explain.router,
    prefix="/explain",
    tags=["Explainability"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)
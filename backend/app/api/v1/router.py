"""
Main API router combining all endpoints.
Backend is the single source of truth and API gateway.
All routes under /api/v1 when mounted in main.py.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, transactions, explain, health, predict, gnn, anomaly, dashboard, stream

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(predict.router, prefix="/predict", tags=["Predict"])
api_router.include_router(explain.router, prefix="/explain", tags=["Explainability"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(gnn.router, prefix="/gnn", tags=["GNN"])
api_router.include_router(anomaly.router, prefix="/anomaly", tags=["Anomaly"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(stream.router, prefix="", tags=["RealTime"])
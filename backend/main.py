"""
FinGuard AI - Backend entry point.
Use: uvicorn main:app --reload --host 0.0.0.0 --port 8000
This runs the full app (app.main) with DB, lifespan, and auto table creation.
"""
from app.main import app

__all__ = ["app"]

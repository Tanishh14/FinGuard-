"""
Dashboard metrics - real aggregates from DB only.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.dependencies import get_db, get_current_active_user
from app.db.models import Transaction as TransactionModel

router = APIRouter()


@router.get(
    "/metrics",
    response_model=dict,
)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    GET /api/v1/dashboard/metrics
    Real aggregates from DB only. Returns 404 if no data.
    """
    uid = current_user.id
    r = await db.execute(select(func.count(TransactionModel.id)).where(TransactionModel.user_id == uid))
    total = r.scalar() or 0

    if total == 0:
        return {
            "total_transactions": 0,
            "flagged_transactions": 0,
            "high_risk_percentage": 0.0,
        }

    r = await db.execute(
        select(func.count(TransactionModel.id)).where(
            TransactionModel.user_id == uid,
            TransactionModel.is_fraudulent == True,
        )
    )
    flagged = r.scalar() or 0
    
    r = await db.execute(
        select(func.count(TransactionModel.id)).where(
            TransactionModel.user_id == uid,
            TransactionModel.risk_level.in_(["high", "critical"]),
        )
    )
    high_risk_count = r.scalar() or 0
    high_risk_percentage = (high_risk_count / total * 100) if total else 0.0
    
    return {
        "total_transactions": total,
        "flagged_transactions": flagged,
        "high_risk_percentage": round(high_risk_percentage, 2),
    }

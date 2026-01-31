"""
Anomaly detection - real scores from DB only.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.dependencies import get_db, get_current_active_user
from app.db.models import Transaction as TransactionModel

router = APIRouter()


@router.get(
    "/summary",
    response_model=dict,
)
async def get_anomaly_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    GET /api/v1/anomaly/summary
    Real anomaly/risk scores from DB only. Returns 404 if no data.
    """
    q = (
        select(
            TransactionModel.transaction_id,
            TransactionModel.user_id,
            TransactionModel.anomaly_score,
            TransactionModel.risk_score,
            TransactionModel.risk_level,
            TransactionModel.merchant_id,
        )
        .where(TransactionModel.user_id == current_user.id)
        .order_by(TransactionModel.processed_at.desc().nullslast(), TransactionModel.created_at.desc().nullslast())
        .limit(100)
    )
    r = await db.execute(q)
    rows = r.all()

    if not rows:
        return {
            "chart_data": [],
            "scores": [],
            "alert": {"message": "No anomaly data yet. Submit transactions to see scores."},
        }

    chart_data = []
    scores_data = []
    for t in rows:
        score = (t.anomaly_score or 0) * 100 if t.anomaly_score is not None else (t.risk_score or 0)
        chart_data.append({
            "user": f"{str(t.user_id)[:8]}..." if t.user_id else "N/A",
            "score": round(score, 1),
        })
        risk_status = "High Risk" if (t.risk_level or "").lower() in ("high", "critical") else "Medium Risk" if (t.risk_level or "").lower() == "medium" else "Low Risk"
        scores_data.append({
            "user": f"{str(t.user_id)[:8]}... ({t.merchant_id or 'N/A'})",
            "score": round(score, 1),
            "pattern": t.risk_level or "Normal",
            "status": risk_status,
        })
    return {
        "chart_data": chart_data,
        "scores": scores_data,
        "alert": {
            "message": f"Anomaly detection: {len(rows)} transactions with risk scores from database.",
        },
    }

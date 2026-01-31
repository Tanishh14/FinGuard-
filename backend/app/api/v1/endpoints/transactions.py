"""
Transaction API endpoints - NO MOCK DATA.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, and_, select, cast, Date, Integer
from loguru import logger

from app.core.dependencies import get_db, get_current_active_user, get_ml_client, get_alerting_service
from app.schemas.transaction import (
    TransactionCreate, TransactionResponse, TransactionListResponse,
    FraudAlertResponse, TransactionStats, FraudTrend,
)
from app.services.scoring_orchestrator import ScoringOrchestrator
from app.db.models import Transaction as TransactionModel, Alert, Explanation, User

router = APIRouter()


def _recommended_action(risk_level: str) -> str:
    return {"low": "Proceed normally", "medium": "Review", "high": "Verify", "critical": "Block"}.get(risk_level, "Review")


@router.post("/analyze", response_model=TransactionResponse)
async def analyze_transaction(
    transaction: TransactionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    ml_client=Depends(get_ml_client),
    current_user=Depends(get_current_active_user),
):
    """Analyze transaction via ML and DB. Fails with 503/500 if ML or DB unavailable."""
    try:
        orchestrator = ScoringOrchestrator(db, ml_client)
        result = await orchestrator.process_transaction(
            transaction_data=transaction.dict(),
            user_id=str(current_user.id),
        )
    except Exception as e:
        logger.error(f"Transaction analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Analysis failed: {str(e)}",
        )
    # Persist to DB
    try:
        db_txn = TransactionModel(
            transaction_id=result["transaction_id"],
            user_id=current_user.id,
            merchant_id=transaction.merchant_id,
            device_id=transaction.device_id,
            amount=transaction.amount,
            currency=transaction.currency or "USD",
            transaction_time=datetime.now(),
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            is_fraudulent=result["is_fraudulent"],
            confidence_score=result.get("confidence_score", 0.0),
            features=result.get("features"),
            anomaly_score=result.get("anomaly_score"),
            graph_risk_score=result.get("graph_risk_score"),
            processed_at=datetime.now(),
        )
        db.add(db_txn)
        await db.flush()
        if result.get("explanation"):
            expl = result["explanation"]
            db.add(
                Explanation(
                    transaction_id=db_txn.id,
                    summary=expl.get("summary", ""),
                    reasons=expl.get("reasons", []),
                    suggested_actions=expl.get("suggested_actions", []),
                    confidence=expl.get("confidence", 0.0),
                    model_used=expl.get("model_used", ""),
                )
            )
        if result["risk_level"] in ("high", "critical"):
            db.add(
                Alert(
                    transaction_id=db_txn.id,
                    alert_type="fraud_risk",
                    severity=result["risk_level"],
                    message=f"High risk: {result['risk_score']:.1f}",
                    status="pending",
                )
            )
        await db.commit()
    except Exception as e:
        logger.error(f"DB write failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to store result")
    return TransactionResponse(
        transaction_id=result["transaction_id"],
        amount=transaction.amount,
        currency=transaction.currency or "USD",
        merchant_id=transaction.merchant_id,
        device_id=transaction.device_id,
        transaction_time=datetime.now().isoformat(),
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        is_fraudulent=result["is_fraudulent"],
        confidence_score=result.get("confidence_score", 0.0),
        explanation=result.get("explanation"),
        timestamp=datetime.now().isoformat(),
        recommended_action=_recommended_action(result["risk_level"]),
    )


@router.get("/stats/dashboard", response_model=TransactionStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Dashboard stats from DB only. Returns 404 if no data."""
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    week_ago = today - timedelta(days=7)
    uid = current_user.id
    
    r = await db.execute(select(func.count(TransactionModel.id)).where(TransactionModel.user_id == uid))
    total = r.scalar() or 0

    if total == 0:
        return TransactionStats(
            total_transactions=0,
            today_transactions=0,
            fraudulent_transactions=0,
            high_risk_transactions=0,
            total_amount=0.0,
            fraud_amount=0.0,
            avg_risk_score=0.0,
            risk_score_distribution={},
        )

    r = await db.execute(
        select(func.count(TransactionModel.id)).where(
            and_(TransactionModel.user_id == uid, TransactionModel.transaction_time >= today_start, TransactionModel.transaction_time <= today_end)
        )
    )
    today_count = r.scalar() or 0
    
    r = await db.execute(
        select(func.count(TransactionModel.id)).where(and_(TransactionModel.user_id == uid, TransactionModel.is_fraudulent == True))
    )
    fraud_count = r.scalar() or 0
    
    r = await db.execute(
        select(func.count(TransactionModel.id)).where(
            and_(TransactionModel.user_id == uid, TransactionModel.risk_level.in_(["high", "critical"]))
        )
    )
    high_risk = r.scalar() or 0
    
    r = await db.execute(select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(TransactionModel.user_id == uid))
    total_amt = float(r.scalar() or 0)
    
    r = await db.execute(
        select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(TransactionModel.user_id == uid, TransactionModel.is_fraudulent == True)
        )
    )
    fraud_amt = float(r.scalar() or 0)
    
    r = await db.execute(select(func.coalesce(func.avg(TransactionModel.risk_score), 0)).where(TransactionModel.user_id == uid))
    avg_risk = float(r.scalar() or 0)
    
    r = await db.execute(
        select(TransactionModel.risk_level, func.count(TransactionModel.id)).where(
            and_(TransactionModel.user_id == uid, TransactionModel.transaction_time >= week_ago)
        ).group_by(TransactionModel.risk_level)
    )
    dist = {row[0] or "unknown": row[1] for row in r.all()}
    
    return TransactionStats(
        total_transactions=total,
        today_transactions=today_count,
        fraudulent_transactions=fraud_count,
        high_risk_transactions=high_risk,
        total_amount=total_amt,
        fraud_amount=fraud_amt,
        avg_risk_score=avg_risk,
        risk_score_distribution=dist,
    )


@router.get("/alerts/recent", response_model=List[FraudAlertResponse])
async def get_recent_alerts(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Recent alerts from DB only."""
    q = (
        select(Alert)
        .join(TransactionModel, Alert.transaction_id == TransactionModel.id)
        .where(and_(TransactionModel.user_id == current_user.id, Alert.status == "pending"))
        .order_by(desc(Alert.created_at))
        .limit(limit)
    )
    r = await db.execute(q)
    alerts = r.scalars().all()
    out = []
    for a in alerts:
        rt = await db.execute(select(TransactionModel).where(TransactionModel.id == a.transaction_id))
        t = rt.scalar_one_or_none()
        if t:
            out.append(
                FraudAlertResponse(
                    alert_id=str(a.id),
                    transaction_id=t.transaction_id,
                    amount=t.amount,
                    merchant_id=t.merchant_id,
                    risk_score=t.risk_score,
                    risk_level=t.risk_level or "low",
                    alert_type=a.alert_type,
                    severity=a.severity,
                    message=a.message,
                    created_at=a.created_at.isoformat() if a.created_at else "",
                    status=a.status,
                )
            )
    return out


@router.get("/trends/risk", response_model=List[FraudTrend])
async def get_risk_trends(
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Risk trends from DB only."""
    end = datetime.now()
    start = end - timedelta(days=days)
    q = (
        select(
            cast(TransactionModel.transaction_time, Date).label("date"),
            func.count(TransactionModel.id).label("total"),
            func.avg(TransactionModel.risk_score).label("avg_risk"),
            func.sum(func.cast(TransactionModel.is_fraudulent, Integer)).label("fraud_count"),
        )
        .where(
            and_(
                TransactionModel.user_id == current_user.id,
                TransactionModel.transaction_time >= start,
                TransactionModel.transaction_time <= end,
            )
        )
        .group_by(cast(TransactionModel.transaction_time, Date))
        .order_by(cast(TransactionModel.transaction_time, Date))
    )
    r = await db.execute(q)
    rows = r.all()
    return [
        FraudTrend(
            date=row[0].isoformat(),
            total_transactions=row[1],
            avg_risk_score=float(row[2] or 0),
            fraudulent_transactions=int(row[3] or 0),
        )
        for row in rows
    ]


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
  alert_id: str,
  resolution_notes: str = Query(...),
  is_false_positive: bool = Query(False),
  db: AsyncSession = Depends(get_db),
  current_user=Depends(get_current_active_user),
):
    """Resolve alert in DB. 404 if not found."""
    try:
        aid = UUID(alert_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    q = (
        select(Alert)
        .join(TransactionModel, Alert.transaction_id == TransactionModel.id)
        .where(and_(Alert.id == aid, TransactionModel.user_id == current_user.id))
    )
    r = await db.execute(q)
    alert = r.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alert.status = "false_positive" if is_false_positive else "resolved"
    alert.reviewed_by = getattr(current_user, "username", None) or str(current_user.id)
    alert.reviewed_at = datetime.now()
    alert.resolution_notes = resolution_notes
    await db.commit()
    return {"status": "success", "message": "Alert resolved"}


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Single transaction from DB. 404 if not found."""
    q = select(TransactionModel).where(
        and_(TransactionModel.transaction_id == transaction_id, TransactionModel.user_id == current_user.id)
    )
    r = await db.execute(q)
    t = r.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    rex = await db.execute(select(Explanation).where(Explanation.transaction_id == t.id))
    ex = rex.scalar_one_or_none()
    return TransactionResponse(
        transaction_id=t.transaction_id,
        amount=t.amount,
        currency=t.currency or "USD",
        merchant_id=t.merchant_id,
        device_id=t.device_id,
        transaction_time=t.transaction_time.isoformat(),
        risk_score=t.risk_score,
        risk_level=t.risk_level or "low",
        is_fraudulent=t.is_fraudulent,
        confidence_score=t.confidence_score or 0.0,
        explanation={"summary": ex.summary, "reasons": ex.reasons or [], "suggested_actions": ex.suggested_actions or []} if ex else None,
        timestamp=(t.created_at.isoformat() if t.created_at else datetime.now().isoformat()),
        recommended_action=_recommended_action(t.risk_level or "low"),
    )


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """List transactions from DB. Real query only."""
    q = select(TransactionModel).where(TransactionModel.user_id == current_user.id)
    cnt = await db.execute(select(func.count()).select_from(q.subquery()))
    total = cnt.scalar() or 0
    q = q.order_by(desc(TransactionModel.transaction_time)).offset(skip).limit(limit)
    r = await db.execute(q)
    rows = r.scalars().all()
    items = [
        {
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "currency": t.currency or "USD",
            "merchant_id": t.merchant_id,
            "transaction_time": t.transaction_time.isoformat(),
            "risk_score": t.risk_score,
            "risk_level": t.risk_level or "low",
            "is_fraudulent": t.is_fraudulent,
        }
        for t in rows
    ]
    return TransactionListResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit else 1,
        pages=(total // limit + 1) if limit else 0,
        has_more=skip + len(items) < total,
    )

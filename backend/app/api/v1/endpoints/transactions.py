"""
Transaction API endpoints for fraud detection and management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, and_
from loguru import logger
import asyncio

from app.core.dependencies import get_db, get_current_active_user, get_ml_client, get_alerting_service
from app.schemas.transaction import (
    TransactionCreate, TransactionResponse, TransactionListResponse,
    TransactionUpdate, TransactionAnalysisRequest, FraudAlertResponse,
    TransactionStats, RiskScoreDistribution, FraudTrend
)
from app.services.scoring_orchestrator import ScoringOrchestrator
from app.db.models import Transaction as TransactionModel, Alert, Explanation, SystemMetrics
from app.db.session import get_session

router = APIRouter()


@router.post("/analyze", response_model=TransactionResponse)
async def analyze_transaction(
    transaction: TransactionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    ml_client = Depends(get_ml_client),
    current_user = Depends(get_current_active_user)
):
    """
    Analyze a transaction for fraud risk
    
    This endpoint:
    1. Receives transaction data
    2. Extracts features
    3. Calls ML services for scoring
    4. Generates explanations
    5. Creates alerts if needed
    6. Stores everything in database
    """
    try:
        logger.info(f"Analyzing transaction for user {current_user.id}")
        
        # Initialize orchestrator
        orchestrator = ScoringOrchestrator(db, ml_client)
        
        # Process transaction
        transaction_result = await orchestrator.process_transaction(
            transaction_data=transaction.dict(),
            user_id=str(current_user.id)
        )
        
        # Store in database
        db_transaction = TransactionModel(
            transaction_id=transaction_result["transaction_id"],
            user_id=current_user.id,
            merchant_id=transaction.merchant_id,
            device_id=transaction.device_id,
            amount=transaction.amount,
            currency=transaction.currency,
            location_lat=transaction.location_lat,
            location_lng=transaction.location_lng,
            location_country=transaction.location_country,
            location_city=transaction.location_city,
            transaction_type=transaction.transaction_type,
            category=transaction.category,
            transaction_time=datetime.now(),
            
            # ML results
            risk_score=transaction_result["risk_score"],
            risk_level=transaction_result["risk_level"],
            is_fraudulent=transaction_result["is_fraudulent"],
            fraud_type=transaction_result.get("fraud_type"),
            confidence_score=transaction_result["confidence_score"],
            features=transaction_result["features"],
            anomaly_score=transaction_result["anomaly_score"],
            graph_risk_score=transaction_result["graph_risk_score"],
            processed_at=datetime.now()
        )
        
        db.add(db_transaction)
        await db.commit()
        await db.refresh(db_transaction)
        
        # Create explanation if available
        if "explanation" in transaction_result:
            explanation = Explanation(
                transaction_id=db_transaction.id,
                summary=transaction_result["explanation"].get("summary", ""),
                reasons=transaction_result["explanation"].get("reasons", []),
                suggested_actions=transaction_result["explanation"].get("suggested_actions", []),
                confidence=transaction_result["explanation"].get("confidence", 0.0),
                model_used="llama3",
                prompt_tokens=transaction_result["explanation"].get("prompt_tokens", 0),
                completion_tokens=transaction_result["explanation"].get("completion_tokens", 0),
                total_tokens=transaction_result["explanation"].get("total_tokens", 0),
            )
            db.add(explanation)
        
        # Create alert if high risk
        if transaction_result["risk_level"] in ["high", "critical"]:
            alert = Alert(
                transaction_id=db_transaction.id,
                alert_type="fraud_risk",
                severity=transaction_result["risk_level"],
                message=f"High risk transaction detected: {transaction_result['risk_score']:.1f}",
                status="pending"
            )
            db.add(alert)
            
            # Schedule alert notification
            background_tasks.add_task(
                send_fraud_alert,
                db_transaction.id,
                transaction_result["risk_score"],
                transaction_result["risk_level"]
            )
        
        await db.commit()
        
        # Update system metrics
        background_tasks.add_task(update_system_metrics, db)
        
        # Prepare response
        response_data = {
            "transaction_id": db_transaction.transaction_id,
            "risk_score": db_transaction.risk_score,
            "risk_level": db_transaction.risk_level,
            "is_fraudulent": db_transaction.is_fraudulent,
            "confidence_score": db_transaction.confidence_score,
            "explanation": transaction_result.get("explanation"),
            "timestamp": datetime.now().isoformat(),
            "recommended_action": get_recommended_action(db_transaction.risk_level)
        }
        
        return TransactionResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Transaction analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction analysis failed: {str(e)}"
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get detailed information about a specific transaction"""
    transaction = await db.execute(
        select(TransactionModel).where(
            and_(
                TransactionModel.transaction_id == transaction_id,
                TransactionModel.user_id == current_user.id
            )
        )
    )
    transaction = transaction.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Get explanation if exists
    explanation = await db.execute(
        select(Explanation).where(Explanation.transaction_id == transaction.id)
    )
    explanation = explanation.scalar_one_or_none()
    
    response_data = {
        "transaction_id": transaction.transaction_id,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "merchant_id": transaction.merchant_id,
        "device_id": transaction.device_id,
        "transaction_time": transaction.transaction_time.isoformat(),
        "risk_score": transaction.risk_score,
        "risk_level": transaction.risk_level,
        "is_fraudulent": transaction.is_fraudulent,
        "confidence_score": transaction.confidence_score,
        "explanation": {
            "summary": explanation.summary if explanation else "",
            "reasons": explanation.reasons if explanation else [],
            "suggested_actions": explanation.suggested_actions if explanation else []
        } if explanation else None,
        "timestamp": transaction.created_at.isoformat()
    }
    
    return TransactionResponse(**response_data)


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    risk_level: Optional[str] = None,
    is_fraudulent: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List transactions with filtering and pagination"""
    from sqlalchemy import select
    
    # Build query
    query = select(TransactionModel).where(
        TransactionModel.user_id == current_user.id
    )
    
    # Apply filters
    if start_date:
        query = query.where(TransactionModel.transaction_time >= start_date)
    if end_date:
        query = query.where(TransactionModel.transaction_time <= end_date)
    if risk_level:
        query = query.where(TransactionModel.risk_level == risk_level)
    if is_fraudulent is not None:
        query = query.where(TransactionModel.is_fraudulent == is_fraudulent)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.order_by(desc(TransactionModel.transaction_time))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Transform to response format
    items = []
    for t in transactions:
        items.append({
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "currency": t.currency,
            "merchant_id": t.merchant_id,
            "transaction_time": t.transaction_time.isoformat(),
            "risk_score": t.risk_score,
            "risk_level": t.risk_level,
            "is_fraudulent": t.is_fraudulent
        })
    
    return TransactionListResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        pages=total // limit + 1 if limit > 0 else 1,
        has_more=skip + len(items) < total
    )


@router.get("/stats/dashboard", response_model=TransactionStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get dashboard statistics for the current user"""
    from sqlalchemy import func, case
    
    # Today's date
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Last 7 days
    week_ago = today - timedelta(days=7)
    
    # Total transactions
    total_query = select(func.count()).where(
        TransactionModel.user_id == current_user.id
    )
    total_result = await db.execute(total_query)
    total_transactions = total_result.scalar() or 0
    
    # Today's transactions
    today_query = select(func.count()).where(
        and_(
            TransactionModel.user_id == current_user.id,
            TransactionModel.transaction_time >= today_start,
            TransactionModel.transaction_time <= today_end
        )
    )
    today_result = await db.execute(today_query)
    today_transactions = today_result.scalar() or 0
    
    # Fraudulent transactions
    fraud_query = select(func.count()).where(
        and_(
            TransactionModel.user_id == current_user.id,
            TransactionModel.is_fraudulent == True
        )
    )
    fraud_result = await db.execute(fraud_query)
    fraudulent_transactions = fraud_result.scalar() or 0
    
    # High risk transactions
    high_risk_query = select(func.count()).where(
        and_(
            TransactionModel.user_id == current_user.id,
            TransactionModel.risk_level.in_(["high", "critical"])
        )
    )
    high_risk_result = await db.execute(high_risk_query)
    high_risk_transactions = high_risk_result.scalar() or 0
    
    # Total amount
    amount_query = select(func.sum(TransactionModel.amount)).where(
        TransactionModel.user_id == current_user.id
    )
    amount_result = await db.execute(amount_query)
    total_amount = amount_result.scalar() or 0.0
    
    # Fraud amount
    fraud_amount_query = select(func.sum(TransactionModel.amount)).where(
        and_(
            TransactionModel.user_id == current_user.id,
            TransactionModel.is_fraudulent == True
        )
    )
    fraud_amount_result = await db.execute(fraud_amount_query)
    fraud_amount = fraud_amount_result.scalar() or 0.0
    
    # Average risk score
    avg_risk_query = select(func.avg(TransactionModel.risk_score)).where(
        TransactionModel.user_id == current_user.id
    )
    avg_risk_result = await db.execute(avg_risk_query)
    avg_risk_score = avg_risk_result.scalar() or 0.0
    
    # Risk score distribution (last 7 days)
    distribution_query = select(
        TransactionModel.risk_level,
        func.count(TransactionModel.id).label('count')
    ).where(
        and_(
            TransactionModel.user_id == current_user.id,
            TransactionModel.transaction_time >= week_ago
        )
    ).group_by(TransactionModel.risk_level)
    
    distribution_result = await db.execute(distribution_query)
    distribution_data = distribution_result.all()
    
    distribution = {}
    for level, count in distribution_data:
        distribution[level or "unknown"] = count
    
    return TransactionStats(
        total_transactions=total_transactions,
        today_transactions=today_transactions,
        fraudulent_transactions=fraudulent_transactions,
        high_risk_transactions=high_risk_transactions,
        total_amount=total_amount,
        fraud_amount=fraud_amount,
        avg_risk_score=avg_risk_score,
        risk_score_distribution=distribution
    )


@router.get("/alerts/recent", response_model=List[FraudAlertResponse])
async def get_recent_alerts(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get recent fraud alerts for the current user"""
    from sqlalchemy import select
    
    query = select(Alert).join(TransactionModel).where(
        and_(
            TransactionModel.user_id == current_user.id,
            Alert.status == "pending"
        )
    ).order_by(desc(Alert.created_at)).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    response_alerts = []
    for alert in alerts:
        # Get transaction details
        tx_query = select(TransactionModel).where(
            TransactionModel.id == alert.transaction_id
        )
        tx_result = await db.execute(tx_query)
        transaction = tx_result.scalar_one_or_none()
        
        if transaction:
            response_alerts.append(FraudAlertResponse(
                alert_id=str(alert.id),
                transaction_id=transaction.transaction_id,
                amount=transaction.amount,
                merchant_id=transaction.merchant_id,
                risk_score=transaction.risk_score,
                risk_level=transaction.risk_level,
                alert_type=alert.alert_type,
                severity=alert.severity,
                message=alert.message,
                created_at=alert.created_at.isoformat(),
                status=alert.status
            ))
    
    return response_alerts


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution_notes: str = Query(..., description="Notes on why alert was resolved"),
    is_false_positive: bool = Query(False, description="Whether this was a false positive"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Resolve a fraud alert"""
    from sqlalchemy import select
    
    query = select(Alert).join(TransactionModel).where(
        and_(
            Alert.id == alert_id,
            TransactionModel.user_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.status = "false_positive" if is_false_positive else "resolved"
    alert.reviewed_by = current_user.username
    alert.reviewed_at = datetime.now()
    alert.resolution_notes = resolution_notes
    
    await db.commit()
    
    return {"status": "success", "message": "Alert resolved successfully"}


@router.get("/trends/risk", response_model=List[FraudTrend])
async def get_risk_trends(
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get risk score trends over time"""
    from sqlalchemy import func, Date, cast
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = select(
        cast(TransactionModel.transaction_time, Date).label('date'),
        func.count(TransactionModel.id).label('total_transactions'),
        func.avg(TransactionModel.risk_score).label('avg_risk_score'),
        func.sum(case((TransactionModel.is_fraudulent == True, 1), else_=0)).label('fraud_count')
    ).where(
        and_(
            TransactionModel.user_id == current_user.id,
            TransactionModel.transaction_time >= start_date,
            TransactionModel.transaction_time <= end_date
        )
    ).group_by(
        cast(TransactionModel.transaction_time, Date)
    ).order_by(
        cast(TransactionModel.transaction_time, Date)
    )
    
    result = await db.execute(query)
    trends_data = result.all()
    
    trends = []
    for date, total, avg_risk, fraud_count in trends_data:
        trends.append(FraudTrend(
            date=date.isoformat(),
            total_transactions=total,
            avg_risk_score=float(avg_risk) if avg_risk else 0.0,
            fraudulent_transactions=fraud_count
        ))
    
    return trends


# Helper functions
async def send_fraud_alert(transaction_id: str, risk_score: float, risk_level: str):
    """Send fraud alert notification"""
    try:
        alert_service = get_alerting_service()
        await alert_service.send_fraud_alert(
            transaction_id=transaction_id,
            risk_score=risk_score,
            risk_level=risk_level
        )
        logger.info(f"Fraud alert sent for transaction {transaction_id}")
    except Exception as e:
        logger.error(f"Failed to send fraud alert: {e}")


async def update_system_metrics(db: AsyncSession):
    """Update system metrics in background"""
    try:
        metric = SystemMetrics(
            request_count=1,
            transactions_processed=1,
            timestamp=datetime.now()
        )
        db.add(metric)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to update system metrics: {e}")


def get_recommended_action(risk_level: str) -> str:
    """Get recommended action based on risk level"""
    actions = {
        "low": "Proceed normally",
        "medium": "Review transaction details",
        "high": "Require additional verification",
        "critical": "Block transaction and notify security team"
    }
    return actions.get(risk_level, "Review transaction")
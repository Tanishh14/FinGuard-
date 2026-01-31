"""
Fraud prediction endpoint. Real ML only. Fails with 503 if ML unavailable.
"""
from datetime import datetime
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.dependencies import get_db, get_current_active_user, get_ml_client
from app.schemas.transaction import PredictFraudRequest, PredictFraudResponse, ModelScores
from app.services.scoring_orchestrator import ScoringOrchestrator
from app.db.models import Transaction as TransactionModel, Alert, Explanation
from app.db.session import AsyncSessionLocal

router = APIRouter()


def _risk_label(level: str) -> str:
    if level in ("high", "critical"):
        return "HIGH"
    if level == "medium":
        return "MEDIUM"
    return "LOW"


@router.post("/fraud", response_model=PredictFraudResponse)
async def predict_fraud(
    body: PredictFraudRequest,
    db: AsyncSession = Depends(get_db),
    ml_client=Depends(get_ml_client),
    current_user=Depends(get_current_active_user),
):
    """Predict fraud via ML. Fails with 503 if ML unavailable. No mock response."""
    try:
        transaction_data = {
            "transaction_id": body.transaction_id,
            "user_id": body.user_id,
            "amount": body.amount,
            "timestamp": body.timestamp,
            "merchant_id": body.merchant,
            "device_id": body.device_id or None,
            "ip_address": body.ip_address,
        }
        orchestrator = ScoringOrchestrator(db, ml_client)
        result = await orchestrator.process_transaction(
            transaction_data=transaction_data,
            user_id=str(current_user.id),
        )
    except (httpx.HTTPError, RuntimeError) as e:
        logger.error(f"ML service failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML service unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Predict failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )
    risk_score = result.get("risk_score", 0.0)
    risk_level = result.get("risk_level", "low")
    ml_results = result.get("ml_results") or result

    # Persist transaction in a separate session so dashboard/live feed update.
    # Use a fresh session to avoid "transaction is aborted" when the orchestrator's
    # session was left in a failed state (e.g. feature extractor caught an exception).
    try:
        async with AsyncSessionLocal() as persist_session:
            db_txn = TransactionModel(
                transaction_id=result["transaction_id"],
                user_id=current_user.id,
                merchant_id=body.merchant,
                device_id=body.device_id or None,
                amount=body.amount,
                currency="USD",
                transaction_time=datetime.now(),
                risk_score=risk_score,
                risk_level=risk_level,
                is_fraudulent=result.get("is_fraudulent", False),
                confidence_score=result.get("confidence_score", 0.0),
                features=result.get("features"),
                anomaly_score=ml_results.get("anomaly_score"),
                graph_risk_score=ml_results.get("graph_risk_score"),
                processed_at=datetime.now(),
            )
            persist_session.add(db_txn)
            await persist_session.flush()
            if result.get("explanation"):
                expl = result["explanation"]
                persist_session.add(
                    Explanation(
                        transaction_id=db_txn.id,
                        summary=expl.get("summary", ""),
                        reasons=expl.get("reasons", []),
                        suggested_actions=expl.get("suggested_actions", []),
                        confidence=expl.get("confidence", 0.0),
                        model_used=expl.get("model_used", ""),
                    )
                )
            if risk_level in ("high", "critical"):
                persist_session.add(
                    Alert(
                        transaction_id=db_txn.id,
                        alert_type="fraud_risk",
                        severity=risk_level,
                        message=f"High risk: {risk_score:.1f}",
                        status="pending",
                    )
                )
            await persist_session.commit()
            # Publish event for real-time clients
            try:
                from app.services.broadcaster import publish
                publish({
                    "type": "transaction",
                    "transaction_id": db_txn.transaction_id,
                    "risk_score": float(db_txn.risk_score),
                    "risk_level": db_txn.risk_level,
                    "merchant_id": db_txn.merchant_id,
                    "amount": float(db_txn.amount),
                    "currency": db_txn.currency,
                    "is_fraudulent": bool(db_txn.is_fraudulent),
                    "transaction_time": str(db_txn.processed_at or db_txn.created_at),
                })
            except Exception:
                logger.warning("Failed to publish transaction event to subscribers")
    except Exception as e:
        logger.warning(f"Failed to store transaction after predict: {e}")
        # Still return the prediction
        try:
            from app.services.broadcaster import publish
            publish({
                "type": "transaction",
                "transaction_id": result.get("transaction_id"),
                "risk_score": float(risk_score),
                "risk_level": risk_level,
                "merchant_id": body.merchant,
                "amount": float(body.amount),
                "currency": "USD",
                "is_fraudulent": bool(result.get("is_fraudulent", False)),
                "transaction_time": str(datetime.now()),
            })
        except Exception:
            logger.warning("Failed to publish transaction event to subscribers")

    return PredictFraudResponse(
        transaction_id=body.transaction_id,
        fraud_score=min(1.0, risk_score / 100.0),
        risk_label=_risk_label(risk_level),
        model_scores=ModelScores(
            autoencoder=float(ml_results.get("anomaly_score", 0.0)),
            isolation_forest=float(ml_results.get("iforest_score", 0.0)),
            gnn=float(ml_results.get("graph_risk_score", 0.0)),
        ),
    )

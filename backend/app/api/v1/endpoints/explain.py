"""
Explainability API. Real explain service and DB only. Fails explicitly if unavailable.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.dependencies import get_db, get_current_active_user, get_explain_client
from app.schemas.transaction import ExplanationRequest, ExplanationResponse
from app.db.models import Transaction, Explanation as ExplanationModel

router = APIRouter()


@router.post("/transaction", response_model=ExplanationResponse)
async def explain_transaction_risk(
    request: ExplanationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
    explain_client=Depends(get_explain_client),
):
    """Explanation from DB or explain service. 404 if transaction not found. Fails if service unavailable."""
    r = await db.execute(
        select(Transaction).where(
            Transaction.transaction_id == request.transaction_id,
            Transaction.user_id == current_user.id,
        )
    )
    transaction = r.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    rex = await db.execute(select(ExplanationModel).where(ExplanationModel.transaction_id == transaction.id))
    existing = rex.scalar_one_or_none()
    if existing and not request.regenerate:
        return ExplanationResponse(
            transaction_id=transaction.transaction_id,
            summary=existing.summary,
            reasons=existing.reasons or [],
            suggested_actions=existing.suggested_actions or [],
            confidence=existing.confidence or 0.0,
            model_used=existing.model_used,
        )
    try:
        transaction_data = {
            "transaction_id": transaction.transaction_id,
            "amount": transaction.amount,
            "merchant_id": transaction.merchant_id,
            "risk_score": transaction.risk_score,
            "risk_level": transaction.risk_level,
            "is_fraudulent": transaction.is_fraudulent,
        }
        result = await explain_client.generate_explanation(transaction_data=transaction_data, query=request.query)
    except Exception as e:
        logger.error(f"Explain service failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Explainability service unavailable: {str(e)}",
        )
    return ExplanationResponse(
        transaction_id=transaction.transaction_id,
        summary=result.get("summary", ""),
        reasons=result.get("reasons", []),
        suggested_actions=result.get("suggested_actions", []),
        confidence=float(result.get("confidence", 0.0)),
        model_used=result.get("model_used"),
    )


@router.get("/pattern/{pattern_type}")
async def get_fraud_patterns(
    pattern_type: str,
    limit: int = Query(10, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    explain_client=Depends(get_explain_client),
):
    """Patterns from explain service. Fails if service unavailable."""
    try:
        return await explain_client.get_fraud_patterns(pattern_type=pattern_type, limit=limit)
    except Exception as e:
        logger.error(f"Patterns failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Explainability service unavailable: {str(e)}",
        )


@router.post("/query")
async def query_fraud_knowledge(
    question: str = Query(..., description="Question about fraud"),
    current_user=Depends(get_current_active_user),
    explain_client=Depends(get_explain_client),
):
    """Query from explain service. Fails if service unavailable."""
    if not question or len(question.strip()) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question must be at least 3 characters")
    try:
        answer = await explain_client.query_fraud_knowledge(question=question, user_id=str(current_user.id))
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Explainability service unavailable: {str(e)}",
        )
    return {
        "question": question,
        "answer": answer.get("answer", ""),
        "sources": answer.get("sources", []),
        "confidence": answer.get("confidence", 0.0),
    }


@router.get("/{transaction_id}", response_model=ExplanationResponse)
async def get_explanation_by_transaction_id(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Explanation from DB. 404 if not found."""
    r = await db.execute(
        select(Transaction).where(
            Transaction.transaction_id == transaction_id,
            Transaction.user_id == current_user.id,
        )
    )
    transaction = r.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    rex = await db.execute(select(ExplanationModel).where(ExplanationModel.transaction_id == transaction.id))
    explanation = rex.scalar_one_or_none()
    if not explanation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Explanation not found for this transaction")
    return ExplanationResponse(
        transaction_id=transaction.transaction_id,
        summary=explanation.summary,
        reasons=explanation.reasons or [],
        suggested_actions=explanation.suggested_actions or [],
        confidence=explanation.confidence or 0.0,
        model_used=explanation.model_used,
    )

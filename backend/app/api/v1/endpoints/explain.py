"""
Explainability API endpoints for fraud risk explanations
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.dependencies import get_db, get_current_active_user, get_explain_client
from app.schemas.transaction import ExplanationRequest, ExplanationResponse
from app.db.models import Transaction, Explanation as ExplanationModel

router = APIRouter()


@router.post("/transaction", response_model=ExplanationResponse)
async def explain_transaction_risk(
    request: ExplanationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
    explain_client = Depends(get_explain_client)
):
    """
    Get AI-generated explanation for transaction risk
    
    This endpoint uses RAG (Retrieval Augmented Generation) to provide
    human-readable explanations for fraud risk scores.
    """
    try:
        logger.info(f"Generating explanation for transaction {request.transaction_id}")
        
        # Get transaction from database
        from sqlalchemy import select
        
        query = select(Transaction).where(
            Transaction.transaction_id == request.transaction_id,
            Transaction.user_id == current_user.id
        )
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check if explanation already exists
        exp_query = select(ExplanationModel).where(
            ExplanationModel.transaction_id == transaction.id
        )
        exp_result = await db.execute(exp_query)
        existing_explanation = exp_result.scalar_one_or_none()
        
        if existing_explanation and not request.regenerate:
            # Return cached explanation
            return ExplanationResponse(
                transaction_id=transaction.transaction_id,
                summary=existing_explanation.summary,
                reasons=existing_explanation.reasons or [],
                suggested_actions=existing_explanation.suggested_actions or [],
                confidence=existing_explanation.confidence,
                model_used=existing_explanation.model_used
            )
        
        # Generate new explanation
        transaction_data = {
            "transaction_id": transaction.transaction_id,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "merchant_id": transaction.merchant_id,
            "device_id": transaction.device_id,
            "location": f"{transaction.location_city}, {transaction.location_country}",
            "transaction_time": transaction.transaction_time.isoformat(),
            "risk_score": transaction.risk_score,
            "risk_level": transaction.risk_level,
            "is_fraudulent": transaction.is_fraudulent,
            "anomaly_score": transaction.anomaly_score,
            "graph_risk_score": transaction.graph_risk_score,
            "features": transaction.features
        }
        
        # Call explainability service
        explanation_result = await explain_client.generate_explanation(
            transaction_data=transaction_data,
            query=request.query
        )
        
        # Store explanation in database
        new_explanation = ExplanationModel(
            transaction_id=transaction.id,
            summary=explanation_result.get("summary", ""),
            reasons=explanation_result.get("reasons", []),
            suggested_actions=explanation_result.get("suggested_actions", []),
            confidence=explanation_result.get("confidence", 0.0),
            model_used=explanation_result.get("model_used", "llama3"),
            prompt_tokens=explanation_result.get("prompt_tokens", 0),
            completion_tokens=explanation_result.get("completion_tokens", 0),
            total_tokens=explanation_result.get("total_tokens", 0)
        )
        
        db.add(new_explanation)
        await db.commit()
        
        return ExplanationResponse(
            transaction_id=transaction.transaction_id,
            summary=explanation_result.get("summary", ""),
            reasons=explanation_result.get("reasons", []),
            suggested_actions=explanation_result.get("suggested_actions", []),
            confidence=explanation_result.get("confidence", 0.0),
            model_used=explanation_result.get("model_used", "llama3")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.get("/pattern/{pattern_type}")
async def get_fraud_patterns(
    pattern_type: str,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
    explain_client = Depends(get_explain_client)
):
    """
    Get known fraud patterns by type
    
    Types: behavioral, network, device, merchant, all
    """
    try:
        patterns = await explain_client.get_fraud_patterns(
            pattern_type=pattern_type,
            limit=limit
        )
        
        return patterns
        
    except Exception as e:
        logger.error(f"Failed to get fraud patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fraud patterns: {str(e)}"
        )


@router.post("/query")
async def query_fraud_knowledge(
    question: str = Query(..., description="Question about fraud patterns or detection"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
    explain_client = Depends(get_explain_client)
):
    """
    Ask questions about fraud detection and get AI-generated answers
    
    Uses RAG to retrieve relevant information from fraud pattern database
    and generate contextual answers.
    """
    try:
        if not question or len(question.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question must be at least 3 characters long"
            )
        
        answer = await explain_client.query_fraud_knowledge(
            question=question,
            user_id=str(current_user.id)
        )
        
        return {
            "question": question,
            "answer": answer.get("answer", ""),
            "sources": answer.get("sources", []),
            "confidence": answer.get("confidence", 0.0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )
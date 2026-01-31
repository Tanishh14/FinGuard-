"""
Explainability HTTP service.
Generates human-readable explanations (SHAP/attribution + RAG/LLM).
Exposes: POST /explain, GET /health, GET /patterns.
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

app = FastAPI(
    title="FinGuard Explainability Service",
    description="Fraud risk explanations (RAG + LLM)",
    version="1.0.0",
)

_rag = None


def _get_rag():
    global _rag
    if _rag is None:
        try:
            from rag_pipeline import RAGPipeline
            enable_rag = os.path.exists("vector_store/index.faiss")
            _rag = RAGPipeline(enable_rag=enable_rag)
        except Exception:
            # Fallback when faiss/sentence_transformers not installed
            from llm_explainer import LLMExplainer
            class StubRAG:
                def __init__(self):
                    self.llm = LLMExplainer()
                def explain_transaction(self, transaction, model_signals):
                    return self.llm.explain(transaction, model_signals, "")
            _rag = StubRAG()
    return _rag


class ExplainRequest(BaseModel):
    transaction: Dict[str, Any] = {}
    query: Optional[str] = None
    llm_model: Optional[str] = None


def _to_backend_format(llm_text: str, transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Map LLM explanation string to backend-expected structure."""
    summary = llm_text[:2000] if len(llm_text) > 2000 else llm_text
    reasons = []
    if "anomaly" in llm_text.lower() or "deviation" in llm_text.lower():
        reasons.append({"reason": "Anomaly or behavioral deviation indicated", "severity": "medium", "impact_score": 0.5})
    if "high" in llm_text.lower() and "risk" in llm_text.lower():
        reasons.append({"reason": "Elevated fraud risk signals", "severity": "high", "impact_score": 0.7})
    suggested_actions = []
    if "block" in llm_text.lower():
        suggested_actions.append({"action": "Block transaction", "priority": "high", "description": "Review before approval"})
    elif "review" in llm_text.lower():
        suggested_actions.append({"action": "Review transaction", "priority": "medium", "description": "Manual review recommended"})
    else:
        suggested_actions.append({"action": "Monitor transaction", "priority": "low", "description": "Keep under observation"})
    confidence = 0.85 if "High" in llm_text or "high" in llm_text else 0.7
    return {
        "summary": summary,
        "reasons": reasons,
        "suggested_actions": suggested_actions,
        "confidence": confidence,
        "model_used": os.getenv("LLM_MODEL", "llama3"),
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }


@app.post("/explain")
async def explain(request: ExplainRequest) -> Dict[str, Any]:
    """
    Generate explanation for transaction risk.
    Input: transaction (with risk_score, risk_level, ml_results, etc.), optional query.
    Output: summary, reasons, suggested_actions, confidence.
    """
    try:
        transaction = request.transaction
        model_signals = {
            "risk_score": transaction.get("risk_score"),
            "risk_level": transaction.get("risk_level"),
            "ml_results": transaction.get("ml_results", {}),
            "features": transaction.get("features", {}),
        }
        rag = _get_rag()
        text = rag.explain_transaction(transaction=transaction, model_signals=model_signals)
        return _to_backend_format(text, transaction)
    except Exception as e:
        # Fallback when LLM/RAG unavailable
        risk_score = request.transaction.get("risk_score", 0)
        risk_level = request.transaction.get("risk_level", "low")
        return _to_backend_format(
            f"Transaction risk score: {risk_score} ({risk_level}). "
            "Automated analysis completed. Review recommended for elevated risk.",
            request.transaction,
        )


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "FinGuard Explainability",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/patterns")
async def patterns(
    type: str = Query("all", description="Pattern type: behavioral, network, device, merchant, all"),
    limit: int = Query(10, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Return known fraud patterns (stub for RAG/knowledge base)."""
    stubs = [
        {"id": "fp_1", "type": "behavioral", "name": "Unusual amount spike", "description": "Transaction amount far above user baseline"},
        {"id": "fp_2", "type": "network", "name": "Shared device", "description": "Device used by multiple high-risk accounts"},
        {"id": "fp_3", "type": "device", "name": "New device", "description": "First transaction from this device"},
        {"id": "fp_4", "type": "merchant", "name": "High-fraud merchant", "description": "Merchant with elevated fraud rate"},
    ]
    if type != "all":
        stubs = [s for s in stubs if s["type"] == type]
    return stubs[:limit]


class QueryRequest(BaseModel):
    question: str = ""
    user_id: Optional[str] = None


@app.post("/query")
async def query(request: QueryRequest) -> Dict[str, Any]:
    """Query fraud knowledge base (RAG). Stub returns short answer."""
    return {
        "answer": "Fraud detection uses behavioral, network, and device signals. Review high-risk transactions and explanations for details.",
        "sources": [],
        "confidence": 0.8,
    }

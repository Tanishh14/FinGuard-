"""
ML inference HTTP service.
Stateless at inference time. No frontend imports.
Exposes: POST /predict, GET /health, GET /models.
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from inference import predict as ml_predict

app = FastAPI(
    title="FinGuard ML Service",
    description="Fraud inference (AE + IF + GNN)",
    version="1.0.0",
)


class PredictRequest(BaseModel):
    features: Dict[str, Any] = {}
    transaction_data: Dict[str, Any] = {}
    timestamp: Optional[str] = None


@app.post("/predict")
async def predict(request: PredictRequest) -> Dict[str, Any]:
    """
    Run fraud inference for one transaction.
    Input: features (from backend FeatureExtractor), transaction_data.
    Output: fraud_score (0-1), risk_label, model-wise scores.
    """
    try:
        result = ml_predict(
            transaction_data=request.transaction_data,
            features=request.features,
        )
        anomaly = float(result.get("anomaly_score", 0.0))
        gnn = float(result.get("graph_risk_score", 0.0))
        combined = (0.4 * anomaly + 0.6 * gnn) * 100.0
        combined = max(0.0, min(100.0, combined))
        return {
            "anomaly_score": anomaly,
            "iforest_score": result.get("iforest_score", anomaly),
            "graph_risk_score": gnn,
            "combined_risk_score": round(combined, 2),
            "risk_level": result.get("risk_level", "low"),
            "features_used": result.get("features_used", []),
            "model_confidence": result.get("model_confidence", 0.5),
            "fraud_type_prediction": result.get("fraud_type_prediction"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "FinGuard ML",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/models")
async def models() -> Dict[str, Any]:
    model_dir = os.getenv("MODEL_PATH", os.path.join(os.path.dirname(__file__), "models"))
    ae_path = os.path.join(model_dir, "autoencoder.pkl")
    if_path = os.path.join(model_dir, "isolation_forest.pkl")
    gnn_paths = [os.path.join(model_dir, "gnn_gat.pt"), os.path.join(model_dir, "gnn.pt")]
    return {
        "autoencoder": os.path.isfile(ae_path),
        "isolation_forest": os.path.isfile(if_path),
        "gnn": any(os.path.isfile(p) for p in gnn_paths),
        "model_path": model_dir,
    }

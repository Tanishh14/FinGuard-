"""
Single predict(transaction) interface for fraud detection.
Uses Autoencoder (reconstruction error → 0-1), Isolation Forest (decision_function → 0-1),
GNN (sigmoid output 0-1). Falls back to heuristics in 0-1 when models unavailable.
"""

import os
import math
from typing import Dict, Any, Optional, Tuple

MODEL_DIR = os.getenv("MODEL_PATH", os.path.join(os.path.dirname(__file__), "models"))

_ae = None
_ae_scaler = None
_iforest = None
_if_scaler = None
_gnn = None
_gnn_input_dim = None


def _load_ae() -> Tuple[Optional[Any], Optional[Any]]:
    global _ae, _ae_scaler
    if _ae is not None:
        return _ae, _ae_scaler
    path = os.path.join(MODEL_DIR, "autoencoder.pkl")
    scaler_path = os.path.join(MODEL_DIR, "ae_scaler.pkl")
    if not os.path.isfile(path):
        return None, None
    try:
        import joblib
        _ae = joblib.load(path)
        _ae_scaler = joblib.load(scaler_path) if os.path.isfile(scaler_path) else None
        return _ae, _ae_scaler
    except Exception:
        return None, None


def _load_iforest() -> Tuple[Optional[Any], Optional[Any]]:
    global _iforest, _if_scaler
    if _iforest is not None:
        return _iforest, _if_scaler
    path = os.path.join(MODEL_DIR, "isolation_forest.pkl")
    scaler_path = os.path.join(MODEL_DIR, "if_scaler.pkl")
    if not os.path.isfile(path):
        return None, None
    try:
        import joblib
        _iforest = joblib.load(path)
        _if_scaler = joblib.load(scaler_path) if os.path.isfile(scaler_path) else None
        return _iforest, _if_scaler
    except Exception:
        return None, None


def _load_gnn() -> Tuple[Optional[Any], Optional[int]]:
    """Returns (model, input_dim or None)."""
    global _gnn, _gnn_input_dim
    if _gnn is not None:
        return _gnn, getattr(_gnn, "_input_dim", _gnn_input_dim)
    for name in ("gnn_gat.pt", "gnn.pt"):
        path = os.path.join(MODEL_DIR, name)
        if not os.path.isfile(path):
            continue
        try:
            import torch
            from torch.nn import Linear
            import torch.nn.functional as F
            try:
                from torch_geometric.nn import GATConv
            except ImportError:
                GATConv = None
            if GATConv is None:
                return None, None
            class FraudGNN(torch.nn.Module):
                def __init__(self, input_dim):
                    super().__init__()
                    self.gat1 = GATConv(input_dim, 32, heads=2, concat=True)
                    self.gat2 = GATConv(64, 16, heads=1)
                    self.out = Linear(16, 1)
                def forward(self, x, edge_index):
                    x = self.gat1(x, edge_index)
                    x = F.elu(x)
                    x = self.gat2(x, edge_index)
                    x = F.elu(x)
                    return torch.sigmoid(self.out(x))
            state = torch.load(path, map_location="cpu", weights_only=True)
            # Infer input_dim from first layer weight
            for k, v in state.items():
                if "gat1" in k and "weight" in k:
                    _gnn_input_dim = v.shape[1]
                    break
            else:
                _gnn_input_dim = 24
            _gnn = FraudGNN(input_dim=_gnn_input_dim)
            _gnn.load_state_dict(state, strict=False)
            _gnn.eval()
            _gnn._input_dim = _gnn_input_dim
            return _gnn, _gnn_input_dim
        except Exception:
            continue
    return None, None


def _build_feature_vector(transaction_data: Dict[str, Any], features: Dict[str, Any]) -> Any:
    """Build numeric feature vector for AE/IF/GNN. Returns (1, n) array."""
    try:
        from ml.pipelines.feature_builder import build_features_from_transaction
        import numpy as np
        arr = build_features_from_transaction(transaction_data, features)
        return arr.reshape(1, -1)
    except Exception:
        import numpy as np
        amount = float(transaction_data.get("amount", 0))
        return np.array([[amount, math.log1p(amount), 0] + [0.0] * 21], dtype=np.float32)[:, :24]


def _anomaly_from_ae(feature_vec, ae, scaler) -> float:
    """Reconstruction error → 0-1. Higher error = higher anomaly."""
    import numpy as np
    try:
        X = scaler.transform(feature_vec) if scaler is not None else feature_vec
        pred = ae.predict(X)
        mse = float(np.mean((X - pred) ** 2))
        # Normalize to 0-1: use 1 - exp(-mse) so 0→0, large→1
        score = 1.0 - math.exp(-min(mse, 10.0))
        return max(0.0, min(1.0, score))
    except Exception:
        return 0.0


def _anomaly_from_iforest(feature_vec, model, scaler) -> float:
    """Isolation Forest decision_function → 0-1. More negative = more anomalous."""
    import numpy as np
    try:
        X = scaler.transform(feature_vec) if scaler is not None else feature_vec
        score = model.decision_function(X)
        score = float(score[0]) if hasattr(score, "__len__") else float(score)
        # decision_function: negative = anomaly. Map to 0-1: 1 / (1 + exp(score))
        # When score very negative, exp(score)~0 → prob~1. When score positive, prob~0.
        prob = 1.0 / (1.0 + math.exp(score))
        return max(0.0, min(1.0, prob))
    except Exception:
        return 0.0


def _risk_from_gnn(feature_vec, gnn, expected_dim: Optional[int] = None) -> float:
    """GNN forward on single-node graph → already sigmoid 0-1."""
    try:
        import torch
        import numpy as np
        n = feature_vec.shape[1]
        if expected_dim is not None and n != expected_dim:
            if n < expected_dim:
                pad = np.zeros((1, expected_dim - n), dtype=np.float32)
                feature_vec = np.hstack([feature_vec, pad])
            else:
                feature_vec = feature_vec[:, :expected_dim]
        x = torch.tensor(feature_vec, dtype=torch.float32)
        edge_index = torch.zeros((2, 0), dtype=torch.long)
        with torch.no_grad():
            out = gnn(x, edge_index)
        return float(out.squeeze().item())
    except Exception:
        return 0.0


def predict(
    transaction_data: Dict[str, Any],
    features: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run fraud inference. Returns anomaly_score, graph_risk_score, iforest_score in [0, 1].
    Uses real models when loaded; otherwise heuristics in 0-1.
    """
    import numpy as np
    feature_vec = _build_feature_vector(transaction_data, features)
    n_features = feature_vec.shape[1]

    # Autoencoder: reconstruction error → 0-1
    ae, ae_scaler = _load_ae()
    if ae is not None:
        try:
            ae_score = _anomaly_from_ae(feature_vec, ae, ae_scaler)
        except Exception:
            ae_score = None
    else:
        ae_score = None

    # Isolation Forest → 0-1
    iforest, if_scaler = _load_iforest()
    if iforest is not None:
        try:
            iforest_score = _anomaly_from_iforest(feature_vec, iforest, if_scaler)
        except Exception:
            iforest_score = None
    else:
        iforest_score = None

    # Combined anomaly: average of AE and IF when both available
    if ae_score is not None and iforest_score is not None:
        anomaly_score = (ae_score + iforest_score) / 2.0
    elif ae_score is not None:
        anomaly_score = ae_score
    elif iforest_score is not None:
        anomaly_score = iforest_score
    else:
        amount = float(transaction_data.get("amount", 0))
        anomaly_score = min(1.0, amount / 5000.0) * 0.5 + 0.1

    # GNN → 0-1 (already sigmoid)
    gnn, gnn_input_dim = _load_gnn()
    if gnn is not None:
        try:
            graph_risk_score = _risk_from_gnn(feature_vec, gnn, gnn_input_dim)
        except Exception:
            graph_risk_score = anomaly_score * 0.8
    else:
        graph_risk_score = anomaly_score * 0.8

    anomaly_score = max(0.0, min(1.0, anomaly_score))
    if iforest_score is None:
        iforest_score = anomaly_score
    else:
        iforest_score = max(0.0, min(1.0, iforest_score))
    graph_risk_score = max(0.0, min(1.0, graph_risk_score))

    risk_level = "low"
    if (0.4 * anomaly_score + 0.6 * graph_risk_score) >= 0.75:
        risk_level = "high"
    elif (0.4 * anomaly_score + 0.6 * graph_risk_score) >= 0.5:
        risk_level = "medium"

    features_used = list(features.keys())[:20] if features else []
    return {
        "anomaly_score": round(anomaly_score, 4),
        "iforest_score": round(iforest_score, 4),
        "graph_risk_score": round(graph_risk_score, 4),
        "risk_level": risk_level,
        "model_confidence": 0.7,
        "features_used": features_used,
        "fraud_type_prediction": "suspicious" if risk_level == "high" else None,
    }


def fraud_score(features_vec) -> float:
    """Legacy: single score from feature vector. Prefer predict()."""
    return 0.5

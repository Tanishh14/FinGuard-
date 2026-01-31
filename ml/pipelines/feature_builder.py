"""
Consistent feature construction for fraud inference.
Used by ML service only; no frontend imports.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

# Fixed feature order for AE/IF models (must match training)
FEATURE_ORDER = [
    "amount", "amount_log", "currency", "transaction_type", "category",
    "has_location", "latitude", "longitude",
    "user_transaction_count", "user_avg_amount", "user_amount_std",
    "user_frequency_days", "is_new_user", "time_since_first_transaction",
    "merchant_risk_score", "merchant_fraud_count", "merchant_total_txn",
    "device_risk_score", "device_is_suspicious", "device_account_count",
    "hour_of_day", "day_of_week", "is_weekend",
    "graph_risk_raw", "behavioral_deviation",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build numerical features for anomaly detection (batch/training).
    Compatible with credit card fraud dataset.
    """
    features = df.drop(columns=["Class"], errors="ignore")
    features = features.select_dtypes(include=["number"])
    return features


def build_features_from_transaction(
    transaction_data: Dict[str, Any],
    features: Dict[str, Any],
) -> np.ndarray:
    """
    Build a single numeric feature vector from transaction + extracted features.
    Returns 1D array for inference (AE, IF). Missing keys filled with 0.
    """
    merged = {**transaction_data, **features}
    out = []
    for key in FEATURE_ORDER:
        val = merged.get(key)
        if val is None:
            out.append(0.0)
        elif isinstance(val, (int, float)):
            out.append(float(val))
        elif isinstance(val, bool):
            out.append(1.0 if val else 0.0)
        else:
            out.append(0.0)
    return np.array(out, dtype=np.float32).reshape(1, -1)

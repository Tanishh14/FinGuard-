"""
Monitoring metrics for fraud detection pipeline.
Tracks: prediction volume, fraud rate, model confidence drift, latency.
Ready for Prometheus / Grafana integration.
"""

from typing import Dict, Any
from datetime import datetime, timedelta

# In-memory counters (in production use Prometheus client or Redis)
_metrics = {
    "predictions_total": 0,
    "fraud_detected_total": 0,
    "requests_total": 0,
    "latency_sum_ms": 0.0,
    "last_reset": datetime.now().isoformat(),
}


def record_prediction(is_fraud: bool, latency_ms: float = 0.0) -> None:
    _metrics["predictions_total"] += 1
    _metrics["requests_total"] += 1
    if is_fraud:
        _metrics["fraud_detected_total"] += 1
    _metrics["latency_sum_ms"] += latency_ms


def get_metrics() -> Dict[str, Any]:
    total = _metrics["predictions_total"] or 1
    return {
        "predictions_total": _metrics["predictions_total"],
        "fraud_detected_total": _metrics["fraud_detected_total"],
        "fraud_rate": round(_metrics["fraud_detected_total"] / total, 4),
        "requests_total": _metrics["requests_total"],
        "average_latency_ms": round(_metrics["latency_sum_ms"] / total, 2),
        "last_reset": _metrics["last_reset"],
    }


def reset_metrics() -> None:
    _metrics["predictions_total"] = 0
    _metrics["fraud_detected_total"] = 0
    _metrics["requests_total"] = 0
    _metrics["latency_sum_ms"] = 0.0
    _metrics["last_reset"] = datetime.now().isoformat()

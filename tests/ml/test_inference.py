import math
import types
import numpy as np
from ml import inference


def test_ae_extreme_values():
    # Dummy AE that returns zeros (perfect reconstruction of zeros)
    class DummyAE:
        def predict(self, X):
            return np.zeros_like(X)

    # Small input -> very small mse -> low anomaly
    small = np.array([[1e-6, 1e-6, 1e-6]])
    # Ensure function behaves when AE model is present
    # Small input -> very small mse -> low anomaly
    score_small = inference._anomaly_from_ae(small, DummyAE(), None)
    assert 0.0 <= score_small <= 0.1

    # Large input -> large mse -> high anomaly
    large = np.array([[1e3, 1e3, 1e3]])
    score_large = inference._anomaly_from_ae(large, DummyAE(), None)
    assert 0.9 <= score_large <= 1.0


def test_iforest_extreme_scores():
    # Dummy IF with score_samples implemented
    class DummyIF:
        def score_samples(self, X):
            # If X[0][0] < 0 -> return -100 (very anomalous)
            return np.array([-100.0]) if X[0][0] < 0 else np.array([100.0])

    neg = np.array([[-1.0]])
    pos = np.array([[10.0]])
    prob_neg = inference._anomaly_from_iforest(neg, DummyIF(), None)
    prob_pos = inference._anomaly_from_iforest(pos, DummyIF(), None)
    assert prob_neg > 0.9
    assert prob_pos < 0.1


def test_combined_fraud_score_range():
    # Build a transaction with extremes
    features = {}
    tx = {"amount": 1000000}
    # Monkeypatch functions to force anomaly=1, gnn=1
    orig_ae = inference._anomaly_from_ae
    orig_if = inference._anomaly_from_iforest
    orig_gnn = inference._risk_from_gnn
    # Provide dummy models so predict will use our patched functions
    class DummyModel:
        pass

    orig_load_ae = inference._load_ae
    orig_load_if = inference._load_iforest
    orig_load_gnn = inference._load_gnn
    try:
        inference._load_ae = lambda: (DummyModel(), None)
        inference._load_iforest = lambda: (DummyModel(), None)
        inference._load_gnn = lambda: (DummyModel(), None)
        inference._anomaly_from_ae = lambda fv, a, s: 1.0
        inference._anomaly_from_iforest = lambda fv, m, s: 1.0
        inference._risk_from_gnn = lambda fv, g, d: 1.0
        res = inference.predict(tx, features)
        assert float(res.get("fraud_score", 0)) >= 99.0
    finally:
        inference._anomaly_from_ae = orig_ae
        inference._anomaly_from_iforest = orig_if
        inference._risk_from_gnn = orig_gnn
        inference._load_ae = orig_load_ae
        inference._load_iforest = orig_load_if
        inference._load_gnn = orig_load_gnn

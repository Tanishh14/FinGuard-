# ml/inference.py
import joblib
import torch
import numpy as np

def fraud_score(features):
    ae = torch.load("ml/models/autoencoder.pt")
    iforest = joblib.load("ml/models/isolation_forest.pkl")

    ae_score = np.mean((features - ae(features)) ** 2)
    if_score = -iforest.decision_function(features)[0]

    return round((0.6 * ae_score + 0.4 * if_score) * 100, 2)

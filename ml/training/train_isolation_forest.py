import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ml.pipelines.feature_builder import build_features

DATA_PATH = "data/raw/Credit Card-Fraud Detection.csv"
MODEL_PATH = "ml/models/isolation_forest.pkl"
SCALER_PATH = "ml/models/if_scaler.pkl"

if __name__ == "__main__":
    print("📥 Loading dataset...")
    df = pd.read_csv(DATA_PATH)

    print("🛠 Building features...")
    X = build_features(df)

    print("📏 Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("🌲 Training Isolation Forest...")
    if_model = IsolationForest(
        n_estimators=200,
        max_samples="auto",
        contamination=0.01,   # fraud is rare
        random_state=42,
        n_jobs=-1
    )

    if_model.fit(X_scaled)

    print("💾 Saving model...")
    joblib.dump(if_model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print("✅ Isolation Forest trained & saved!")

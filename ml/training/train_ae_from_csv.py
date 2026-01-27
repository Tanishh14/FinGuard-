import pandas as pd
from pipelines.feature_builder import build_features
from training.train_autoencoder import train_autoencoder

DATASET_PATH = "data/raw/Financial Transactions Dataset for Fraud Detection.csv"

if __name__ == "__main__":
    print("📥 Loading dataset...")
    df = pd.read_csv(DATASET_PATH)

    print("🛠 Building features...")
    X = build_features(df)

    print(f"📊 Feature shape: {X.shape}")

    print("🚀 Training Autoencoder...")
    train_autoencoder(X)

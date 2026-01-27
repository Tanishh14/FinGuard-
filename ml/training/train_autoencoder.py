import os
import numpy as np
import pandas as pd
import joblib

from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.callbacks import EarlyStopping

from ml.pipelines.feature_builder import build_features

# -------------------------------
# CONFIG
# -------------------------------
DATA_PATH = "data/raw/Credit Card-Fraud Detection.csv"
MODEL_PATH = "ml/models/autoencoder.pkl"

SAMPLE_ROWS = 50000      # ⬅ prevents OOM
EPOCHS = 20              # ⬅ dev-safe
BATCH_SIZE = 32          # ⬅ low memory
RANDOM_STATE = 42


# -------------------------------
# LOAD DATA
# -------------------------------
print("📥 Loading dataset...")
df = pd.read_csv(DATA_PATH)

# Sample to avoid OOM kill
df = df.sample(n=min(SAMPLE_ROWS, len(df)), random_state=RANDOM_STATE)
df.reset_index(drop=True, inplace=True)

print(f"✅ Using {len(df)} rows for training")

# -------------------------------
# FEATURE ENGINEERING
# -------------------------------
print("🛠 Building features...")
X = build_features(df)

# -------------------------------
# SCALING
# -------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Save scaler
os.makedirs("ml/models", exist_ok=True)
joblib.dump(scaler, "ml/models/ae_scaler.pkl")

# -------------------------------
# AUTOENCODER MODEL
# -------------------------------
print("🔥 Building AutoEncoder...")

input_dim = X_scaled.shape[1]
input_layer = Input(shape=(input_dim,))

encoded = Dense(16, activation="relu")(input_layer)
encoded = Dense(8, activation="relu")(encoded)

decoded = Dense(16, activation="relu")(encoded)
output_layer = Dense(input_dim, activation="linear")(decoded)

autoencoder = Model(inputs=input_layer, outputs=output_layer)
autoencoder.compile(optimizer="adam", loss="mse")

autoencoder.summary()

# -------------------------------
# TRAINING
# -------------------------------
print("🚀 Training AutoEncoder...")

early_stop = EarlyStopping(
    monitor="loss",
    patience=3,
    restore_best_weights=True
)

autoencoder.fit(
    X_scaled,
    X_scaled,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    shuffle=True,
    callbacks=[early_stop],
    verbose=1
)

# -------------------------------
# SAVE MODEL
# -------------------------------
joblib.dump(autoencoder, MODEL_PATH)

print("💾 AutoEncoder training complete & saved!")

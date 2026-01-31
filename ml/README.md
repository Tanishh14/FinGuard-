ML service calibration and runtime configuration

This ML inference service exposes environment variables to tune how model outputs
are scaled to probabilities. This allows calibration in production without code
changes.

Environment variables:
- AE_SIGMOID_K (default 8.0): Steepness of sigmoid for Autoencoder reconstruction error.
- AE_SIGMOID_LOC (default 0.7): Center (location) used in AE sigmoid; increase to reduce false positives.
- IF_SIGMOID_K (default 8.0): Steepness of sigmoid for IsolationForest inverted score.
- IF_SIGMOID_LOC (default 0.0): Location used for IF sigmoid mapping.
- GNN_GAMMA (default 1.0): Gamma sharpening for GNN probability; >1 pushes values towards 0/1.

Calibration workflow (recommended):
1. Compute model raw outputs on a labeled validation set.
2. Fit an isotonic or logistic calibrator mapping raw -> probability.
3. Persist calibration artifacts as joblib/pickle files and modify `_anomaly_from_ae`
   and `_anomaly_from_iforest` to load and use them (future work).

Tune these env vars for immediate behavior changes:
- To make AE more sensitive to small reconstruction errors: reduce AE_SIGMOID_LOC.
- To make IF more sensitive: increase IF_SIGMOID_K.
- To sharpen GNN output: increase GNN_GAMMA (>1).

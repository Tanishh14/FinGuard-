# FinGuard AI – Architecture

## System goal

End-to-end fraud detection and risk intelligence: frontend sends transaction/user data; backend orchestrates auth, validation, and routing; ML pipeline performs fraud inference (AE + IF + GNN); explainability produces human-readable insights; monitoring tracks metrics. All components are containerized via Docker Compose.

## Component responsibilities

- **Frontend**: Dashboard UI. Login/JWT, transaction submission form, fraud score visualization, risk badge (LOW/MEDIUM/HIGH), explainability panel. Talks ONLY to backend APIs. No direct ML or DB.
- **Backend**: Single source of truth and API gateway. JWT auth, Pydantic validation, routing. Calls ML and explainability over HTTP. Stores predictions and metadata. No ML logic.
- **ML**: Stateless inference. Loads pre-trained AE, IF, GNN. Exposes predict(transaction) and feature builder. Returns fraud_score (0–1), risk_label, model-wise scores. No frontend imports.
- **Explainability**: SHAP/attribution and RAG/LLM explanations. Input: transaction_id + model outputs. Output: top features, natural-language explanation, confidence. Backend fetches via HTTP.
- **Data**: Training datasets and sample transactions only. Never accessed by frontend.
- **Monitoring**: Prediction volume, fraud rate, drift, latency. Metrics endpoint; Prometheus/Grafana-ready.

## Data flow

1. Transaction: Frontend → POST /predict/fraud (JWT) → Backend → ML (POST /predict) + Explainability (POST /explain) → Backend stores → Response with fraud_score + explanation.
2. Explanation: Frontend → GET /explain/{transaction_id} (JWT) → Backend (DB cached explanation).
3. Auth: Frontend → POST /auth/login → Backend returns JWT.

## Security boundaries

- Frontend: no ML or DB; only backend URL.
- Backend: no ML logic; calls ML and explainability over internal HTTP.
- ML/Explainability: no frontend imports; stateless at inference.
- Data: training/samples only; not exposed to frontend.

## Docker topology

backend (8000), ml-service (8001), explain-service (8002), frontend (3000) on finguard-network. Frontend build: ./frontend_file/frontend. NEXT_PUBLIC_API_URL points to backend.

Real-time updates: The backend exposes a Server-Sent Events endpoint `/api/v1/stream` which broadcasts new transactions and alerts to connected clients. Use SSE in the frontend to receive live updates without polling.


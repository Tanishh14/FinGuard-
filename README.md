# FinGuard AI – Fraud Detection & Risk Intelligence

End-to-end fraud detection pipeline: frontend → backend → ML → explainability, with monitoring and Docker Compose.

## System flow (textual)

```
[Frontend]  --POST /auth/login-->           [Backend]
     |                                      |
     |  --POST /predict/fraud (JWT)-->      |  --POST /predict-->  [ML Service]
     |                                      |  --POST /explain-->   [Explainability]
     |  <-- fraud_score + explanation --    |  <-- scores + text --  (both)
     |
     |  --GET /explain/{tx_id} (JWT)-->     [Backend]  --> DB (cached explanation)
     |  <-- explanation --
```

- **Backend**: API gateway, JWT auth, validation, storage. Calls ML and explainability over HTTP.
- **ML**: Stateless inference (AE + IF + GNN); single `predict(transaction)` interface.
- **Explainability**: Human-readable explanations (RAG/LLM, feature attribution).
- **Monitoring**: Metrics endpoint; Prometheus/Grafana-ready.

## How to run locally

### With Docker Compose (recommended)

```bash
# From repo root
cp .env.example .env   # optional: set NEXT_PUBLIC_API_URL, etc.
docker-compose up --build
```

- Backend: http://localhost:8000  
- Frontend: http://localhost:3000  
- ML service: http://localhost:8001  
- Explainability: http://localhost:8002  
- Docs: http://localhost:8000/docs (when not production)

Frontend uses `NEXT_PUBLIC_API_URL=http://localhost:8000` so the browser talks to the backend.

### Without Docker

1. **Backend** (from `backend/`):
   ```bash
   cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000
   ```
   Set `ML_SERVICE_URL`, `EXPLAIN_SERVICE_URL`, `DATABASE_URL`, `REDIS_URL` in `.env` if needed.pip

2. **ML service** (from `ml/`):
   ```bash
   cd ml && pip install -r requirements-ml.txt && uvicorn server:app --port 8001
   ```

3. **Explainability** (from `explainability/`):
   ```bash
   cd explainability && pip install -r requirements.txt && uvicorn server:app --port 8002
   ```

4. **Frontend** (from `frontend_file/frontend/`):
   ```bash
   cd frontend_file/frontend && npm ci && npm run dev
   ```
   Ensure `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## API examples

### Login (get JWT)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo"}'
```

Response: `{"access_token":"...", "token_type":"bearer", "expires_in_minutes":10080}`

### Submit transaction (fraud prediction)

```bash
export TOKEN="<access_token from login>"
curl -X POST http://localhost:8000/api/v1/predict/fraud \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_id": "txn_001",
    "amount": 149.99,
    "currency": "USD",
    "merchant_id": "m_001"
  }'
```

Response includes `risk_score`, `risk_level`, `explanation`, `recommended_action`, `transaction_id`.

### Get explanation by transaction ID

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/explain/txn_001
```

### Health

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health/detailed
```

## Data

Used only for training and sample data. Place datasets under `data/raw/` as per existing README instructions. Not used by frontend.

## Tests

From repo root, run backend tests (from `backend/` so `main` resolves):

```bash
cd backend && pytest ../tests/backend -v
```

Covers health, auth/login, predict/fraud (with mocked ML and explainability), explain by transaction_id, and auth boundaries.

## Docs

- **ARCHITECTURE.md**: Component responsibilities, data flow, security boundaries, Docker topology.

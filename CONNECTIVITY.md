# FinGuard – Backend, Frontend & ML Connectivity

This document describes how the **backend**, **frontend**, and **ML** services connect so you can fix "Failed to fetch" and API errors.

## Service URLs

| Service        | Default URL              | Purpose |
|----------------|--------------------------|--------|
| **Backend**    | `http://localhost:8000`   | Main API: auth, transactions, GNN, anomaly, dashboard |
| **Frontend**   | `http://localhost:3000`  | Next.js UI; proxies `/api/v1/*` to backend when same-origin |
| **ML**         | `http://localhost:8001`  | Fraud inference (autoencoder, isolation forest, GNN); called by backend only |
| **Explain**    | `http://localhost:8002`  | LLM explanations; called by backend only |

## How the frontend talks to the backend

1. **In the browser** the frontend uses **same-origin** requests (`/api/v1/...`). Next.js **rewrites** (in `frontend_file/frontend/next.config.js`) proxy these to `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). This avoids CORS and "Failed to fetch" when the backend is on another port.
2. **`NEXT_PUBLIC_API_URL`** is used by:
   - Next.js rewrites (so the dev server knows where to proxy).
   - Server-side code (e.g. SSR) when building full URLs.

**Frontend env (e.g. `frontend_file/frontend/.env.local`):**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If you run the backend on another host/port, set this to that URL (no trailing slash).

## How the backend talks to ML and Explain

- **Backend** calls **ML** at `ML_SERVICE_URL` (default `http://localhost:8001`) for `/predict` and `/health`.
- **Backend** calls **Explain** at `EXPLAIN_SERVICE_URL` (default `http://localhost:8002`) for explanations and health.

**Backend env (e.g. `backend/.env` or root `.env`):**

```env
DATABASE_URL=postgresql+asyncpg://finguard:finguard_password@localhost:5432/finguard_db
REDIS_URL=redis://localhost:6379/0
ML_SERVICE_URL=http://localhost:8001
EXPLAIN_SERVICE_URL=http://localhost:8002
```

For **Docker**, use service names: `http://ml-service:8001`, `http://explain-service:8002` (as in `docker-compose.yml`).

## Fixing "Failed to fetch" and API errors

1. **Backend must be running**  
   From repo root:
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Use `app.main:app` for the full app (DB, auth, GNN, anomaly).  
   Health: [http://localhost:8000/health](http://localhost:8000/health) and [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health).

2. **Frontend must point at the backend**  
   In `frontend_file/frontend/.env.local` set:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
   Restart the Next dev server after changing env.

3. **Log in**  
   GNN (`/api/v1/gnn/clusters`), Anomaly (`/api/v1/anomaly/summary`), and Dashboard all require an authenticated user. Use the login page; without auth you get 401 and the UI will show "Authentication required" or similar.

4. **Empty data vs errors**  
   If the backend is up and you are logged in, GNN/Anomaly/Dashboard return **200 with empty data** when there are no transactions (no more 404). The UI should show empty states, not "Failed to fetch".

5. **Optional: ML and Explain**  
   For full fraud scoring and explanations, start the ML and Explain services (see `docker-compose.yml` or their own README). If they are down, the backend may return 503 for predict/explain but health and data endpoints (GNN, anomaly, dashboard) still work.

## Quick checklist

- [ ] Backend running: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` in `backend/`
- [ ] Frontend env: `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend_file/frontend/.env.local`
- [ ] Frontend running: `npm run dev` in `frontend_file/frontend/`
- [ ] User logged in when opening Dashboard, GNN Detection, or Anomaly Detection
- [ ] (Optional) PostgreSQL, Redis, ML, Explain running if you need full predict/explain

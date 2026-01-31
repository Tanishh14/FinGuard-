# Run FinGuard Backend (no DB)

## Command (from repo root)

```bash
cd backend
uvicorn main:app --reload
```

Or with host/port:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Verify

- Root health: `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`
- API v1 health: `curl http://127.0.0.1:8000/api/v1/health/` → `{"status":"ok"}`
- Swagger: http://127.0.0.1:8000/docs

## Frontend API base

Set in frontend (e.g. `.env.local`):

- `NEXT_PUBLIC_API_URL=http://localhost:8000` (or your backend URL)

Frontend calls:

- `GET http://localhost:8000/health` (root health)
- `GET/POST http://localhost:8000/api/v1/...` (auth, transactions, predict, explain, health)

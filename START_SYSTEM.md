# FinGuard AI - Complete System Startup Guide

## CRITICAL: You MUST log in first!

The system requires authentication. All APIs require a valid JWT token.

## Quick Start (3 Steps)

### 1. Verify All Services Are Running

Check these URLs in your browser:
- Backend: http://localhost:8000/health (should show `{"status":"ok","database":"up"}`)
- ML Service: http://localhost:8001/health
- Explainability: http://localhost:8002/health  
- Frontend: http://localhost:3000 (should show FinGuard AI dashboard)

### 2. LOG IN TO THE FRONTEND

**This is the most important step!**

1. Open http://localhost:3000 in your browser
2. Click the **"Login"** button in the top-right corner (blue button)
3. You will be redirected to http://localhost:3000/login
4. Enter credentials:
   - **Username**: `demo`
   - **Password**: `demo`
5. Click **"Log in"**
6. You will be redirected back to the dashboard

**After login, the system will work!**

### 3. Verify Data Shows Up

After logging in, refresh the page and verify:
- Dashboard shows: **50 total transactions, 3 flagged**
- Navigate to **Live Transactions** page: Shows 50 transactions in table
- Navigate to **GNN Fraud Rings** page: Shows graph with 21 nodes, 20 clusters
- Navigate to **Anomaly Detection** page: Shows 50 anomaly scores with chart

## Why Login Is Required

- The backend enforces JWT authentication on ALL endpoints
- The demo user has 50 transactions in the database
- Without logging in, ALL API calls return 401 Unauthorized
- Frontend cannot load data without authentication

## Demo User Details

- **Username**: demo
- **Password**: demo
- **User ID**: 14072f85-98b1-4d8e-9b2d-4c9209fcc5df
- **Transactions**: 50 (45 normal, 5 suspicious, 3 fraudulent)

## Troubleshooting

### Frontend shows "Backend error" or "API unavailable"

**Solution**: Log in first! Click the "Login" button in the top-right corner.

### After login, still seeing errors

1. Open browser DevTools (F12)
2. Go to Application tab → Local Storage → http://localhost:3000
3. Verify `finguard_token` key exists with a JWT token value
4. If missing, log in again
5. Refresh the page (Ctrl+R or F5)

### "Not authenticated" errors

- Your JWT token may have expired (valid for 7 days)
- Log out and log in again
- Check if localStorage has the token

### No transactions showing in Live Transactions page

- Make sure you're logged in
- The transactions belong to the demo user
- Check Network tab in DevTools to see if API calls are being made with `Authorization: Bearer <token>` header

## Testing New Transaction Submission

After logging in:

1. Go to **Submit Transaction** page
2. Fill in the form with test data:
   - Transaction ID: `test_tx_001`
   - User ID: Can be any UUID format
   - Amount: `500.00`
   - Merchant: `TestMerchant`
   - Device ID: `device_123`
   - IP Address: `192.168.1.100`
3. Click **Submit**
4. The ML service will analyze it and return risk score
5. Go to **Live Transactions** to see your new transaction

## System Architecture

```
Frontend (React/Next.js) :3000
    ↓ (HTTP + JWT Bearer Token)
Backend (FastAPI) :8000
    ↓ (Database queries)
PostgreSQL Database
    ↓ (ML predictions)
ML Service :8001
    ↓ (Explanations)
Explainability Service :8002
```

## API Endpoints (All require Authorization header)

All requests need: `Authorization: Bearer <your_jwt_token>`

- `POST /api/v1/auth/login` - Get JWT token (no auth required)
- `GET /api/v1/dashboard/metrics` - Dashboard summary
- `GET /api/v1/transactions` - List transactions
- `GET /api/v1/transactions/stats/dashboard` - Transaction stats
- `GET /api/v1/gnn/clusters` - GNN graph data
- `GET /api/v1/anomaly/summary` - Anomaly detection data
- `POST /api/v1/predict/fraud` - Submit new transaction for analysis

## Backend Verification (Command Line)

To test backend directly with PowerShell:

```powershell
# Login and get token
$body = @{ username = "demo"; password = "demo" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json"
$token = $response.access_token

# Test transactions endpoint with Python
python -c "import requests; r = requests.get('http://localhost:8000/api/v1/transactions?limit=5', headers={'Authorization': f'Bearer $token'}); print(r.json())"
```

## Success Criteria

After following this guide, you should see:

✅ All 4 services running (Backend, ML, Explainability, Frontend)  
✅ Logged in to frontend with "Logout" button visible  
✅ Dashboard showing 50 transactions, 3 flagged, 8% high risk  
✅ Live Transactions page showing 50 rows in table  
✅ GNN Detection showing graph with nodes and clusters  
✅ Anomaly Detection showing scores and chart  
✅ Can submit new transactions and see them in Live Transactions  
✅ No "Authentication required", "Backend error", or "API unavailable" messages

## Important Notes

- **NO MOCK DATA**: All data comes from real PostgreSQL database
- **REAL ML PREDICTIONS**: ML service uses heuristic scoring based on amount, merchant, device
- **AUTHENTICATION REQUIRED**: You must log in for the system to work
- **Token Expiry**: JWT tokens are valid for 7 days, then you must log in again

---

**REMEMBER**: The #1 reason for errors is **NOT LOGGING IN**. Always log in first!

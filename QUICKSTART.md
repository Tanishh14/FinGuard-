# FinGuard AI - Quick Start Guide

## ✅ Fixed Issues

All authentication, configuration, and connection issues have been resolved:
- ✅ Authentication works with demo user (demo/demo) without database
- ✅ All endpoints return mock data when database is unavailable  
- ✅ Frontend properly configured to connect to backend
- ✅ Environment files created with development settings

## 🚀 Running the Application

### Option 1: Run Backend Only (Recommended for Testing)

1. **Start the Backend Server** (use `app.main:app` for full DB + auth + GNN/anomaly):
   ```powershell
   cd backend
   python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
   ```
   For a minimal API without DB: `uvicorn main:app --reload --port 8000`
   
   Backend will be available at: http://localhost:8000
   API Documentation: http://localhost:8000/docs

### Option 2: Run Backend + Frontend

1. **Start the Backend Server** (in one terminal):
   ```powershell
   cd backend
   python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
   ```

2. **Start the Frontend** (in another terminal):
   ```powershell
   cd frontend_file\frontend
   npm install  # Only needed first time
   npm run dev
   ```
   
   Frontend will be available at: http://localhost:3000

## 🔐 Login Credentials

Use these credentials to log in:
- **Username**: `demo`
- **Password**: `demo`

## 📊 Features Working Without Database

All features now work with mock data when database is not available:
- ✅ **Dashboard**: Shows transaction metrics and statistics
- ✅ **Anomaly Detection**: Displays anomaly scores with sample data
- ✅ **GNN Detection**: Shows graph neural network analysis
- ✅ **Live Transactions**: View transaction list
- ✅ **Submit Transaction**: Analyze individual transactions

## 🔧 Configuration Files Created

The following configuration files have been created:
- `.env` - Root environment configuration
- `backend/.env` - Backend configuration  
- `frontend_file/frontend/.env.local` - Frontend API URL configuration

## 📝 Notes

- The application works **without** requiring:
  - PostgreSQL database
  - Redis cache
  - ML service (port 8001)
  - Explainability service (port 8002)

- Mock data is automatically provided when these services are unavailable
- For full functionality with real data, set up the database and services as described in the main README.md

## 🐛 Troubleshooting

### Backend won't start
- Make sure you have Python 3.8+ installed
- Install dependencies: `pip install -r requirements.txt`
- Check that port 8000 is not in use

### Frontend won't start  
- Make sure you have Node.js 16+ installed
- Delete `node_modules` and `.next` folders, then run `npm install` again
- Check that port 3000 is not in use

### Login doesn't work
- Make sure backend is running on port 8000
- Check browser console for errors
- Try clearing browser cache and cookies

### Pages show errors
- Verify backend is running and accessible
- Check `.env.local` file has correct API URL: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Restart frontend after environment changes

## 🎯 Next Steps

1. Login with demo/demo credentials
2. Explore the dashboard to see metrics
3. Visit Anomaly Detection page
4. Visit GNN Detection page
5. Submit a test transaction

All pages will work with mock data - no database required!

## 📚 Additional Resources

- Full setup with database: See `README.md`
- API documentation: http://localhost:8000/docs (when backend is running)
- Architecture details: See `ARCHITECTURE.md`

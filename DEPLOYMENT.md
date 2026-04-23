# Deployment Guide

This guide covers deploying the Medical Copilot application with:
- **Frontend**: Streamlit Cloud
- **Backend API**: Render

## Prerequisites

1. **Database**: Supabase PostgreSQL (already configured in `.env`)
2. **GitHub Repository**: Push your code to GitHub
3. **Accounts**:
   - [Streamlit Cloud](https://streamlit.io/cloud) (free)
   - [Render](https://render.com) (free tier available)

---

## Part 1: Deploy Backend API to Render

### Step 1: Prepare Your Repository

Ensure these files are in your repository:
- ✅ `api/main.py` - FastAPI backend
- ✅ `requirements.txt` - Python dependencies
- ✅ `render.yaml` - Render configuration
- ✅ `Procfile` - Process configuration
- ✅ `runtime.txt` - Python version

### Step 2: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `medical-copilot-api` (or your choice)
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

### Step 3: Configure Environment Variables

In Render dashboard, add these environment variables:

```
DATABASE_URL=postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require

DATABASE_PUBLIC_URL=postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require

DB_HOST=aws-1-ap-northeast-2.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.zvgrchtdzradiidwoeid
DB_PASSWORD=dbmsprojectc13
DB_SSLMODE=require
PYTHON_VERSION=3.11.0
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Once deployed, note your API URL: `https://medical-copilot-api.onrender.com`

### Step 5: Test Backend

Visit: `https://your-app-name.onrender.com/health`

You should see: `{"status": "ok"}`

Test the API:
```bash
curl -X POST https://medical-copilot-api.onrender.com/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "query": "female patients with fever"}'
```

---

## Part 2: Deploy Frontend to Streamlit Cloud

### Step 1: Prepare Repository

Ensure these files exist:
- ✅ `app.py` - Main Streamlit app
- ✅ `streamlit_app.py` - Entry point for Streamlit Cloud
- ✅ `requirements.txt` - Dependencies
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `.env` - Environment variables (for reference)

### Step 2: Update Frontend to Use Backend API

If you want the frontend to call the backend API (optional), update your code to use the Render API URL.

For now, the frontend connects directly to Supabase, which works fine.

### Step 3: Deploy to Streamlit Cloud

1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Click **"New app"**
3. Configure:
   - **Repository**: Select your GitHub repo
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
4. Click **"Advanced settings"**
5. Add environment variables (copy from `.env`):

```
DATABASE_URL=postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require

DATABASE_PUBLIC_URL=postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require

DB_HOST=aws-1-ap-northeast-2.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.zvgrchtdzradiidwoeid
DB_PASSWORD=dbmsprojectc13
DB_SSLMODE=require
```

6. Click **"Deploy!"**

### Step 4: Wait for Deployment

- Deployment takes 2-5 minutes
- Your app will be available at: `https://your-app-name.streamlit.app`

---

## Part 3: Connect Frontend to Backend (Optional)

If you want the Streamlit frontend to use the Render backend API:

1. Add `BACKEND_API_URL` to Streamlit Cloud secrets:
   ```
   BACKEND_API_URL=https://your-render-app.onrender.com
   ```

2. Update your frontend code to use `requests` to call the API:
   ```python
   import os
   import requests
   
   BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
   
   response = requests.post(
       f"{BACKEND_URL}/api/v1/search",
       json={"user_id": user_id, "query": query}
   )
   results = response.json()
   ```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Users                                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├──────────────────┬─────────────────────────┐
                 │                  │                         │
                 ▼                  ▼                         ▼
    ┌────────────────────┐ ┌──────────────────┐  ┌──────────────────┐
    │  Streamlit Cloud   │ │   Render API     │  │   Supabase DB    │
    │   (Frontend)       │ │   (Backend)      │  │  (PostgreSQL)    │
    │                    │ │                  │  │                  │
    │  - UI/Dashboard    │ │  - FastAPI       │  │  - Patient data  │
    │  - Auth pages      │ │  - Search API    │  │  - Search logs   │
    │  - Direct DB calls │ │  - REST endpoints│  │  - Cohorts       │
    └────────────────────┘ └──────────────────┘  └──────────────────┘
             │                      │                      ▲
             │                      │                      │
             └──────────────────────┴──────────────────────┘
                    Both connect to Supabase
```

---

## Troubleshooting

### Backend Issues

**Problem**: API returns 500 error
- Check Render logs: Dashboard → Your Service → Logs
- Verify environment variables are set correctly
- Test database connection

**Problem**: Slow cold starts
- Render free tier spins down after inactivity
- First request after idle takes 30-60 seconds
- Consider upgrading to paid tier for always-on

### Frontend Issues

**Problem**: App won't start
- Check Streamlit Cloud logs
- Verify `streamlit_app.py` exists
- Check `requirements.txt` has all dependencies

**Problem**: Database connection fails
- Verify environment variables in Streamlit Cloud secrets
- Check Supabase connection pooler is accessible
- Test connection string locally first

### Database Issues

**Problem**: Connection timeout
- Supabase pooler may have connection limits
- Check Supabase dashboard for active connections
- Consider connection pooling settings

---

## Monitoring

### Backend (Render)
- Dashboard: https://dashboard.render.com
- Logs: Real-time in dashboard
- Metrics: CPU, Memory, Request count

### Frontend (Streamlit Cloud)
- Dashboard: https://share.streamlit.io
- Logs: Available in app settings
- Analytics: Built-in usage stats

### Database (Supabase)
- Dashboard: https://supabase.com/dashboard
- Query performance
- Connection pooling stats

---

## Cost Breakdown

| Service | Plan | Cost | Limits |
|---------|------|------|--------|
| Streamlit Cloud | Free | $0 | 1 app, public repos |
| Render | Free | $0 | 750 hrs/month, sleeps after 15min idle |
| Supabase | Free | $0 | 500MB database, 2GB bandwidth |

**Total**: $0/month for free tier

---

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Deploy frontend to Streamlit Cloud
3. ✅ Test both deployments
4. 🔄 (Optional) Connect frontend to backend API
5. 📊 Monitor usage and performance
6. 🚀 Consider upgrading for production use

---

## Support

- **Streamlit**: https://docs.streamlit.io
- **Render**: https://render.com/docs
- **Supabase**: https://supabase.com/docs
- **FastAPI**: https://fastapi.tiangolo.com

---

## Security Notes

⚠️ **Important**: 
- Never commit `.env` file to Git
- Use environment variables for all secrets
- Rotate database credentials regularly
- Enable SSL/TLS for all connections
- Monitor API usage for anomalies

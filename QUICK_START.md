# 🚀 Quick Start Guide

## Deploy in 15 Minutes

### Step 1: Verify Setup (2 min)
```bash
python verify_deployment.py
```
✅ All checks should pass

### Step 2: Push to GitHub (1 min)
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 3: Deploy Backend to Render (5 min)

1. Go to https://render.com → Sign up/Login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo
4. Fill in:
   - **Name**: `medical-copilot-api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (copy from `.env`):
   ```
   DATABASE_URL=your_database_url
   DB_HOST=your_host
   DB_PORT=5432
   DB_NAME=postgres
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_SSLMODE=require
   ```
6. Click **"Create Web Service"**
7. Wait 5 minutes for deployment
8. Test: Visit `https://your-app.onrender.com/health`

### Step 4: Deploy Frontend to Streamlit Cloud (5 min)

1. Go to https://streamlit.io/cloud → Sign up/Login
2. Click **"New app"**
3. Select your GitHub repo
4. Fill in:
   - **Main file**: `streamlit_app.py`
5. Click **"Advanced settings"**
6. Add secrets in TOML format (paste this exactly):
   ```toml
   DATABASE_URL = "your_database_url"
   DATABASE_PUBLIC_URL = "your_database_url"
   DB_HOST = "your_host"
   DB_PORT = "5432"
   DB_NAME = "postgres"
   DB_USER = "your_user"
   DB_PASSWORD = "your_password"
   DB_SSLMODE = "require"
   ```
   
   **Replace** `your_*` values with your actual credentials from `.env`
7. Click **"Deploy"**
8. Wait 3 minutes
9. Test: Visit your app URL

### Step 5: Test Everything (2 min)

✅ Backend health: `https://your-app.onrender.com/health`
✅ Frontend loads: `https://your-app.streamlit.app`
✅ Login works
✅ Search works

---

## 🎯 That's It!

Your app is now live on the internet! 🎉

---

## 📱 Share Your App

**Frontend URL**: `https://your-app.streamlit.app`
**Backend API**: `https://your-app.onrender.com`

---

## 🆘 Troubleshooting

### Backend won't start
- Check Render logs
- Verify environment variables
- Test database connection

### Frontend won't start
- Check Streamlit logs
- Verify secrets are set
- Check requirements.txt

### Database connection fails
- Verify Supabase is running
- Check connection string
- Confirm SSL mode is set

---

## 📚 More Help

- **Full Guide**: See `DEPLOYMENT.md`
- **Checklist**: See `DEPLOYMENT_CHECKLIST.md`
- **Summary**: See `DEPLOYMENT_SUMMARY.md`

---

## 💡 Pro Tips

1. **Free tier limits**: Render sleeps after 15min idle
2. **First request**: May take 30-60s after sleep
3. **Logs**: Check dashboards for errors
4. **Updates**: Push to GitHub to auto-deploy
5. **Custom domain**: Available on paid plans

---

## 🎓 What You Deployed

```
Internet
   │
   ├─→ Streamlit Cloud (Frontend)
   │   └─→ User Interface
   │
   ├─→ Render (Backend API)
   │   └─→ FastAPI Endpoints
   │
   └─→ Supabase (Database)
       └─→ PostgreSQL
```

**Total Cost**: $0/month (free tier) 💰

---

**Need help?** Check the full documentation in `DEPLOYMENT.md`

# 🚀 Quick Fix - Query Not Loading

## The Problem
Queries in Streamlit don't load or show "using mock data"

## The Solution
Add backend URL to Streamlit secrets

## 3 Simple Steps

### 1️⃣ Go to Streamlit Cloud
https://share.streamlit.io → Your App → Settings → Secrets

### 2️⃣ Add This Line
```toml
BACKEND_API_URL = "https://medical-copilot-system.onrender.com/api/v1"
```

### 3️⃣ Save
Click Save → Wait 30 seconds → Done!

---

## Copy-Paste This Entire Block

```toml
DATABASE_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"
DATABASE_PUBLIC_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"
DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres.zvgrchtdzradiidwoeid"
DB_PASSWORD = "dbmsprojectc13"
DB_SSLMODE = "require"
BACKEND_API_URL = "https://medical-copilot-system.onrender.com/api/v1"
```

---

## Why This Works

✅ Your backend is deployed and working
✅ Backend tested: 88 patients found
✅ Just needs to be connected to frontend

---

## After Adding

Test with: **"female patients over 60"**

Expected: **88 results** ✅

---

**See ADD_BACKEND_URL.md for detailed step-by-step guide**

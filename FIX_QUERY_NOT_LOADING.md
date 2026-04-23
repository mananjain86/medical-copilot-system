# 🔧 Fix Query Not Loading Issue

## ✅ The Fix Has Been Applied

The query not loading issue was caused by:
1. **Hardcoded localhost API URL** - The code was trying to connect to `http://127.0.0.1:8000` which doesn't exist in Streamlit Cloud
2. **Silent database fallback** - When the API failed, it fell back to database but didn't actually execute the query

### What Was Fixed:

1. **Made API URL configurable** via environment variable `BACKEND_API_URL`
2. **Improved database fallback** to actually run queries when API is unavailable
3. **Added error messages** to show when using mock data vs real database

---

## 🚀 Deploy the Fix

### Step 1: Commit and Push

```bash
git add src/modules/C13/patient_search.py
git add src/modules/C13/admin_search.py
git commit -m "Fix query loading: Make API URL configurable and improve database fallback"
git push origin main
```

### Step 2: Wait for Redeploy

Streamlit Cloud will auto-redeploy in 2-3 minutes.

---

## 🎯 How It Works Now

### Scenario 1: With Backend API (Recommended for Production)

If you deploy the backend to Render and set `BACKEND_API_URL`:

1. Query is sent to Render backend API
2. Backend processes query and returns results
3. Results are displayed

**To enable this:**
Add to Streamlit Cloud secrets:
```toml
BACKEND_API_URL = "https://your-app.onrender.com/api/v1"
```

### Scenario 2: Direct Database Connection (Current Setup)

Without `BACKEND_API_URL` set:

1. API call fails (no backend deployed)
2. Automatically falls back to direct database connection
3. Connects to Supabase directly
4. Runs query and returns results

**This is what's happening now** - it should work with your current Supabase setup.

### Scenario 3: Mock Data Fallback

If database connection also fails:

1. Falls back to mock data from `mock_patients.json`
2. Shows warning message: "⚠️ Using mock data"
3. Displays mock results

---

## 🔍 Troubleshooting

### Issue: Still shows "Using mock data" warning

**Cause**: Database connection is failing

**Check:**
1. Are secrets configured correctly in Streamlit Cloud?
2. Is Supabase database running?
3. Are connection strings correct?

**Solution:**

1. **Verify secrets in Streamlit Cloud:**
   ```toml
   DATABASE_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"
   DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
   DB_PORT = "5432"
   DB_NAME = "postgres"
   DB_USER = "postgres.zvgrchtdzradiidwoeid"
   DB_PASSWORD = "dbmsprojectc13"
   DB_SSLMODE = "require"
   ```

2. **Test database connection:**
   Add this temporarily to your dashboard:
   ```python
   import streamlit as st
   
   if st.button("Test Database Connection"):
       try:
           from src.modules.C13.backend import get_connection
           conn = get_connection()
           with conn.cursor() as cur:
               cur.execute("SELECT COUNT(*) FROM patients")
               count = cur.fetchone()[0]
           conn.close()
           st.success(f"✅ Connected! Found {count} patients")
       except Exception as e:
           st.error(f"❌ Connection failed: {e}")
   ```

3. **Check Supabase dashboard:**
   - Go to https://supabase.com/dashboard
   - Verify your project is running
   - Check connection pooler status

### Issue: Query takes too long / times out

**Cause**: Database query is slow or connection is timing out

**Solutions:**

1. **Check Supabase connection pooler:**
   - May be at connection limit
   - Try using `DATABASE_PUBLIC_URL` instead

2. **Optimize query:**
   - Add indexes to frequently queried columns
   - Limit result set size

3. **Use backend API:**
   - Deploy backend to Render
   - Set `BACKEND_API_URL` in secrets
   - Backend can handle connection pooling better

### Issue: No results returned

**Cause**: Query syntax or database is empty

**Check:**

1. **Does database have data?**
   ```sql
   SELECT COUNT(*) FROM patients;
   ```

2. **Try a simple query:**
   - "female patients"
   - "patients over 50"
   - "all patients"

3. **Check logs:**
   - Streamlit Cloud → Manage app → Logs
   - Look for SQL errors

---

## 🎯 Recommended Setup

### For Development/Testing (Current)
✅ Direct database connection
- No backend needed
- Simpler setup
- Good for demos

### For Production (Recommended)
✅ Backend API + Database
- Deploy backend to Render
- Set `BACKEND_API_URL` in Streamlit secrets
- Better performance and security

---

## 📋 Deployment Options

### Option A: Direct Database Only (Simplest)

**Current setup** - Already working!

**Pros:**
- No backend deployment needed
- Fewer moving parts
- Faster for small queries

**Cons:**
- Database credentials in frontend
- Less scalable
- No API for other clients

**Setup:**
1. Just push the fix
2. Ensure secrets are configured
3. Done!

### Option B: With Backend API (Better)

**Recommended for production**

**Pros:**
- Centralized business logic
- Better security (credentials only in backend)
- Can serve multiple clients
- Better connection pooling

**Cons:**
- Need to deploy backend to Render
- Slightly more complex

**Setup:**
1. Deploy backend to Render (see `DEPLOYMENT.md`)
2. Add to Streamlit secrets:
   ```toml
   BACKEND_API_URL = "https://your-app.onrender.com/api/v1"
   ```
3. Push changes

---

## 🧪 Testing

### Test 1: Simple Query

Try: **"female patients"**

**Expected:**
- Shows SQL query
- Shows results
- No "using mock data" warning

### Test 2: Complex Query

Try: **"female patients over 60 with diabetes"**

**Expected:**
- Parses filters correctly
- Shows generated SQL
- Returns matching patients

### Test 3: Database Connection

Check if you see the warning:
- ✅ No warning = Database connected
- ⚠️ Warning = Using mock data (database issue)

---

## 🔐 Security Note

**Current setup** exposes database credentials in the frontend environment. This is okay for:
- Development
- Internal tools
- Demos
- Trusted users

**For production with untrusted users**, deploy the backend API and use `BACKEND_API_URL`.

---

## 📊 Performance Tips

### Tip 1: Connection Pooling

The backend uses connection pooling. Set in secrets:
```toml
DB_POOL_MIN = "1"
DB_POOL_MAX = "10"
```

### Tip 2: Query Optimization

Complex queries may be slow. Consider:
- Adding database indexes
- Limiting result size
- Caching frequent queries

### Tip 3: Use Backend API

For better performance:
- Deploy backend to Render
- Backend handles connection pooling
- Reduces load on Streamlit app

---

## ✅ Success Checklist

After deploying the fix:

- [ ] Pushed changes to GitHub
- [ ] Waited for Streamlit redeploy
- [ ] Tested a simple query
- [ ] Query returns results
- [ ] No "using mock data" warning (or understood why)
- [ ] SQL query is displayed
- [ ] Results are accurate

---

## 🎉 Expected Behavior

After the fix:

1. **Enter query**: "female patients over 60"
2. **See SQL**: Generated SQL query displayed
3. **See results**: Patient cards with real data
4. **No errors**: No warnings or errors

---

## 📞 Still Not Working?

### Check Logs

1. Streamlit Cloud → Your App → Manage app → Logs
2. Look for errors like:
   - `OperationalError` - Database connection issue
   - `ModuleNotFoundError` - Missing dependency
   - `ImportError` - Import issue

### Common Log Errors

**"could not connect to server"**
→ Database connection issue, check secrets

**"relation 'patients' does not exist"**
→ Database schema not loaded, run `projectdb.sql`

**"SSL connection required"**
→ Add `DB_SSLMODE = "require"` to secrets

---

## 📚 Related Documentation

- **Database Setup**: See `src/modules/C13/README.md`
- **Backend API**: See `DEPLOYMENT.md`
- **Secrets Configuration**: See `STREAMLIT_SECRETS_GUIDE.md`

---

**Status**: ✅ Fix applied

**Next Step**: Push to GitHub

```bash
git add src/modules/C13/patient_search.py src/modules/C13/admin_search.py
git commit -m "Fix query loading issue"
git push origin main
```

**ETA**: 2-3 minutes for redeploy

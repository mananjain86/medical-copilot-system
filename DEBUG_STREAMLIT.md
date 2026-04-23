# Debugging Streamlit Blank Page Issue

## 🐛 Common Causes of Blank Page

### 1. Import Errors
The app can't import required modules.

### 2. Missing Secrets
Environment variables not configured.

### 3. Database Connection Failure
Can't connect to Supabase.

### 4. Python Version Mismatch
Wrong Python version.

### 5. Missing Dependencies
Packages not installed.

---

## 🔍 How to Debug

### Step 1: Check Streamlit Cloud Logs

1. Go to https://share.streamlit.io
2. Click on your app
3. Click **"Manage app"** (bottom right)
4. Click **"Logs"**

**Look for errors like:**
```
ModuleNotFoundError: No module named 'psycopg2'
ImportError: cannot import name 'login_page'
OperationalError: could not connect to server
```

### Step 2: Check Secrets Configuration

1. Go to app Settings → Secrets
2. Verify all secrets are present:

```toml
DATABASE_URL = "postgresql://..."
DATABASE_PUBLIC_URL = "postgresql://..."
DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres.zvgrchtdzradiidwoeid"
DB_PASSWORD = "dbmsprojectc13"
DB_SSLMODE = "require"
```

### Step 3: Verify File Structure

Make sure these files exist in your GitHub repo:
- ✅ `streamlit_app.py`
- ✅ `app.py`
- ✅ `requirements.txt`
- ✅ `auth/login.py`
- ✅ `auth/signup.py`
- ✅ `dashboards/patient_dashboard.py`
- ✅ `dashboards/doctor_dashboard.py`
- ✅ `dashboards/admin_dashboard.py`

### Step 4: Check Requirements.txt

Verify `requirements.txt` has all dependencies:
```
streamlit
streamlit-option-menu
matplotlib
psycopg2-binary
python-dotenv
pandas
fastapi
uvicorn
pydantic
requests
```

---

## 🔧 Quick Fixes

### Fix 1: Update streamlit_app.py

The file has been updated to properly import all components. Push the changes:

```bash
git add streamlit_app.py
git commit -m "Fix streamlit_app.py entry point"
git push origin main
```

Streamlit will auto-redeploy in 2-3 minutes.

### Fix 2: Add Error Handling

If you want to see errors on the page, temporarily add this to the top of `streamlit_app.py`:

```python
import streamlit as st
import traceback

try:
    # Your existing code here
    from auth.login import login_page
    # ... rest of imports
except Exception as e:
    st.error(f"Error loading app: {e}")
    st.code(traceback.format_exc())
    st.stop()
```

### Fix 3: Test Locally First

Before deploying, test locally:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the app
streamlit run streamlit_app.py --server.port 8501
```

If it works locally but not in cloud, it's likely a secrets/environment issue.

### Fix 4: Verify Secrets Format

Run the conversion script again:

```bash
python convert_env_to_toml.py
```

Copy the EXACT output and paste into Streamlit Cloud secrets.

### Fix 5: Check Python Version

In Streamlit Cloud settings:
- Python version should be **3.11** or **3.10**
- Match the version in `runtime.txt`

---

## 📋 Debugging Checklist

Go through this checklist:

- [ ] Pushed latest code to GitHub
- [ ] `streamlit_app.py` exists and is correct
- [ ] All imports work locally
- [ ] Secrets are configured in TOML format
- [ ] All secrets have quotes: `key = "value"`
- [ ] `requirements.txt` has all dependencies
- [ ] Python version matches `runtime.txt`
- [ ] Checked Streamlit Cloud logs for errors
- [ ] Database connection string is correct
- [ ] Supabase database is running

---

## 🚨 Most Common Issues

### Issue 1: "This app has encountered an error"

**Cause**: Import error or missing dependency

**Solution**:
1. Check logs for the specific error
2. Add missing package to `requirements.txt`
3. Push to GitHub

### Issue 2: Blank white page, no error

**Cause**: `streamlit_app.py` not executing properly

**Solution**:
1. Use the updated `streamlit_app.py` (already fixed)
2. Push changes to GitHub
3. Wait for auto-redeploy

### Issue 3: "Secrets not found"

**Cause**: Secrets not configured or wrong format

**Solution**:
1. Run `python convert_env_to_toml.py`
2. Copy output to Streamlit Cloud secrets
3. Save and reboot app

### Issue 4: Database connection timeout

**Cause**: Wrong connection string or Supabase down

**Solution**:
1. Verify `DATABASE_URL` in secrets
2. Check Supabase dashboard
3. Test connection locally first

---

## 🔬 Advanced Debugging

### Enable Debug Mode

Add this to the top of `streamlit_app.py`:

```python
import streamlit as st
import os

# Show debug info
st.sidebar.write("Debug Info:")
st.sidebar.write(f"Python: {os.sys.version}")
st.sidebar.write(f"Streamlit: {st.__version__}")

# Check secrets
try:
    st.sidebar.write(f"DB_HOST: {st.secrets['DB_HOST']}")
    st.sidebar.success("✅ Secrets loaded")
except Exception as e:
    st.sidebar.error(f"❌ Secrets error: {e}")
```

### Test Database Connection

Add this temporarily:

```python
import streamlit as st

st.title("Database Connection Test")

try:
    from src.modules.C13.backend import get_connection
    
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        result = cur.fetchone()
    conn.close()
    
    st.success("✅ Database connection successful!")
except Exception as e:
    st.error(f"❌ Database connection failed: {e}")
    import traceback
    st.code(traceback.format_exc())
```

---

## 📞 Get Help

### Check Logs First
Always check Streamlit Cloud logs before asking for help. The error message will tell you exactly what's wrong.

### Common Log Messages

**"ModuleNotFoundError"**
→ Add missing package to `requirements.txt`

**"OperationalError: could not connect"**
→ Check database secrets

**"FileNotFoundError"**
→ File missing from GitHub repo

**"Invalid TOML"**
→ Fix secrets format

---

## ✅ Solution Summary

The blank page issue has been fixed by updating `streamlit_app.py` to properly import and execute all components.

**Next steps:**

1. **Push the fix:**
   ```bash
   git add streamlit_app.py
   git commit -m "Fix blank page issue"
   git push origin main
   ```

2. **Wait for redeploy** (2-3 minutes)

3. **Check logs** if still blank

4. **Verify secrets** are configured correctly

5. **Test locally** if issues persist

---

**Most likely cause**: The original `streamlit_app.py` wasn't executing the app code properly. The updated version now includes all the necessary code directly.

**Status**: ✅ FIXED - Push changes to GitHub

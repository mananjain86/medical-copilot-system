# Streamlit Cloud Secrets Guide

## 🔑 The TOML Format Issue - SOLVED

Streamlit Cloud requires secrets in **TOML format**, not the standard `.env` format.

### ❌ Wrong Format (Standard .env)
```
DATABASE_URL=postgresql://user:pass@host:5432/db
DB_HOST=host.supabase.com
DB_PORT=5432
```

### ✅ Correct Format (TOML)
```toml
DATABASE_URL = "postgresql://user:pass@host:5432/db"
DB_HOST = "host.supabase.com"
DB_PORT = "5432"
```

**Key Differences:**
1. Add spaces around `=` (optional but recommended)
2. **Wrap all values in double quotes** `"value"`
3. Keep the same key names

---

## 🚀 Quick Solution

### Method 1: Use the Conversion Script (Easiest)

```bash
python convert_env_to_toml.py
```

This will:
1. Read your `.env` file
2. Convert it to TOML format
3. Display the output to copy

Then just **copy and paste** the output into Streamlit Cloud!

### Method 2: Manual Conversion

Copy this template and replace the values:

```toml
# Streamlit Cloud Secrets
DATABASE_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

DATABASE_PUBLIC_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres.zvgrchtdzradiidwoeid"
DB_PASSWORD = "dbmsprojectc13"
DB_SSLMODE = "require"
```

---

## 📝 Step-by-Step Instructions

### Step 1: Generate TOML Format

Run the conversion script:
```bash
python convert_env_to_toml.py
```

### Step 2: Copy the Output

Copy everything between the dashed lines:
```
------------------------------------------------------------
DATABASE_URL = "your_value"
DB_HOST = "your_value"
...
------------------------------------------------------------
```

### Step 3: Paste into Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click on your app (or create new app)
3. Click **Settings** (⚙️ icon)
4. Click **Secrets** in the left sidebar
5. **Paste** the TOML content
6. Click **Save**

### Step 4: Verify

Your secrets section should look like this:

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

---

## 🔍 Common Errors & Fixes

### Error: "Invalid TOML format"

**Cause**: Missing quotes around values

❌ Wrong:
```toml
DB_PORT = 5432
```

✅ Correct:
```toml
DB_PORT = "5432"
```

### Error: "Unexpected character"

**Cause**: Special characters not properly escaped in URLs

❌ Wrong:
```toml
DATABASE_URL = postgresql://user:pass@host/db
```

✅ Correct:
```toml
DATABASE_URL = "postgresql://user:pass@host/db"
```

### Error: "Key already defined"

**Cause**: Duplicate keys in secrets

**Fix**: Remove duplicate lines, keep only one of each key

### Error: "Empty value"

**Cause**: Missing value after `=`

❌ Wrong:
```toml
DB_HOST = 
```

✅ Correct:
```toml
DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
```

---

## 🧪 Testing Your Secrets

After adding secrets, test them in your Streamlit app:

```python
import streamlit as st

# Access secrets
st.write("Testing secrets...")
st.write(f"DB_HOST: {st.secrets['DB_HOST']}")
st.write(f"DB_PORT: {st.secrets['DB_PORT']}")
st.write(f"DB_NAME: {st.secrets['DB_NAME']}")

# Don't display passwords!
st.write(f"DB_PASSWORD: {'*' * len(st.secrets['DB_PASSWORD'])}")
```

---

## 📋 Complete Example

Here's the complete TOML format for your project:

```toml
# Supabase Database Configuration
DATABASE_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

DATABASE_PUBLIC_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

# Connection Parameters
DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres.zvgrchtdzradiidwoeid"
DB_PASSWORD = "dbmsprojectc13"
DB_SSLMODE = "require"

# Connection Pool Settings (Optional)
DB_POOL_MIN = "1"
DB_POOL_MAX = "10"

# Backend API URL (Optional - only if using separate backend)
# BACKEND_API_URL = "https://your-app.onrender.com"
```

---

## 🔐 Security Best Practices

1. **Never commit secrets to Git**
   - `.env` is in `.gitignore` ✅
   - `secrets.toml` is in `.gitignore` ✅

2. **Use environment-specific secrets**
   - Development: Local `.env` file
   - Production: Streamlit Cloud secrets

3. **Rotate credentials regularly**
   - Update Supabase password
   - Update Streamlit secrets
   - Update Render environment variables

4. **Limit access**
   - Only share secrets with team members who need them
   - Use Streamlit Cloud's team features for collaboration

---

## 🛠️ Troubleshooting Checklist

- [ ] All values are wrapped in double quotes `"value"`
- [ ] No duplicate keys
- [ ] No empty values
- [ ] Special characters in URLs are inside quotes
- [ ] No trailing spaces or newlines
- [ ] Saved the secrets in Streamlit Cloud
- [ ] Restarted the app after saving secrets

---

## 📚 Additional Resources

- [Streamlit Secrets Documentation](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [TOML Format Specification](https://toml.io/en/)
- [Supabase Connection Strings](https://supabase.com/docs/guides/database/connecting-to-postgres)

---

## 🆘 Still Having Issues?

1. **Check Streamlit Cloud logs**
   - Dashboard → Your App → Logs
   - Look for secret-related errors

2. **Verify secret names**
   - Make sure your code uses the same key names
   - Example: `st.secrets["DB_HOST"]` matches `DB_HOST = "..."`

3. **Test locally first**
   - Create `.streamlit/secrets.toml` locally
   - Test with `streamlit run app.py`
   - If it works locally, it should work in cloud

4. **Contact support**
   - Streamlit Community: https://discuss.streamlit.io
   - Check status: https://status.streamlit.io

---

## ✅ Success Checklist

After following this guide, you should have:

- [ ] Converted `.env` to TOML format
- [ ] Pasted secrets into Streamlit Cloud
- [ ] Saved the secrets
- [ ] App deployed successfully
- [ ] Database connection working
- [ ] No errors in logs

---

**Last Updated**: April 24, 2026
**Issue**: TOML format error in Streamlit Cloud secrets
**Status**: ✅ RESOLVED

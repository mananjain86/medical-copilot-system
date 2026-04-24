# Configure Streamlit to Use Render Backend

## Add to Streamlit Cloud Secrets

Go to your Streamlit Cloud app → Settings → Secrets and add:

```toml
# Existing database secrets
DATABASE_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"
DATABASE_PUBLIC_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"
DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres.zvgrchtdzradiidwoeid"
DB_PASSWORD = "dbmsprojectc13"
DB_SSLMODE = "require"

# Add this line for backend API
BACKEND_API_URL = "https://medical-copilot-system.onrender.com/api/v1"
```

## What This Does

With `BACKEND_API_URL` set:
1. Search queries will go through your Render backend API
2. Backend handles all database connections
3. Better performance and security
4. Centralized business logic

## Test Results

Your backend at `https://medical-copilot-system.onrender.com` is working:

✅ Health check: OK
✅ Patient search: Returns results (88 patients found for "female patients over 60")
✅ Search history: Working
✅ Cohorts: 7 cohorts available

## Without BACKEND_API_URL

If you don't set it:
- Streamlit connects directly to database
- Still works fine
- Slightly less secure (credentials in frontend)

## Recommendation

**Add the BACKEND_API_URL** - Your backend is deployed and working perfectly!

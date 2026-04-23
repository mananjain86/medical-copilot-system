# Deployment Guide

Deploy your Medical Copilot application with frontend on Streamlit Cloud and backend on Render.

## Quick Start

### 1. Convert Secrets to TOML Format

```bash
python convert_env_to_toml.py
```

Copy the output - you'll need it for Streamlit Cloud.

### 2. Push to GitHub

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 3. Deploy Backend to Render (Optional)

1. Go to https://render.com
2. Create **New Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env`
6. Click **Deploy**

### 4. Deploy Frontend to Streamlit Cloud

1. Go to https://streamlit.io/cloud
2. Click **New app**
3. Select your repository
4. Configure:
   - **Main file path**: `streamlit_app.py`
5. Click **Advanced settings**
6. In **Secrets**, paste the TOML output from step 1
7. Click **Deploy**

---

## Troubleshooting

### Blank Page
- Check Streamlit Cloud logs
- Verify secrets are configured
- Ensure all files are in GitHub

### TOML Format Error
- Run `python convert_env_to_toml.py`
- Use exact output in Streamlit secrets
- All values must be in quotes: `key = "value"`

### Query Not Loading
- Check for "Using mock data" warning
- Verify database secrets
- Test connection locally

### Database Connection Error
- Verify `DATABASE_URL` in secrets
- Check `DB_SSLMODE = "require"` is set
- Confirm Supabase is running

---

## Files Overview

**Required:**
- `streamlit_app.py` - Entry point
- `requirements.txt` - Dependencies
- `Procfile` - Render config
- `runtime.txt` - Python version

**Utilities:**
- `convert_env_to_toml.py` - Convert secrets
- `verify_deployment.py` - Pre-deployment checks
- `test_local.sh` - Local testing

---

## Cost

| Service | Free | Paid |
|---------|------|------|
| Streamlit | $0 | $20/mo |
| Render | $0 | $7/mo |
| Supabase | $0 | $25/mo |

---

## Support

- Streamlit: https://docs.streamlit.io
- Render: https://render.com/docs
- Supabase: https://supabase.com/docs

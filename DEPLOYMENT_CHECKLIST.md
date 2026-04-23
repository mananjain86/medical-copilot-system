# Deployment Checklist

Use this checklist to ensure smooth deployment of your Medical Copilot application.

## Pre-Deployment

- [ ] Code is pushed to GitHub repository
- [ ] `.env` file is NOT committed (check `.gitignore`)
- [ ] Database is set up on Supabase with schema loaded
- [ ] All dependencies are in `requirements.txt`
- [ ] Local testing completed successfully

## Backend Deployment (Render)

- [ ] Create Render account at https://render.com
- [ ] Create new Web Service
- [ ] Connect GitHub repository
- [ ] Set build command: `pip install -r requirements.txt`
- [ ] Set start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- [ ] Add all environment variables from `.env`:
  - [ ] `DATABASE_URL`
  - [ ] `DATABASE_PUBLIC_URL`
  - [ ] `DB_HOST`
  - [ ] `DB_PORT`
  - [ ] `DB_NAME`
  - [ ] `DB_USER`
  - [ ] `DB_PASSWORD`
  - [ ] `DB_SSLMODE`
- [ ] Deploy and wait for build to complete
- [ ] Test health endpoint: `https://your-app.onrender.com/health`
- [ ] Test search endpoint with curl or Postman
- [ ] Note down your Render API URL

## Frontend Deployment (Streamlit Cloud)

- [ ] Create Streamlit Cloud account at https://streamlit.io/cloud
- [ ] Click "New app"
- [ ] Select your GitHub repository
- [ ] Set main file path: `streamlit_app.py`
- [ ] Click "Advanced settings"
- [ ] Add environment variables (Secrets):
  - [ ] `DATABASE_URL`
  - [ ] `DATABASE_PUBLIC_URL`
  - [ ] `DB_HOST`
  - [ ] `DB_PORT`
  - [ ] `DB_NAME`
  - [ ] `DB_USER`
  - [ ] `DB_PASSWORD`
  - [ ] `DB_SSLMODE`
- [ ] (Optional) Add `BACKEND_API_URL` if using Render backend
- [ ] Click "Deploy"
- [ ] Wait for deployment (2-5 minutes)
- [ ] Test the application in browser
- [ ] Note down your Streamlit app URL

## Post-Deployment Testing

- [ ] Frontend loads without errors
- [ ] Login/signup functionality works
- [ ] Patient search returns results
- [ ] Dashboard displays correctly
- [ ] All navigation works
- [ ] Database queries execute successfully
- [ ] No console errors in browser
- [ ] Backend API responds correctly (if using separate backend)

## Optional: Connect Frontend to Backend API

If you want Streamlit to use the Render backend instead of direct DB access:

- [ ] Add `BACKEND_API_URL` to Streamlit secrets
- [ ] Update frontend code to use `requests` library
- [ ] Test API integration
- [ ] Verify CORS settings in FastAPI

## Documentation

- [ ] Update README.md with deployment URLs
- [ ] Document any deployment-specific configurations
- [ ] Add monitoring/logging setup instructions
- [ ] Share access with team members

## Monitoring Setup

- [ ] Set up Render dashboard monitoring
- [ ] Enable Streamlit analytics
- [ ] Configure Supabase alerts
- [ ] Set up uptime monitoring (optional)

## Security Review

- [ ] Verify no secrets in Git history
- [ ] Check environment variables are set correctly
- [ ] Confirm SSL/TLS is enabled
- [ ] Review CORS settings
- [ ] Test authentication flows
- [ ] Verify database connection uses SSL

## Performance Optimization

- [ ] Test cold start time on Render (free tier)
- [ ] Monitor database connection pool
- [ ] Check Streamlit app load time
- [ ] Optimize slow queries if needed

## Troubleshooting

If something goes wrong:

1. **Check logs**:
   - Render: Dashboard → Your Service → Logs
   - Streamlit: App settings → Logs
   - Supabase: Dashboard → Logs

2. **Verify environment variables**:
   - All variables are set
   - No typos in variable names
   - Values are correct

3. **Test database connection**:
   - Use Supabase SQL editor
   - Check connection pooler status
   - Verify SSL mode

4. **Common issues**:
   - Cold start delays (Render free tier)
   - Connection timeouts (check pooler)
   - Import errors (check requirements.txt)
   - CORS errors (check FastAPI middleware)

## Success Criteria

✅ Backend API is accessible and returns data
✅ Frontend loads and displays correctly
✅ Users can log in and search patients
✅ Database queries execute without errors
✅ No critical errors in logs
✅ Application is publicly accessible

---

## Quick Links

- **Render Dashboard**: https://dashboard.render.com
- **Streamlit Cloud**: https://share.streamlit.io
- **Supabase Dashboard**: https://supabase.com/dashboard
- **GitHub Repository**: [Your repo URL]
- **Deployed Frontend**: [Your Streamlit URL]
- **Deployed Backend**: [Your Render URL]

---

## Support Resources

- Render Docs: https://render.com/docs
- Streamlit Docs: https://docs.streamlit.io
- Supabase Docs: https://supabase.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com

---

**Last Updated**: [Date]
**Deployed By**: [Your Name]

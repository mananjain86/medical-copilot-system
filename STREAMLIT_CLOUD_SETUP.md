# Streamlit Cloud Setup - Visual Guide

## 🎯 Complete Setup in 5 Minutes

This guide walks you through deploying to Streamlit Cloud with screenshots descriptions.

---

## Step 1: Prepare Your Secrets (2 minutes)

### Generate TOML Format

```bash
python convert_env_to_toml.py
```

**Output will look like:**
```toml
DATABASE_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"
DATABASE_PUBLIC_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"
DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres.zvgrchtdzradiidwoeid"
DB_PASSWORD = "dbmsprojectc13"
DB_SSLMODE = "require"
```

**Copy this entire output** - you'll need it in Step 3.

---

## Step 2: Create New App (1 minute)

### 2.1 Go to Streamlit Cloud
Visit: https://share.streamlit.io

### 2.2 Sign In
- Click **"Sign in"** (top right)
- Use GitHub account (recommended)
- Authorize Streamlit to access your repositories

### 2.3 Create New App
- Click **"New app"** button (top right)
- Or click **"Create app"** if this is your first app

---

## Step 3: Configure Your App (2 minutes)

### 3.1 Repository Settings

**You'll see a form with these fields:**

```
┌─────────────────────────────────────────────┐
│ Repository                                   │
│ ┌─────────────────────────────────────────┐ │
│ │ your-username/medical-copilot-system    │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ Branch                                       │
│ ┌─────────────────────────────────────────┐ │
│ │ main                                     │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ Main file path                               │
│ ┌─────────────────────────────────────────┐ │
│ │ streamlit_app.py                        │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ App URL (optional)                           │
│ ┌─────────────────────────────────────────┐ │
│ │ medical-copilot                         │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Fill in:**
- **Repository**: Select `your-username/medical-copilot-system`
- **Branch**: `main` (or `master`)
- **Main file path**: `streamlit_app.py` ⚠️ Important!
- **App URL**: Choose a custom name (optional)

### 3.2 Advanced Settings

**Click "Advanced settings" button** at the bottom

You'll see additional options:

```
┌─────────────────────────────────────────────┐
│ Python version                               │
│ ┌─────────────────────────────────────────┐ │
│ │ 3.11                                     │ │
│ └─────────────────────────────────────────┘ │
│                                              │
│ Secrets                                      │
│ ┌─────────────────────────────────────────┐ │
│ │                                          │ │
│ │  [Paste your TOML secrets here]         │ │
│ │                                          │ │
│ │                                          │ │
│ │                                          │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**In the Secrets box, paste:**

```toml
DATABASE_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

DATABASE_PUBLIC_URL = "postgresql://postgres.zvgrchtdzradiidwoeid:dbmsprojectc13@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

DB_HOST = "aws-1-ap-northeast-2.pooler.supabase.com"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres.zvgrchtdzradiidwoeid"
DB_PASSWORD = "dbmsprojectc13"
DB_SSLMODE = "require"
```

⚠️ **Critical**: 
- Use the output from `convert_env_to_toml.py`
- All values MUST be in quotes: `key = "value"`
- No syntax errors or the deployment will fail

### 3.3 Deploy

Click **"Deploy!"** button at the bottom

---

## Step 4: Wait for Deployment (2-3 minutes)

### 4.1 Deployment Progress

You'll see a screen like:

```
┌─────────────────────────────────────────────┐
│ 🚀 Deploying your app...                    │
│                                              │
│ ⏳ Installing dependencies                   │
│ ⏳ Starting app                              │
│                                              │
│ [Progress bar]                               │
└─────────────────────────────────────────────┘
```

**This takes 2-3 minutes**

### 4.2 Logs

You can view real-time logs:

```
Installing dependencies...
✓ streamlit
✓ psycopg2-binary
✓ fastapi
✓ pandas
...
Starting app...
✓ App is running!
```

### 4.3 Success!

When done, you'll see:

```
┌─────────────────────────────────────────────┐
│ ✅ Your app is live!                        │
│                                              │
│ 🌐 https://medical-copilot.streamlit.app   │
│                                              │
│ [Visit app] [Share] [Settings]              │
└─────────────────────────────────────────────┘
```

---

## Step 5: Test Your App (1 minute)

### 5.1 Visit Your App

Click **"Visit app"** or go to your URL:
`https://your-app-name.streamlit.app`

### 5.2 Test Features

✅ App loads without errors
✅ Login page appears
✅ Can create account
✅ Can log in
✅ Dashboard loads
✅ Patient search works
✅ No error messages

---

## 🔧 Managing Your App

### Access Settings

After deployment, you can manage your app:

1. Go to https://share.streamlit.io
2. Click on your app
3. Click **Settings** (⚙️ icon)

### Settings Menu

```
┌─────────────────────────────────────────────┐
│ Settings                                     │
│                                              │
│ ├─ General                                   │
│ ├─ Secrets          ← Update secrets here   │
│ ├─ Resources                                 │
│ ├─ Sharing                                   │
│ └─ Delete app                                │
└─────────────────────────────────────────────┘
```

### Update Secrets

1. Click **"Secrets"**
2. Edit the TOML content
3. Click **"Save"**
4. App will automatically restart

### View Logs

1. Click **"Manage app"** (bottom right of your app)
2. Click **"Logs"**
3. See real-time application logs

### Reboot App

If your app is stuck:
1. Click **"Manage app"**
2. Click **"Reboot app"**
3. Wait 30 seconds

---

## 🐛 Common Issues & Solutions

### Issue 1: "Invalid TOML format"

**Error message:**
```
Error: Invalid TOML format in secrets
```

**Solution:**
1. Run `python convert_env_to_toml.py` again
2. Copy the EXACT output
3. Paste into Streamlit secrets
4. Make sure all values have quotes: `key = "value"`

### Issue 2: "Module not found"

**Error message:**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solution:**
1. Check `requirements.txt` has all dependencies
2. Make sure it includes `psycopg2-binary`
3. Push changes to GitHub
4. Streamlit will auto-redeploy

### Issue 3: "Database connection failed"

**Error message:**
```
OperationalError: could not connect to server
```

**Solution:**
1. Verify secrets are correct in Streamlit Cloud
2. Check Supabase is running
3. Test connection string locally first
4. Make sure `DB_SSLMODE = "require"` is set

### Issue 4: "App is sleeping"

**Message:**
```
Your app is waking up...
```

**This is normal!**
- Free tier apps sleep after inactivity
- First request takes 30-60 seconds
- Subsequent requests are fast
- Upgrade to paid tier for always-on

### Issue 5: "File not found: streamlit_app.py"

**Error message:**
```
FileNotFoundError: streamlit_app.py
```

**Solution:**
1. Make sure `streamlit_app.py` exists in your repo
2. Check the "Main file path" setting
3. Should be `streamlit_app.py` not `app.py`
4. Push to GitHub if file is missing

---

## 📊 Monitoring Your App

### Analytics Dashboard

Streamlit Cloud provides built-in analytics:

1. Go to https://share.streamlit.io
2. Click on your app
3. View metrics:
   - **Viewers**: Number of users
   - **Views**: Page views
   - **Uptime**: App availability
   - **Errors**: Error count

### Usage Limits (Free Tier)

```
┌─────────────────────────────────────────────┐
│ Free Tier Limits                             │
│                                              │
│ ✓ 1 private app                              │
│ ✓ Unlimited public apps                      │
│ ✓ 1 GB RAM per app                           │
│ ✓ 1 CPU core per app                         │
│ ✓ Community support                          │
│                                              │
│ ⚠️ Apps sleep after 7 days of inactivity    │
└─────────────────────────────────────────────┘
```

---

## 🎓 Pro Tips

### Tip 1: Auto-Deploy on Push

Streamlit Cloud automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Your app will automatically update in 2-3 minutes!

### Tip 2: Use Branches for Testing

Create a test deployment:
1. Create branch: `git checkout -b test`
2. Deploy separate app from `test` branch
3. Test changes before merging to `main`

### Tip 3: Share Your App

Click **"Share"** button to get:
- Direct link
- Embed code
- Social media links

### Tip 4: Custom Domain (Paid)

Upgrade to use your own domain:
- `app.yourdomain.com` instead of
- `your-app.streamlit.app`

### Tip 5: Monitor Logs

Keep logs open during first deployment:
- Catch errors early
- See what's happening
- Debug issues faster

---

## ✅ Deployment Checklist

Before clicking "Deploy":

- [ ] Repository is pushed to GitHub
- [ ] `streamlit_app.py` exists in repo
- [ ] `requirements.txt` is complete
- [ ] Secrets are in TOML format
- [ ] All values are in quotes
- [ ] No syntax errors in secrets
- [ ] Database credentials are correct

After deployment:

- [ ] App loads successfully
- [ ] No errors in logs
- [ ] Login works
- [ ] Database connection works
- [ ] All features functional

---

## 🆘 Need More Help?

### Documentation
- [Streamlit Docs](https://docs.streamlit.io)
- [Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud)
- [Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

### Community
- [Streamlit Forum](https://discuss.streamlit.io)
- [GitHub Issues](https://github.com/streamlit/streamlit/issues)
- [Discord](https://discord.gg/streamlit)

### Status
- [Streamlit Status](https://status.streamlit.io)

---

## 🎉 Success!

Your app is now live on the internet! 

**Share your URL:**
`https://your-app-name.streamlit.app`

**Next steps:**
1. Share with your team
2. Collect feedback
3. Monitor usage
4. Plan improvements

---

**Last Updated**: April 24, 2026
**Status**: Complete deployment guide ✅

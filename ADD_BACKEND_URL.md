# How to Add Backend URL to Streamlit Cloud

## Step-by-Step Instructions

### Step 1: Go to Streamlit Cloud
1. Open your browser
2. Go to: **https://share.streamlit.io**
3. Sign in if needed

### Step 2: Find Your App
1. You'll see a list of your apps
2. Find your **medical-copilot-system** app
3. Click on it

### Step 3: Open Settings
1. Look for the **⚙️ Settings** button (usually top right or in the menu)
2. Click **Settings**

### Step 4: Go to Secrets
1. In the left sidebar, click **"Secrets"**
2. You'll see a text editor with your current secrets

### Step 5: Add Backend URL
Your current secrets look like this:

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

**Add this line at the end:**

```toml
BACKEND_API_URL = "https://medical-copilot-system.onrender.com/api/v1"
```

### Step 6: Complete Secrets Should Look Like This

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

### Step 7: Save
1. Click the **"Save"** button (usually at the bottom)
2. Streamlit will automatically restart your app (takes ~30 seconds)

### Step 8: Test
1. Wait for app to restart
2. Go to your app URL
3. Try a search query like "female patients over 60"
4. Should now load and show results!

---

## Visual Guide

```
┌─────────────────────────────────────────────────────────┐
│  Streamlit Cloud Dashboard                              │
│                                                          │
│  My Apps                                                 │
│  ┌────────────────────────────────────────────────┐    │
│  │  medical-copilot-system                        │    │
│  │  https://your-app.streamlit.app                │    │
│  │                                    [⚙️ Settings] │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                         ↓ Click Settings
┌─────────────────────────────────────────────────────────┐
│  Settings                                                │
│  ┌──────────────┐                                       │
│  │ General      │                                       │
│  │ Secrets      │ ← Click here                         │
│  │ Resources    │                                       │
│  │ Sharing      │                                       │
│  └──────────────┘                                       │
│                                                          │
│  Secrets Editor:                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │ DATABASE_URL = "postgresql://..."              │   │
│  │ DB_HOST = "aws-1-ap-northeast-2..."            │   │
│  │ DB_PORT = "5432"                               │   │
│  │ ...                                            │   │
│  │                                                │   │
│  │ # Add this line:                               │   │
│  │ BACKEND_API_URL = "https://medical-copilot-... │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│                                    [Save]               │
└─────────────────────────────────────────────────────────┘
```

---

## Alternative: Copy-Paste Ready

Just copy this entire block and paste it into Streamlit Secrets:

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

## Troubleshooting

### Can't Find Settings Button
- Look for **⚙️** icon
- Or click the **three dots menu** (⋮) next to your app
- Select "Settings" from dropdown

### Can't Find Secrets
- Make sure you're in the right app
- Secrets is in the left sidebar under Settings
- If you don't see it, you might not have permission

### Save Button Not Working
- Make sure all values are in quotes
- Check for syntax errors (missing quotes, etc.)
- Try refreshing the page

### App Not Restarting
- Click "Reboot app" manually
- Wait 1-2 minutes
- Refresh your app URL

---

## What Happens After Adding

1. **App restarts** (30 seconds)
2. **Queries now go to backend** instead of direct database
3. **Faster performance** (backend handles connections better)
4. **Better reliability** (backend is always running)

---

## Verification

After adding and saving:

1. Go to your app
2. Enter query: "female patients over 60"
3. Should see: **88 results** (we tested this!)
4. No "using mock data" warning
5. Results load quickly

---

## Need Help?

If you're stuck:
1. Take a screenshot of the Secrets page
2. Check that the URL is exactly: `https://medical-copilot-system.onrender.com/api/v1`
3. Make sure there are quotes around the URL
4. Try copying the complete block above

---

**That's it!** Just add one line and save. Your queries will start working! 🚀

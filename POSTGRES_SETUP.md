# PostgreSQL Setup for Streamlit Cloud

Complete guide to deploy Bitcoin EMA Analyzer with full database access on Streamlit Cloud.

## Overview

We're exporting your 4.5M record SQLite database (573MB) to PostgreSQL hosted on **Neon** (free tier: 3GB storage).

---

## Step 1: Export Database (Running Now)

The export script is creating a PostgreSQL-compatible SQL file:

```bash
# This is running in the background
python scripts/export_to_postgres.py
```

**Output:** `data/bitcoin_ohlcv_postgres.sql` (~800MB SQL file)

---

## Step 2: Sign Up for Neon (2 minutes)

1. Go to: **https://console.neon.tech/signup**
2. Sign up with GitHub (same account as Streamlit)
3. Free tier includes:
   - ✅ 3 GB storage (enough for our 573MB database)
   - ✅ Unlimited queries
   - ✅ 1 project
   - ✅ PostgreSQL 16

---

## Step 3: Create Database (1 minute)

1. Click "Create Project"
2. **Project name:** bitcoin-analyzer
3. **Postgres version:** 16 (latest)
4. **Region:** Choose closest to you (e.g., US East for faster access)
5. Click "Create Project"

### Save Your Connection String

You'll see a connection string like:
```
postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require
```

**⚠️ IMPORTANT:** Copy this now! You'll need it for import and Streamlit.

---

## Step 4: Import Data to Neon

### Option A: Using psql (Command Line - Recommended)

```bash
# Install psql if not already installed
# macOS:
brew install postgresql

# Import the data (replace with your connection string)
psql "postgresql://user:pass@host.neon.tech/neondb?sslmode=require" < data/bitcoin_ohlcv_postgres.sql
```

**Time:** ~5-10 minutes for 4.5M rows

### Option B: Using Neon SQL Editor (Smaller Datasets)

⚠️ The SQL editor has a size limit. For our 800MB file, use psql (Option A).

1. In Neon console, go to "SQL Editor"
2. Paste the SQL content
3. Click "Run"

---

## Step 5: Configure Streamlit Cloud (2 minutes)

### Add Database Connection to Streamlit Secrets

1. Go to your Streamlit Cloud dashboard
2. Click your app: **bitcoin-ema-analyzer**
3. Click "⚙️ Settings"
4. Click "Secrets"
5. Add this configuration (replace with your Neon connection string):

```toml
[database]
url = "postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require"
```

6. Click "Save"
7. Click "Reboot app"

---

## Step 6: Deploy Updated Code (1 minute)

The code is already updated to support PostgreSQL! Just push to GitHub:

```bash
git add -A
git commit -m "Add PostgreSQL support for Streamlit Cloud deployment"
git push origin main
```

Streamlit Cloud will auto-deploy with the new changes.

---

## ✅ Verification

After deployment, your Streamlit Cloud app should:

1. ✅ Connect to Neon PostgreSQL
2. ✅ Load 4.5M records
3. ✅ Show full date range (3+ years)
4. ✅ Display all timeframes
5. ✅ Generate charts with real data

---

## 🎯 What Changed

### Code Updates:

1. **`database/connection.py`** - Now supports both SQLite and PostgreSQL
   - Auto-detects database from environment
   - Uses Streamlit secrets when available
   - Falls back to SQLite for local development

2. **`requirements.txt`** - Added `psycopg2-binary`
   - Required for PostgreSQL connection
   - Works on Streamlit Cloud

3. **`scripts/export_to_postgres.py`** - New export tool
   - Converts SQLite → PostgreSQL format
   - Handles 4.5M rows efficiently

### How It Works:

**Local (SQLite):**
- Runs: `streamlit run app.py`
- Uses: `data/bitcoin_ohlcv.db`
- No secrets needed

**Cloud (PostgreSQL):**
- Detects Streamlit secrets
- Uses: Neon PostgreSQL
- Automatic connection

---

## 🔧 Troubleshooting

### "No database found" on Streamlit Cloud

**Check:**
1. Secrets are correctly configured in Streamlit Cloud
2. Connection string includes `?sslmode=require`
3. App was rebooted after adding secrets

### Import takes too long

**Tips:**
- Use psql (much faster than web editor)
- Ensure good internet connection
- Import during off-peak hours

### Connection timeout

**Fix:**
- Check Neon isn't suspended (free tier suspends after 7 days inactive)
- Verify connection string is correct
- Test connection: `psql "YOUR_CONNECTION_STRING" -c "SELECT version();"`

---

## 💰 Cost

**Current Setup:**
- Neon Free Tier: $0/month
- Streamlit Cloud: $0/month
- Total: **$0/month** ✅

**Usage Limits:**
- Storage: 3 GB (we use ~600 MB)
- Compute: 191.9 hours/month active time
- Suspends after 7 days inactive (wakes up automatically)

---

## 📊 After Setup

You'll have:

1. **Streamlit Cloud (Public)**
   - Full functionality with 4.5M records
   - Clean permanent URL
   - Share with anyone
   - Auto-updates with GitHub

2. **Local (Private)**
   - Still works with SQLite
   - No changes needed
   - Faster for personal use

**Best of both worlds!** 🎉

---

## Next Steps

**Right now:**
1. ✅ Export script is running
2. ⏳ Wait for SQL file generation (~5 minutes)
3. 📝 Sign up for Neon
4. 📤 Import data
5. 🔐 Add secrets to Streamlit
6. 🚀 Push to GitHub

**Status will be updated when export completes!**

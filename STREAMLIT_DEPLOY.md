# Deploy to Streamlit Cloud

Your project is ready for deployment! Follow these steps:

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `bitcoin-ema-analyzer` (or your choice)
3. Make it **Public** (required for free Streamlit Cloud)
4. **DO NOT** initialize with README (we already have one)
5. Click "Create repository"

## Step 2: Push Your Code

```bash
# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/bitcoin-ema-analyzer.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Sign in with GitHub (if not already)
4. Authorize Streamlit Cloud
5. Select your repository: `YOUR_USERNAME/bitcoin-ema-analyzer`
6. Main file path: `app.py`
7. Click "Deploy!"

## Step 4: Wait for Deployment

- First deployment takes 2-5 minutes
- Streamlit Cloud will:
  - Install dependencies from `requirements.txt`
  - Run `app.py`
  - Give you a public URL like: `https://your-app.streamlit.app`

## Important Notes

### ⚠️ Database Issue

The SQLite database (`data/bitcoin_ohlcv.db`) is **not included** in the repo (gitignored).

**Two options:**

#### Option A: Initialize Database on First Run (Recommended for Demo)
Modify `app.py` to check if database exists and initialize with sample data:

```python
# Add at top of app.py
import os
from database.schema import initialize_database

# Check if database exists
if not os.path.exists('data/bitcoin_ohlcv.db'):
    st.warning("⚠️ Database not found. Initializing...")
    initialize_database()
    st.info("✅ Database initialized. Please run data fetch locally and upload.")
```

#### Option B: Use External Database (Production)
- Use PostgreSQL or MySQL instead of SQLite
- Store connection details in Streamlit Secrets
- Modify `database/connection.py` to support external DB

### 🔐 Streamlit Secrets

For sensitive data (API keys, passwords):

1. In Streamlit Cloud dashboard
2. Go to app settings → Secrets
3. Add TOML format:

```toml
[database]
url = "your-database-url"

[api]
key = "your-api-key"
```

Access in code:
```python
import streamlit as st
db_url = st.secrets["database"]["url"]
```

## Current Setup

Your app is currently configured to:
- ✅ Work with local SQLite database
- ✅ Show interactive charts
- ✅ Allow parameter adjustments
- ✅ Display performance metrics

## After Deployment

You'll get a URL like:
**https://bitcoin-ema-analyzer.streamlit.app**

- No tunnel landing page
- No password prompt
- Clean, permanent URL
- Free hosting
- Auto-updates when you push to GitHub

## Limitations (Free Tier)

- Public apps only
- 1 GB storage
- 1 GB memory per app
- Apps sleep after inactivity (wake up in ~30 seconds)

## Alternative: Keep Local + Tunnel

If you prefer to keep using your local database with 3 years of data:

```bash
# Keep using localtunnel (current setup)
lt --port 8501

# Or use ngrok (requires free account)
ngrok http 8501
```

Pros: Full data access, no database migration
Cons: Tunnel landing page, not permanent

## Recommendation

For **demo/sharing**: Deploy to Streamlit Cloud (clean URL)
For **personal use with full data**: Keep local + tunnel

Your choice! The code is ready for both.

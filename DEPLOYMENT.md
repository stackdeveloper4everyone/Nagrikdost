# 🏛️ NagrikMitra — Deployment Guide

Deploy the NagrikMitra application to GitHub, Streamlit Cloud (Frontend), and Railway (Backend).

---

## 📋 Prerequisites

- GitHub account
- Streamlit Cloud account (free at streamlit.io)
- Railway account (free at railway.app)
- Git installed
- Sarvam AI API key

---

## 🚀 Step 1: Push Code to GitHub

### 1.1 Initialize Git Repository

```bash
cd citizen-assistant
git init
git add .
git commit -m "Initial commit: NagrikMitra - AI Citizen Service Assistant"
```

### 1.2 Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Create repository named `citizen-assistant`
3. Copy the repository URL (e.g., `https://github.com/yourusername/citizen-assistant.git`)

### 1.3 Push to GitHub

```bash
git remote add origin https://github.com/yourusername/citizen-assistant.git
git branch -M main
git push -u origin main
```

---

## 🎨 Step 2: Deploy Frontend on Streamlit Cloud

### 2.1 Prerequisites
- GitHub repository is pushed
- Sarvam API key is ready

### 2.2 Deploy

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Configure:
   - **Repository**: yourusername/citizen-assistant
   - **Branch**: main
   - **Main file path**: `streamlit_app.py`
   - **App URL**: `https://citizen-assistant.streamlit.app` (or choose your own)

5. Click **Deploy**

### 2.3 Set Environment Variables

After deployment:
1. Go to app settings (⚙️ bottom-left)
2. Click **Secrets** 
3. Add your Sarvam API key:

```
SARVAM_API_KEY=your_api_key_here
```

### 2.4 Configure API Base URL

Update the API base URL in the streamlit app to point to your Railway backend:

**File**: `frontend/streamlit_app.py`
```python
API_BASE = "https://citizen-assistant.railway.app"  # Update to your Railway URL
```

---

## 🚂 Step 3: Deploy Backend on Railway

### 3.1 Prerequisites
- Railway account at [railway.app](https://railway.app)
- GitHub repository is pushed
- Environment variables ready

### 3.2 Deploy Backend

#### Option A: Using Railway Dashboard (Easy)

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Select your `citizen-assistant` repository
5. Railway will auto-detect the Python project

#### Option B: Using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy
railway up
```

### 3.3 Set Environment Variables in Railway

1. In Railway dashboard, go to your project
2. Click **Variables** tab
3. Add these environment variables:

```
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_BASE_URL=https://api.sarvam.ai
QDRANT_PERSIST_PATH=/tmp/qdrant
TAVILY_API_KEY=your_tavily_api_key
LOG_LEVEL=info
CACHE_MAX_SIZE=1000
```

### 3.4 Get Railway URL

1. Go to **Deployments** tab
2. Find the deployment URL (e.g., `https://citizen-assistant.railway.app`)
3. Copy this URL

### 3.5 Update Frontend with Backend URL

Update `frontend/streamlit_app.py`:

```python
API_BASE = "https://your-railway-url.railway.app"
```

Then commit and push to GitHub:

```bash
git add frontend/streamlit_app.py
git commit -m "Update API base URL for production"
git push
```

Streamlit Cloud will auto-redeploy with the new URL.

---

## 📱 Environment Variables Setup

### Frontend (Streamlit Cloud)
- `SARVAM_API_KEY`: Your Sarvam API key

### Backend (Railway)
- `SARVAM_API_KEY`: Your Sarvam API key
- `SARVAM_BASE_URL`: https://api.sarvam.ai
- `TAVILY_API_KEY`: Your Tavily search API key
- `QDRANT_PERSIST_PATH`: /tmp/qdrant (or persistent volume path)
- `LOG_LEVEL`: info
- `CACHE_MAX_SIZE`: 1000
- `MAX_INPUT_LENGTH`: 2000
- `PROMPT_GUARD_THRESHOLD`: 0.7
- `MAX_TOKENS_GENERAL`: 1000
- `MAX_TOKENS_SCHEME_DETAIL`: 1500
- `MAX_TOKENS_ELIGIBILITY`: 800

---

## 🔗 Application Architecture

```
┌─────────────────────────────────────────────────────┐
│          Streamlit Cloud (Frontend)                  │
│  https://citizen-assistant.streamlit.app             │
│                                                       │
│  streamlit_app.py → frontend/streamlit_app.py       │
└────────────┬────────────────────────────────────────┘
             │ API Calls (HTTP)
             │
┌────────────▼────────────────────────────────────────┐
│            Railway (Backend)                         │
│  https://citizen-assistant.railway.app              │
│                                                       │
│  Procfile → uvicorn app.main:app                    │
│  - NLP Pipeline (Sarvam AI)                         │
│  - Scheme Service                                    │
│  - Eligibility Engine                               │
│  - RAG (Tavily Web Search)                          │
│  - Semantic Cache (Qdrant)                          │
│  - Voice I/O (ASR/TTS)                              │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `.env` file NOT committed (protected by .gitignore)
- [ ] Frontend deployed on Streamlit Cloud
- [ ] Backend deployed on Railway
- [ ] Environment variables set on both platforms
- [ ] Frontend API_BASE URL points to Railway backend
- [ ] Test voice input/output
- [ ] Test multilingual support (11 Indian languages)
- [ ] Test scheme eligibility checker
- [ ] Test grievance filing

---

## 🧪 Testing Deployment

### Test Frontend
```
https://citizen-assistant.streamlit.app
```

### Test Backend API Docs
```
https://your-railway-url.railway.app/docs
```

### Test Voice Endpoint
```bash
curl -X POST https://your-railway-url.railway.app/api/voice \
  -F "audio=@test_audio.wav" \
  -F "session_id=test123" \
  -F "language_preference=hi-IN"
```

---

## 🔐 Security Notes

1. **Never commit `.env` file** — it contains API keys
2. **Use Streamlit Secrets** for sensitive data
3. **Use Railway environment variables** for backend secrets
4. **Rotate API keys** regularly
5. **Enable HTTPS** (both services use HTTPS by default)
6. **Set up rate limiting** if needed

---

## 📊 Monitoring & Logs

### Streamlit Cloud Logs
- Dashboard → App → Logs

### Railway Logs
- Dashboard → Project → Logs

---

## 🆘 Troubleshooting

### Frontend can't connect to backend
- Check Railway deployment is active
- Verify API_BASE URL is correct
- Check environment variables on Railway

### Voice feature not working
- Verify SARVAM_API_KEY on Railway
- Check Sarvam API account has sufficient credits
- Test via `/api/voice` endpoint directly

### Translation fails (400 error)
- LLM response exceeds 1000 chars
- Solution: Already implemented character truncation

### Qdrant vector DB errors
- Railway has limited storage
- Solution: Use in-memory mode (default) or persistent volume

---

## 📈 Production Tips

1. **Monitor API usage** — Sarvam AI charges per API call
2. **Cache responses** — Qdrant semantic cache reduces API calls
3. **Set rate limits** — Prevent abuse
4. **Enable CORS only for your domain**
5. **Backup user data** — Grievances, feedback, etc.
6. **Use CDN** for static assets

---

## 🎉 Success!

Your NagrikMitra application is now live:
- **Frontend**: https://citizen-assistant.streamlit.app
- **Backend API**: https://your-railway-url.railway.app
- **API Docs**: https://your-railway-url.railway.app/docs

---

## 📞 Support

For issues:
1. Check Railway logs
2. Check Streamlit logs
3. Verify environment variables
4. Test via `curl` command above
5. Check Sarvam AI API status

Happy deploying! 🚀

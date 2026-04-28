# 🏛️ NagrikMitra — AI-Powered Citizen Service Assistant

**One-platform solution for Indian government schemes, eligibility checking, and citizen support across 11 languages.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://citizen-assistant.streamlit.app)
[![FastAPI Backend](https://img.shields.io/badge/API-FastAPI-009688?style=flat)](https://citizen-assistant.railway.app)

---

## 🌟 Features

### 💬 **Multilingual Support**
- Hindi, English, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Odia, Punjabi
- Auto-detect or manual language selection
- Responses in user's chosen language

### 🎤 **Voice I/O**
- Speech-to-Text (ASR) via Sarvam AI
- Text-to-Speech (TTS) for audio responses
- Real-time audio input/output

### 📋 **Government Schemes Browser**
- 35+ central government schemes
- Category-based filtering
- Eligibility criteria display

### ✅ **Eligibility Checker**
- 10-step ML pipeline for accuracy
- Real-time eligibility assessment
- Personalized scheme recommendations

### 🔍 **RAG + Semantic Search**
- RAG Engine (Tavily Web Search)
- Semantic Cache (Qdrant Vector DB)
- Reduces API calls, improves speed

### 📱 **Fully Responsive Design**
- Works on Android, iOS, tablets, desktops
- Touch-friendly interface (44px buttons)
- Mobile-optimized layouts

### 🔒 **Security & Privacy**
- PII masking (Aadhaar, PAN, Phone, Email)
- Prompt injection detection
- HTTPS encryption

### 📊 **10-Step Processing Pipeline**
1. **Language Detection** — Auto-detect user language
2. **PII Masking** — Protect sensitive data
3. **Prompt Guard** — Detect malicious input
4. **Semantic Cache** — Check for cached responses
5. **Intent Classification** — Understand user intent
6. **RAG Retrieval** — Fetch relevant information
7. **LLM Generation** — Generate contextual response
8. **Translation** — Translate to user's language
9. **PII Unmask** — Restore sensitive data
10. **Cache Storage** — Store for future use

---

## 🚀 Deployment

### **Streamlit Cloud (Frontend)**
```
https://citizen-assistant.streamlit.app
```

### **Railway (Backend API)**
```
https://citizen-assistant.railway.app
```

### **API Documentation**
```
https://citizen-assistant.railway.app/docs
```

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 📦 Tech Stack

### **Frontend**
- Streamlit (Python web framework)
- HTML/CSS for styling
- Responsive design (mobile-first)

### **Backend**
- FastAPI (Python async web framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)

### **AI/ML**
- Sarvam AI (Speech, Language, Chat APIs)
- Tavily (Web search/RAG)
- Scikit-learn (semantic search)
- Qdrant (vector database)

### **DevOps**
- Docker (containerization)
- Railway (backend hosting)
- Streamlit Cloud (frontend hosting)
- GitHub (version control)

---

## 🛠️ Local Development

### **Prerequisites**
- Python 3.12+
- pip (package manager)
- Git

### **Setup**

1. **Clone repository**
```bash
git clone https://github.com/yourusername/citizen-assistant.git
cd citizen-assistant
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your Sarvam API key
```

5. **Run application**
```bash
python run.py
```

Access:
- Frontend: http://localhost:8501
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📁 Project Structure

```
citizen-assistant/
├── app/                    # Backend (FastAPI)
│   ├── main.py            # Main API routes
│   ├── models.py          # Pydantic models
│   ├── config.py          # Configuration
│   ├── services/          # Core services
│   │   ├── orchestrator.py      # 10-step pipeline
│   │   ├── rag_engine.py        # Tavily web search
│   │   ├── scheme_service.py    # Scheme database
│   │   ├── semantic_cache.py    # Qdrant cache
│   │   └── grievance_service.py # Grievance management
│   ├── sarvam/            # Sarvam AI integration
│   ├── security/          # PII masking, prompt guard
│   ├── feedback/          # Feedback collection
│   └── mock/              # Mock government APIs
├── frontend/              # Frontend (Streamlit)
│   └── streamlit_app.py  # Main Streamlit app
├── data/                  # Data files
│   └── schemes.json       # Government schemes
├── tests/                 # Unit tests
├── Dockerfile            # Docker image
├── docker-compose.yml    # Multi-container setup
├── requirements.txt      # Python dependencies
├── Procfile              # Railway deployment
├── streamlit_app.py      # Streamlit Cloud entry point
├── run.py                # Local development runner
└── DEPLOYMENT.md         # Deployment guide
```

---

## 🔧 Configuration

### **Environment Variables** (`.env`)

```env
# Sarvam AI
SARVAM_API_KEY=your_api_key_here
SARVAM_BASE_URL=https://api.sarvam.ai

# Tavily Search
TAVILY_API_KEY=your_tavily_key_here

# Application
LOG_LEVEL=info
CACHE_MAX_SIZE=1000
MAX_INPUT_LENGTH=2000
PROMPT_GUARD_THRESHOLD=0.7
```

---

## 📊 API Endpoints

### **Chat**
```
POST /api/chat
Input: { message, session_id, language_preference, state }
Output: { response, detected_language, intent, schemes_referenced }
```

### **Voice**
```
POST /api/voice
Input: audio file, language_preference
Output: { transcribed_text, response_text, audio_base64, detected_language }
```

### **Schemes**
```
GET /api/schemes
Output: List of 35+ government schemes
```

### **Eligibility**
```
POST /api/eligibility
Input: { age, income, state, category, occupation }
Output: List of eligible schemes
```

### **Grievance**
```
POST /api/grievance
Input: { subject, description, state }
Output: { grievance_id, status, receipt_date }
```

---

## 🧪 Testing

### **Run Tests**
```bash
pytest tests/ -v
```

### **Test Voice Endpoint**
```bash
curl -X POST http://localhost:8000/api/voice \
  -F "audio=@test.wav" \
  -F "language_preference=hi-IN"
```

---

## 📈 Performance

- **Average Response Time**: 2-3 seconds
- **Concurrent Users**: 100+ (Railway)
- **API Calls/Month**: Optimized with semantic cache
- **Uptime**: 99.9% (Railway SLA)

---

## 🔐 Security

✅ PII data masking  
✅ Prompt injection detection  
✅ HTTPS encryption  
✅ API key protection  
✅ Input validation  
✅ Rate limiting ready  

---

## 📄 License

MIT License — See LICENSE file

---

## 👥 Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@citizen-assistant.in

---

## 🎯 Roadmap

- [ ] Mobile app (React Native)
- [ ] Dashboard for government officials
- [ ] SMS support (USSD)
- [ ] Document upload & processing
- [ ] Grievance tracking dashboard
- [ ] Integration with government portals
- [ ] Offline mode

---

## 🙏 Credits

- **Sarvam AI** — Speech, Language, and Chat APIs
- **Tavily** — Web search and RAG
- **Qdrant** — Vector database
- **Streamlit** — Frontend framework
- **FastAPI** — Backend framework

---

**Made with ❤️ for India**

🏛️ NagrikMitra v1.0 | 2026

"""NagrikMitra — Streamlit Frontend.

Three-panel layout:
- Left Sidebar: Location, language, quick actions
- Center: Chat interface with voice support
- Right: Scheme cards, eligibility results, grievance tracker
"""

import streamlit as st
import requests
import json
import base64
import uuid
import os
from datetime import datetime

# ─── PAGE CONFIG ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="NagrikMitra — Citizen Service Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="auto",  # auto-collapse on mobile
    menu_items={
        'Get Help': 'https://github.com/yourusername/citizen-assistant',
        'Report a bug': "https://github.com/yourusername/citizen-assistant/issues",
        'About': "# NagrikMitra\nUnified Citizen Service Assistant"
    }
)

try:
    API_BASE = st.secrets.get("API_BASE", "http://localhost:8000")
except:
    API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

# ─── CUSTOM CSS ──────────────────────────────────────────────────────

st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<style>
    * {
        box-sizing: border-box;
    }

    /* Main theme colors - Government of India inspired */
    :root {
        --primary: #1a237e;
        --primary-light: #534bae;
        --accent: #ff6f00;
        --accent-light: #ffa040;
        --bg-light: #f5f5f5;
        --success: #2e7d32;
        --warning: #f57f17;
    }

    /* Global responsive settings */
    body {
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #303f9f 100%);
        color: white;
        padding: 1.2rem 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(26, 35, 126, 0.3);
    }
    .main-header h1 {
        margin: 0;
        font-size: clamp(1.2rem, 5vw, 1.8rem);
        font-weight: 700;
        word-break: break-word;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.9;
        font-size: clamp(0.75rem, 3vw, 0.95rem);
    }

    /* Chat message bubbles */
    .chat-user {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        border-left: 4px solid #1a237e;
        padding: clamp(0.75rem, 2vw, 1.2rem);
        border-radius: 0 8px 8px 8px;
        margin: 0.5rem 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .chat-bot {
        background: linear-gradient(135deg, #fff3e0, #ffe0b2);
        border-left: 4px solid #ff6f00;
        padding: clamp(0.75rem, 2vw, 1.2rem);
        border-radius: 8px 0 8px 8px;
        margin: 0.5rem 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }

    /* Scheme cards */
    .scheme-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: clamp(0.75rem, 2vw, 1.2rem);
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .scheme-card:hover,
    .scheme-card:active {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .scheme-card:active {
        transform: translateY(0);
    }
    .scheme-card h4 {
        color: #1a237e;
        margin: 0 0 0.5rem 0;
        font-size: clamp(0.9rem, 3vw, 1.1rem);
        word-break: break-word;
    }
    .scheme-card p {
        font-size: clamp(0.75rem, 2.5vw, 0.9rem);
        line-height: 1.4;
    }
    
    .scheme-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: clamp(0.6rem, 2vw, 0.75rem);
        font-weight: 600;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
    .badge-category {
        background: #e8eaf6;
        color: #1a237e;
    }
    .badge-central {
        background: #e8f5e9;
        color: #2e7d32;
    }
    .badge-state {
        background: #fff3e0;
        color: #e65100;
    }

    /* Status indicators */
    .status-submitted { color: #1565c0; font-weight: 600; }
    .status-in_review { color: #f57f17; font-weight: 600; }
    .status-resolved { color: #2e7d32; font-weight: 600; }

    /* Quick action buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
        font-size: clamp(0.8rem, 2.5vw, 0.95rem) !important;
        padding: clamp(0.4rem, 2vw, 0.6rem) !important;
        min-height: 44px !important;
        min-width: 44px !important;
    }

    /* Pipeline info badge */
    .pipeline-info {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
        font-size: clamp(0.6rem, 2vw, 0.75rem);
    }
    .info-chip {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 12px;
        background: #f5f5f5;
        color: #616161;
        border: 1px solid #e0e0e0;
        white-space: nowrap;
    }

    /* Input field responsive styling */
    .stTextInput input,
    .stSelectbox select,
    .stNumberInput input {
        font-size: 16px !important;
        padding: clamp(0.5rem, 2vw, 0.75rem) !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9ff 0%, #eef0ff 100%);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: clamp(0.5rem, 2vw, 1rem) !important;
    }

    /* Responsive columns */
    [data-testid="column"] {
        padding: 0.5rem;
    }

    /* Audio input styling */
    audio {
        width: 100%;
        max-width: 100%;
    }

    /* Chat input field */
    .stChatInput .stTextInput input {
        font-size: 16px !important;
        min-height: 44px !important;
    }

    /* ─── DESKTOP (1024px+) ─── */
    @media (min-width: 1024px) {
        .main-header {
            padding: 1.5rem 2rem;
        }
        .chat-user, .chat-bot {
            max-width: 85%;
        }
        [data-testid="column"] {
            padding: 1rem;
        }
        .scheme-card {
            padding: 1.2rem;
        }
    }

    /* ─── TABLET (768px - 1023px) ─── */
    @media (max-width: 1023px) and (min-width: 768px) {
        .main-header {
            padding: 1rem 1.5rem;
            margin-bottom: 0.8rem;
        }
        .main-header h1 {
            font-size: 1.4rem;
        }
        .chat-user, .chat-bot {
            max-width: 90%;
        }
        .pipeline-info {
            margin-top: 0.3rem;
            gap: 0.3rem;
        }
        [data-testid="column"] {
            padding: 0.75rem;
        }
        .stButton > button {
            min-height: 40px;
        }
    }

    /* ─── MOBILE (up to 767px) ─── */
    @media (max-width: 767px) {
        .main-header {
            padding: 0.8rem;
            margin-bottom: 0.5rem;
            border-radius: 6px;
        }
        .main-header h1 {
            font-size: 1.1rem;
            margin: 0.3rem 0;
        }
        .main-header p {
            font-size: 0.7rem;
            margin-top: 0.2rem;
        }

        /* Full width messages on mobile */
        .chat-user, .chat-bot {
            max-width: 100%;
            padding: 0.7rem 0.9rem;
            border-radius: 6px;
            margin: 0.4rem 0;
            font-size: 0.9rem;
        }

        /* Wider scheme cards on mobile */
        .scheme-card {
            padding: 0.8rem;
            border-radius: 6px;
            margin: 0.4rem 0;
        }
        .scheme-card h4 {
            font-size: 0.95rem;
            margin-bottom: 0.3rem;
        }
        .scheme-card p {
            font-size: 0.8rem;
        }

        .scheme-badge {
            font-size: 0.65rem;
            padding: 0.15rem 0.5rem;
            margin-right: 0.2rem;
        }

        /* Buttons: touch-friendly size (44x44 minimum) */
        .stButton > button {
            width: 100% !important;
            min-height: 44px !important;
            font-size: 0.85rem !important;
            padding: 0.6rem !important;
        }

        /* Stack columns on mobile */
        [data-testid="column"] {
            padding: 0.3rem !important;
        }

        /* Remove gaps between elements */
        .stContainer {
            padding: 0 !important;
        }

        /* Chat history spacing */
        [data-testid="stChatMessageContainer"] {
            padding: 0.5rem 0 !important;
        }

        /* Sidebar on mobile */
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding: 0.5rem !important;
        }

        /* Input fields touch-friendly */
        .stTextInput input,
        .stSelectbox select,
        .stNumberInput input,
        .stChatInput .stTextInput input {
            font-size: 16px !important;
            min-height: 44px !important;
            padding: 0.6rem !important;
        }

        /* Pipeline info badges */
        .pipeline-info {
            font-size: 0.65rem;
            gap: 0.3rem;
        }
        .info-chip {
            padding: 0.1rem 0.4rem;
            font-size: 0.65rem;
        }

        /* Tabs responsive */
        .stTabs [role="tablist"] {
            overflow-x: auto;
        }
        .stTabs [role="tab"] {
            font-size: 0.85rem;
            padding: 0.5rem !important;
        }

        /* Audio player */
        audio {
            height: 40px;
        }
    }

    /* ─── SMALL PHONES (up to 480px) ─── */
    @media (max-width: 480px) {
        .main-header {
            padding: 0.6rem;
        }
        .main-header h1 {
            font-size: 0.95rem;
        }
        .main-header p {
            font-size: 0.65rem;
            margin-top: 0.15rem;
        }

        .chat-user, .chat-bot {
            padding: 0.6rem 0.8rem;
            font-size: 0.85rem;
        }

        .scheme-card {
            padding: 0.7rem;
        }
        .scheme-card h4 {
            font-size: 0.9rem;
        }
        .scheme-card p {
            font-size: 0.75rem;
        }

        .stButton > button {
            font-size: 0.8rem !important;
            padding: 0.5rem !important;
            min-height: 40px !important;
        }

        .stTextInput input,
        .stSelectbox select,
        .stChatInput .stTextInput input {
            font-size: 16px !important;
            min-height: 40px !important;
        }

        /* Reduce gaps */
        .stTabs [role="tab"] {
            font-size: 0.75rem;
            padding: 0.4rem !important;
        }
    }

    /* ─── LANDSCAPE ORIENTATION (height < width) ─── */
    @media (max-height: 500px) and (max-width: 1023px) {
        .main-header {
            padding: 0.5rem;
            margin-bottom: 0.3rem;
        }
        .main-header h1 {
            font-size: 1rem;
        }
        .chat-user, .chat-bot {
            margin: 0.2rem 0;
            padding: 0.5rem;
        }
        .stButton > button {
            min-height: 36px !important;
        }
    }

    /* Prevent zooming on input focus (iOS) */
    input[type=text],
    input[type=email],
    input[type=number],
    textarea,
    select {
        font-size: 16px !important;
    }

    /* Safe area for notched phones */
    @supports (padding: max(0px)) {
        body {
            padding-left: max(12px, env(safe-area-inset-left));
            padding-right: max(12px, env(safe-area-inset-right));
        }
    }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ───────────────────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:16]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_schemes" not in st.session_state:
    st.session_state.selected_schemes = []

# ─── LANGUAGE MAP ────────────────────────────────────────────────────

LANGUAGES = {
    "Auto-Detect": "",
    "English": "en-IN",
    "Hindi (हिन्दी)": "hi-IN",
    "Tamil (தமிழ்)": "ta-IN",
    "Telugu (తెలుగు)": "te-IN",
    "Bengali (বাংলা)": "bn-IN",
    "Marathi (मराठी)": "mr-IN",
    "Gujarati (ગુજરાતી)": "gu-IN",
    "Kannada (ಕನ್ನಡ)": "kn-IN",
    "Malayalam (മലയാളം)": "ml-IN",
    "Odia (ଓଡ଼ିଆ)": "od-IN",
    "Punjabi (ਪੰਜਾਬੀ)": "pa-IN",
}

WELCOME_MESSAGES = {
    "": "🙏 Namaste! I'm **NagrikMitra**, your AI-powered government services assistant.\n\nI can help you with:\n- 📋 Government scheme information\n- ✅ Eligibility checks\n\nAsk me anything in your preferred language!",
    "en-IN": "🙏 Hello! I'm **NagrikMitra**, your AI-powered government services assistant.\n\nI can help you with:\n- 📋 Government scheme information\n- ✅ Eligibility checks\n\nAsk me anything!",
    "hi-IN": "🙏 नमस्ते! मैं **नागरिकमित्र** हूँ, आपका AI-संचालित सरकारी सेवा सहायक।\n\nमैं इनमें आपकी मदद कर सकता हूँ:\n- 📋 सरकारी योजनाओं की जानकारी\n- ✅ पात्रता जाँच\n\nअपनी भाषा में कुछ भी पूछें!",
    "ta-IN": "🙏 வணக்கம்! நான் **நாகரிக்மித்ரா**, உங்கள் AI இயங்கும் அரசு சேவை உதவியாளர்.\n\nநான் உங்களுக்கு உதவ முடியும்:\n- 📋 அரசு திட்டங்கள் பற்றிய தகவல்\n- ✅ தகுதி சோதனை\n\nஉங்கள் மொழியில் எதையும் கேளுங்கள்!",
    "te-IN": "🙏 నమస్కారం! నేను **నాగరిక్‌మిత్ర**, మీ AI-ఆధారిత ప్రభుత్వ సేవల సహాయకుడిని.\n\nనేను మీకు సహాయం చేయగలను:\n- 📋 ప్రభుత్వ పథకాల సమాచారం\n- ✅ అర్హత తనిఖీ\n\nమీ భాషలో ఏదైనా అడగండి!",
    "bn-IN": "🙏 নমস্কার! আমি **নাগরিকমিত্র**, আপনার AI-চালিত সরকারি পরিষেবা সহায়ক।\n\nআমি আপনাকে সাহায্য করতে পারি:\n- 📋 সরকারি প্রকল্পের তথ্য\n- ✅ যোগ্যতা যাচাই\n\nআপনার ভাষায় যেকোনো কিছু জিজ্ঞাসা করুন!",
    "mr-IN": "🙏 नमस्कार! मी **नागरिकमित्र**, तुमचा AI-संचालित सरकारी सेवा सहाय्यक.\n\nमी तुम्हाला यात मदत करू शकतो:\n- 📋 सरकारी योजनांची माहिती\n- ✅ पात्रता तपासणी\n\nतुमच्या भाषेत काहीही विचारा!",
    "gu-IN": "🙏 નમસ્તે! હું **નાગરિકમિત્ર**, તમારો AI-સંચાલિત સરકારી સેવા સહાયક.\n\nહું તમને મદદ કરી શકું:\n- 📋 સરકારી યોજનાઓની માહિતી\n- ✅ પાત્રતા તપાસ\n\nતમારી ભાષામાં કંઈપણ પૂછો!",
    "kn-IN": "🙏 ನಮಸ್ಕಾರ! ನಾನು **ನಾಗರಿಕಮಿತ್ರ**, ನಿಮ್ಮ AI-ಚಾಲಿತ ಸರ್ಕಾರಿ ಸೇವಾ ಸಹಾಯಕ.\n\nನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ:\n- 📋 ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಮಾಹಿತಿ\n- ✅ ಅರ್ಹತಾ ಪರಿಶೀಲನೆ\n\nನಿಮ್ಮ ಭಾಷೆಯಲ್ಲಿ ಏನಾದರೂ ಕೇಳಿ!",
    "ml-IN": "🙏 നമസ്കാരം! ഞാൻ **നാഗരിക്മിത്ര**, നിങ്ങളുടെ AI-പ്രവർത്തിത സർക്കാർ സേവന സഹായി.\n\nഎനിക്ക് നിങ്ങളെ സഹായിക്കാൻ കഴിയും:\n- 📋 സർക്കാർ പദ്ധതി വിവരങ്ങൾ\n- ✅ യോഗ്യതാ പരിശോധന\n\nനിങ്ങളുടെ ഭാഷയിൽ എന്തും ചോദിക്കൂ!",
    "od-IN": "🙏 ନମସ୍କାର! ମୁଁ **ନାଗରିକମିତ୍ର**, ଆପଣଙ୍କ AI-ଚାଳିତ ସରକାରୀ ସେବା ସହାୟକ.\n\nମୁଁ ଆପଣଙ୍କୁ ସାହାଯ୍ୟ କରିପାରିବି:\n- 📋 ସରକାରୀ ଯୋଜନା ସୂଚନା\n- ✅ ଯୋଗ୍ୟତା ଯାଞ୍ଚ\n\nଆପଣଙ୍କ ଭାଷାରେ କିଛି ବି ପଚାରନ୍ତୁ!",
    "pa-IN": "🙏 ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ **ਨਾਗਰਿਕਮਿੱਤਰ**, ਤੁਹਾਡਾ AI-ਸੰਚਾਲਿਤ ਸਰਕਾਰੀ ਸੇਵਾ ਸਹਾਇਕ.\n\nਮੈਂ ਤੁਹਾਡੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ:\n- 📋 ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਦੀ ਜਾਣਕਾਰੀ\n- ✅ ਯੋਗਤਾ ਜਾਂਚ\n\nਆਪਣੀ ਭਾਸ਼ਾ ਵਿੱਚ ਕੁਝ ਵੀ ਪੁੱਛੋ!",
}

# ─── UI TRANSLATIONS ────────────────────────────────────────────────

UI_STRINGS = {
    "en-IN": {
        "settings": "⚙️ Settings",
        "your_state": "📍 Your State",
        "district": "🏘️ District (optional)",
        "language": "🌐 Language",
        "quick_actions": "⚡ Quick Actions",
        "browse_schemes": "📋 Browse Schemes",
        "check_eligibility": "✅ Check Eligibility",
        "footer": "NagrikMitra v1.0 | Powered by Sarvam AI",
        "header_title": "🏛️ NagrikMitra",
        "header_subtitle": "AI-Powered Unified Multilingual Citizen Service Assistant",
        "header_powered": "Powered by Sarvam AI | 11 Indian Languages Supported",
        "chat_title": "💬 Chat with NagrikMitra",
        "chat_placeholder": "Type your message...",
        "voice_label": "🎤 Record your voice",
        "listen": "🔊 Listen",
        "processing_voice": "🎧 Processing voice...",
        "schemes_tab": "📋 Schemes",
        "eligibility_tab": "✅ Eligibility",
        "govt_schemes": "Government Schemes",
        "filter_category": "Filter by category",
        "check_your_eligibility": "Check Your Eligibility",
        "your_age": "Your Age",
        "annual_income": "Annual Income (₹)",
        "gender": "Gender",
        "male": "male",
        "female": "female",
        "occupation": "Occupation (e.g., farmer, student)",
        "state": "State",
        "check_elig_btn": "Check Eligibility",
        "no_schemes": "No schemes found. Try changing filters.",
        "matching_schemes": "Found {count} matching schemes!",
        "no_matching": "No matching schemes found with current criteria",
        "connect_backend": "Connect to backend to browse schemes",
        "tts_failed": "TTS failed, please try again.",
        "tts_connect_fail": "Could not connect to TTS service.",
        "voice_failed": "Voice processing failed",
        "backend_error": "Cannot connect to backend server.",
        "error_retry": "Sorry, I encountered an error. Please try again.",
        "backend_not_running": "Cannot connect to the backend server. Please ensure it's running.",
    },
    "hi-IN": {
        "settings": "⚙️ सेटिंग्स",
        "your_state": "📍 आपका राज्य",
        "district": "🏘️ जिला (वैकल्पिक)",
        "language": "🌐 भाषा",
        "quick_actions": "⚡ त्वरित कार्य",
        "browse_schemes": "📋 योजनाएँ देखें",
        "check_eligibility": "✅ पात्रता जाँचें",
        "footer": "नागरिकमित्र v1.0 | Sarvam AI द्वारा संचालित",
        "header_title": "🏛️ नागरिकमित्र",
        "header_subtitle": "AI-संचालित बहुभाषी नागरिक सेवा सहायक",
        "header_powered": "Sarvam AI द्वारा संचालित | 11 भारतीय भाषाएँ समर्थित",
        "chat_title": "💬 नागरिकमित्र से बात करें",
        "chat_placeholder": "अपना संदेश लिखें...",
        "voice_label": "🎤 अपनी आवाज रिकॉर्ड करें",
        "listen": "🔊 सुनें",
        "processing_voice": "🎧 आवाज़ प्रोसेस हो रही है...",
        "schemes_tab": "📋 योजनाएँ",
        "eligibility_tab": "✅ पात्रता",
        "govt_schemes": "सरकारी योजनाएँ",
        "filter_category": "श्रेणी के अनुसार फ़िल्टर करें",
        "check_your_eligibility": "अपनी पात्रता जाँचें",
        "your_age": "आपकी आयु",
        "annual_income": "वार्षिक आय (₹)",
        "gender": "लिंग",
        "male": "पुरुष",
        "female": "महिला",
        "occupation": "व्यवसाय (जैसे, किसान, छात्र)",
        "state": "राज्य",
        "check_elig_btn": "पात्रता जाँचें",
        "no_schemes": "कोई योजना नहीं मिली। फ़िल्टर बदलकर देखें।",
        "matching_schemes": "{count} मिलती-जुलती योजनाएँ मिलीं!",
        "no_matching": "वर्तमान मानदंडों से कोई योजना नहीं मिली",
        "connect_backend": "योजनाएँ देखने के लिए बैकएंड से कनेक्ट करें",
        "tts_failed": "TTS विफल, कृपया पुनः प्रयास करें।",
        "tts_connect_fail": "TTS सेवा से कनेक्ट नहीं हो सका।",
        "voice_failed": "आवाज़ प्रोसेसिंग विफल",
        "backend_error": "बैकएंड सर्वर से कनेक्ट नहीं हो सका।",
        "error_retry": "क्षमा करें, एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
        "backend_not_running": "बैकएंड सर्वर से कनेक्ट नहीं हो सका। कृपया सुनिश्चित करें कि यह चल रहा है।",
    },
    "ta-IN": {
        "settings": "⚙️ அமைப்புகள்",
        "your_state": "📍 உங்கள் மாநிலம்",
        "district": "🏘️ மாவட்டம் (விருப்பம்)",
        "language": "🌐 மொழி",
        "quick_actions": "⚡ விரைவு செயல்கள்",
        "browse_schemes": "📋 திட்டங்களைப் பார்க்க",
        "check_eligibility": "✅ தகுதியை சரிபார்க்க",
        "footer": "நாகரிக்மித்ரா v1.0 | Sarvam AI ஆல் இயக்கப்படுகிறது",
        "header_title": "🏛️ நாகரிக்மித்ரா",
        "header_subtitle": "AI இயங்கும் பன்மொழி குடிமக்கள் சேவை உதவியாளர்",
        "header_powered": "Sarvam AI ஆல் இயக்கப்படுகிறது | 11 இந்திய மொழிகள் ஆதரிக்கப்படுகின்றன",
        "chat_title": "💬 நாகரிக்மித்ராவுடன் அரட்டை",
        "chat_placeholder": "உங்கள் செய்தியை உள்ளிடவும்...",
        "voice_label": "🎤 உங்கள் குரலை பதிவு செய்யவும்",
        "listen": "🔊 கேளுங்கள்",
        "processing_voice": "🎧 குரல் செயலாக்கம்...",
        "schemes_tab": "📋 திட்டங்கள்",
        "eligibility_tab": "✅ தகுதி",
        "govt_schemes": "அரசு திட்டங்கள்",
        "filter_category": "வகை வாரியாக வடிகட்டவும்",
        "check_your_eligibility": "உங்கள் தகுதியை சரிபார்க்கவும்",
        "your_age": "உங்கள் வயது",
        "annual_income": "ஆண்டு வருமானம் (₹)",
        "gender": "பாலினம்",
        "male": "ஆண்",
        "female": "பெண்",
        "occupation": "தொழில் (எ.கா., விவசாயி, மாணவர்)",
        "state": "மாநிலம்",
        "check_elig_btn": "தகுதியை சரிபார்க்கவும்",
        "no_schemes": "திட்டங்கள் இல்லை. வடிகட்டிகளை மாற்றி முயற்சிக்கவும்.",
        "matching_schemes": "{count} பொருந்தும் திட்டங்கள் கண்டறியப்பட்டன!",
        "no_matching": "தற்போதைய நிபந்தனைகளுக்கு பொருந்தும் திட்டங்கள் இல்லை",
        "connect_backend": "திட்டங்களைப் பார்க்க பின்னணி சேவையகத்துடன் இணைக்கவும்",
        "tts_failed": "TTS தோல்வி, மீண்டும் முயற்சிக்கவும்.",
        "tts_connect_fail": "TTS சேவையுடன் இணைக்க முடியவில்லை.",
        "voice_failed": "குரல் செயலாக்கம் தோல்வி",
        "backend_error": "பின்னணி சேவையகத்துடன் இணைக்க முடியவில்லை.",
        "error_retry": "மன்னிக்கவும், பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.",
        "backend_not_running": "பின்னணி சேவையகத்துடன் இணைக்க முடியவில்லை. இயங்குகிறதா என உறுதிசெய்யவும்.",
    },
    "te-IN": {
        "settings": "⚙️ సెట్టింగ్‌లు",
        "your_state": "📍 మీ రాష్ట్రం",
        "district": "🏘️ జిల్లా (ఐచ్ఛికం)",
        "language": "🌐 భాష",
        "quick_actions": "⚡ త్వరిత చర్యలు",
        "browse_schemes": "📋 పథకాలు చూడండి",
        "check_eligibility": "✅ అర్హత తనిఖీ",
        "footer": "నాగరిక్‌మిత్ర v1.0 | Sarvam AI ద్వారా",
        "header_title": "🏛️ నాగరిక్‌మిత్ర",
        "header_subtitle": "AI-ఆధారిత బహుభాషా పౌర సేవా సహాయకుడు",
        "header_powered": "Sarvam AI ద్వారా | 11 భారతీయ భాషలు",
        "chat_title": "💬 నాగరిక్‌మిత్రతో చాట్",
        "chat_placeholder": "మీ సందేశాన్ని టైప్ చేయండి...",
        "voice_label": "🎤 మీ గొంతు రికార్డ్ చేయండి",
        "listen": "🔊 వినండి",
        "processing_voice": "🎧 గొంతు ప్రాసెస్ అవుతోంది...",
        "schemes_tab": "📋 పథకాలు",
        "eligibility_tab": "✅ అర్హత",
        "govt_schemes": "ప్రభుత్వ పథకాలు",
        "filter_category": "వర్గం ద్వారా ఫిల్టర్",
        "check_your_eligibility": "మీ అర్హతను తనిఖీ చేయండి",
        "your_age": "మీ వయస్సు",
        "annual_income": "వార్షిక ఆదాయం (₹)",
        "gender": "లింగం",
        "male": "పురుషుడు",
        "female": "స్త్రీ",
        "occupation": "వృత్తి (ఉదా., రైతు, విద్యార్థి)",
        "state": "రాష్ట్రం",
        "check_elig_btn": "అర్హత తనిఖీ",
        "no_schemes": "పథకాలు కనుగొనబడలేదు. ఫిల్టర్‌లు మార్చి చూడండి.",
        "matching_schemes": "{count} సరిపోయే పథకాలు కనుగొనబడ్డాయి!",
        "no_matching": "ప్రస్తుత ప్రమాణాలతో పథకాలు కనుగొనబడలేదు",
        "connect_backend": "పథకాలు చూడటానికి బ్యాకెండ్‌కు కనెక్ట్ అవ్వండి",
        "tts_failed": "TTS విఫలమైంది, మళ్ళీ ప్రయత్నించండి.",
        "tts_connect_fail": "TTS సేవకు కనెక్ట్ కాలేదు.",
        "voice_failed": "వాయిస్ ప్రాసెసింగ్ విఫలమైంది",
        "backend_error": "బ్యాకెండ్ సర్వర్‌కు కనెక్ట్ కాలేదు.",
        "error_retry": "క్షమించండి, లోపం ఏర్పడింది. మళ్ళీ ప్రయత్నించండి.",
        "backend_not_running": "బ్యాకెండ్ సర్వర్‌కు కనెక్ట్ కాలేదు. నడుస్తోందో నిర్ధారించుకోండి.",
    },
    "bn-IN": {
        "settings": "⚙️ সেটিংস",
        "your_state": "📍 আপনার রাজ্য",
        "district": "🏘️ জেলা (ঐচ্ছিক)",
        "language": "🌐 ভাষা",
        "quick_actions": "⚡ দ্রুত কার্য",
        "browse_schemes": "📋 প্রকল্প দেখুন",
        "check_eligibility": "✅ যোগ্যতা যাচাই",
        "footer": "নাগরিকমিত্র v1.0 | Sarvam AI দ্বারা",
        "header_title": "🏛️ নাগরিকমিত্র",
        "header_subtitle": "AI-চালিত বহুভাষিক নাগরিক সেবা সহায়ক",
        "header_powered": "Sarvam AI দ্বারা | ১১টি ভারতীয় ভাষা সমর্থিত",
        "chat_title": "💬 নাগরিকমিত্রের সাথে চ্যাট",
        "chat_placeholder": "আপনার বার্তা লিখুন...",
        "voice_label": "🎤 আপনার কণ্ঠ রেকর্ড করুন",
        "listen": "🔊 শুনুন",
        "processing_voice": "🎧 কণ্ঠ প্রক্রিয়াকরণ হচ্ছে...",
        "schemes_tab": "📋 প্রকল্প",
        "eligibility_tab": "✅ যোগ্যতা",
        "govt_schemes": "সরকারি প্রকল্প",
        "filter_category": "বিভাগ অনুসারে ফিল্টার",
        "check_your_eligibility": "আপনার যোগ্যতা যাচাই করুন",
        "your_age": "আপনার বয়স",
        "annual_income": "বার্ষিক আয় (₹)",
        "gender": "লিঙ্গ",
        "male": "পুরুষ",
        "female": "মহিলা",
        "occupation": "পেশা (যেমন, কৃষক, ছাত্র)",
        "state": "রাজ্য",
        "check_elig_btn": "যোগ্যতা যাচাই",
        "no_schemes": "কোনো প্রকল্প পাওয়া যায়নি। ফিল্টার পরিবর্তন করুন।",
        "matching_schemes": "{count}টি মিলে যাওয়া প্রকল্প পাওয়া গেছে!",
        "no_matching": "বর্তমান মানদণ্ডে কোনো প্রকল্প পাওয়া যায়নি",
        "connect_backend": "প্রকল্প দেখতে ব্যাকএন্ডে সংযোগ করুন",
        "tts_failed": "TTS ব্যর্থ, আবার চেষ্টা করুন।",
        "tts_connect_fail": "TTS সেবায় সংযোগ করা যায়নি।",
        "voice_failed": "কণ্ঠ প্রক্রিয়াকরণ ব্যর্থ",
        "backend_error": "ব্যাকএন্ড সার্ভারে সংযোগ করা যায়নি।",
        "error_retry": "দুঃখিত, একটি ত্রুটি হয়েছে। আবার চেষ্টা করুন।",
        "backend_not_running": "ব্যাকএন্ড সার্ভারে সংযোগ করা যায়নি। চালু আছে কিনা নিশ্চিত করুন।",
    },
    "mr-IN": {
        "settings": "⚙️ सेटिंग्ज",
        "your_state": "📍 तुमचे राज्य",
        "district": "🏘️ जिल्हा (ऐच्छिक)",
        "language": "🌐 भाषा",
        "quick_actions": "⚡ जलद कृती",
        "browse_schemes": "📋 योजना पहा",
        "check_eligibility": "✅ पात्रता तपासा",
        "footer": "नागरिकमित्र v1.0 | Sarvam AI द्वारे",
        "header_title": "🏛️ नागरिकमित्र",
        "header_subtitle": "AI-संचालित बहुभाषिक नागरिक सेवा सहाय्यक",
        "header_powered": "Sarvam AI द्वारे | ११ भारतीय भाषा समर्थित",
        "chat_title": "💬 नागरिकमित्रशी बोला",
        "chat_placeholder": "तुमचा संदेश लिहा...",
        "voice_label": "🎤 तुमचा आवाज रेकॉर्ड करा",
        "listen": "🔊 ऐका",
        "processing_voice": "🎧 आवाज प्रक्रिया होत आहे...",
        "schemes_tab": "📋 योजना",
        "eligibility_tab": "✅ पात्रता",
        "govt_schemes": "सरकारी योजना",
        "filter_category": "श्रेणीनुसार फिल्टर करा",
        "check_your_eligibility": "तुमची पात्रता तपासा",
        "your_age": "तुमचे वय",
        "annual_income": "वार्षिक उत्पन्न (₹)",
        "gender": "लिंग",
        "male": "पुरुष",
        "female": "स्त्री",
        "occupation": "व्यवसाय (उदा., शेतकरी, विद्यार्थी)",
        "state": "राज्य",
        "check_elig_btn": "पात्रता तपासा",
        "no_schemes": "योजना आढळल्या नाहीत. फिल्टर बदलून पहा.",
        "matching_schemes": "{count} जुळणाऱ्या योजना सापडल्या!",
        "no_matching": "सध्याच्या निकषांनुसार कोणत्याही योजना सापडल्या नाहीत",
        "connect_backend": "योजना पाहण्यासाठी बॅकएंडशी कनेक्ट करा",
        "tts_failed": "TTS अयशस्वी, पुन्हा प्रयत्न करा.",
        "tts_connect_fail": "TTS सेवेशी कनेक्ट होऊ शकले नाही.",
        "voice_failed": "आवाज प्रक्रिया अयशस्वी",
        "backend_error": "बॅकएंड सर्व्हरशी कनेक्ट होऊ शकले नाही.",
        "error_retry": "क्षमस्व, त्रुटी आली. पुन्हा प्रयत्न करा.",
        "backend_not_running": "बॅकएंड सर्व्हरशी कनेक्ट होऊ शकले नाही. चालू आहे याची खात्री करा.",
    },
    "gu-IN": {
        "settings": "⚙️ સેટિંગ્સ",
        "your_state": "📍 તમારું રાજ્ય",
        "district": "🏘️ જિલ્લો (વૈકલ્પિક)",
        "language": "🌐 ભાષા",
        "quick_actions": "⚡ ઝડપી ક્રિયાઓ",
        "browse_schemes": "📋 યોજનાઓ જુઓ",
        "check_eligibility": "✅ પાત્રતા ચકાસો",
        "footer": "નાગરિકમિત્ર v1.0 | Sarvam AI દ્વારા",
        "header_title": "🏛️ નાગરિકમિત્ર",
        "header_subtitle": "AI-સંચાલિત બહુભાષી નાગરિક સેવા સહાયક",
        "header_powered": "Sarvam AI દ્વારા | ૧૧ ભારતીય ભાષાઓ",
        "chat_title": "💬 નાગરિકમિત્ર સાથે ચેટ",
        "chat_placeholder": "તમારો સંદેશ લખો...",
        "voice_label": "🎤 તમારો અવાજ રિકોર્ડ કરો",
        "listen": "🔊 સાંભળો",
        "processing_voice": "🎧 અવાજ પ્રક્રિયા થઈ રહી છે...",
        "schemes_tab": "📋 યોજનાઓ",
        "eligibility_tab": "✅ પાત્રતા",
        "govt_schemes": "સરકારી યોજનાઓ",
        "filter_category": "કેટેગરી પ્રમાણે ફિલ્ટર",
        "check_your_eligibility": "તમારી પાત્રતા ચકાસો",
        "your_age": "તમારી ઉંમર",
        "annual_income": "વાર્ષિક આવક (₹)",
        "gender": "લિંગ",
        "male": "પુરુષ",
        "female": "સ્ત્રી",
        "occupation": "વ્યવસાય (દા.ત., ખેડૂત, વિદ્યાર્થી)",
        "state": "રાજ્ય",
        "check_elig_btn": "પાત્રતા ચકાસો",
        "no_schemes": "કોઈ યોજના મળી નહીં. ફિલ્ટર બદલીને જુઓ.",
        "matching_schemes": "{count} મેળ ખાતી યોજનાઓ મળી!",
        "no_matching": "વર્તમાન માપદંડોથી કોઈ યોજના મળી નહીં",
        "connect_backend": "યોજનાઓ જોવા બેકએન્ડ સાથે કનેક્ટ કરો",
        "tts_failed": "TTS નિષ્ફળ, ફરી પ્રયાસ કરો.",
        "tts_connect_fail": "TTS સેવા સાથે કનેક્ટ થઈ શકાયું નહીં.",
        "voice_failed": "અવાજ પ્રક્રિયા નિષ્ફળ",
        "backend_error": "બેકએન્ડ સર્વર સાથે કનેક્ટ થઈ શકાયું નહીં.",
        "error_retry": "માફ કરશો, ભૂલ થઈ. ફરી પ્રયાસ કરો.",
        "backend_not_running": "બેકએન્ડ સર્વર સાથે કનેક્ટ થઈ શકાયું નહીં. ચાલુ છે તેની ખાતરી કરો.",
    },
    "kn-IN": {
        "settings": "⚙️ ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
        "your_state": "📍 ನಿಮ್ಮ ರಾಜ್ಯ",
        "district": "🏘️ ಜಿಲ್ಲೆ (ಐಚ್ಛಿಕ)",
        "language": "🌐 ಭಾಷೆ",
        "quick_actions": "⚡ ತ್ವರಿತ ಕ್ರಿಯೆಗಳು",
        "browse_schemes": "📋 ಯೋಜನೆಗಳನ್ನು ನೋಡಿ",
        "check_eligibility": "✅ ಅರ್ಹತೆ ಪರಿಶೀಲಿಸಿ",
        "footer": "ನಾಗರಿಕಮಿತ್ರ v1.0 | Sarvam AI ಮೂಲಕ",
        "header_title": "🏛️ ನಾಗರಿಕಮಿತ್ರ",
        "header_subtitle": "AI-ಚಾಲಿತ ಬಹುಭಾಷಾ ನಾಗರಿಕ ಸೇವಾ ಸಹಾಯಕ",
        "header_powered": "Sarvam AI ಮೂಲಕ | ೧೧ ಭಾರತೀಯ ಭಾಷೆಗಳು",
        "chat_title": "💬 ನಾಗರಿಕಮಿತ್ರದೊಂದಿಗೆ ಚಾಟ್",
        "chat_placeholder": "ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ಟೈಪ್ ಮಾಡಿ...",
        "voice_label": "🎤 ನಿಮ್ಮ ಧ್ವನಿ ರೆಕಾರ್ಡ್ ಮಾಡಿ",
        "listen": "🔊 ಕೇಳಿ",
        "processing_voice": "🎧 ಧ್ವನಿ ಪ್ರಕ್ರಿಯೆ ಆಗುತ್ತಿದೆ...",
        "schemes_tab": "📋 ಯೋಜನೆಗಳು",
        "eligibility_tab": "✅ ಅರ್ಹತೆ",
        "govt_schemes": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು",
        "filter_category": "ವರ್ಗದ ಮೂಲಕ ಫಿಲ್ಟರ್",
        "check_your_eligibility": "ನಿಮ್ಮ ಅರ್ಹತೆ ಪರಿಶೀಲಿಸಿ",
        "your_age": "ನಿಮ್ಮ ವಯಸ್ಸು",
        "annual_income": "ವಾರ್ಷಿಕ ಆದಾಯ (₹)",
        "gender": "ಲಿಂಗ",
        "male": "ಪುರುಷ",
        "female": "ಮಹಿಳೆ",
        "occupation": "ವೃತ್ತಿ (ಉದಾ., ರೈತ, ವಿದ್ಯಾರ್ಥಿ)",
        "state": "ರಾಜ್ಯ",
        "check_elig_btn": "ಅರ್ಹತೆ ಪರಿಶೀಲಿಸಿ",
        "no_schemes": "ಯೋಜನೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ. ಫಿಲ್ಟರ್ ಬದಲಾಯಿಸಿ ನೋಡಿ.",
        "matching_schemes": "{count} ಹೊಂದಾಣಿಕೆಯ ಯೋಜನೆಗಳು ಕಂಡುಬಂದವು!",
        "no_matching": "ಪ್ರಸ್ತುತ ಮಾನದಂಡಗಳೊಂದಿಗೆ ಯೋಜನೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ",
        "connect_backend": "ಯೋಜನೆಗಳನ್ನು ನೋಡಲು ಬ್ಯಾಕೆಂಡ್‌ಗೆ ಸಂಪರ್ಕಿಸಿ",
        "tts_failed": "TTS ವಿಫಲ, ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        "tts_connect_fail": "TTS ಸೇವೆಗೆ ಸಂಪರ್ಕಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.",
        "voice_failed": "ಧ್ವನಿ ಪ್ರಕ್ರಿಯೆ ವಿಫಲ",
        "backend_error": "ಬ್ಯಾಕೆಂಡ್ ಸರ್ವರ್‌ಗೆ ಸಂಪರ್ಕಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.",
        "error_retry": "ಕ್ಷಮಿಸಿ, ದೋಷ ಸಂಭವಿಸಿದೆ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        "backend_not_running": "ಬ್ಯಾಕೆಂಡ್ ಸರ್ವರ್‌ಗೆ ಸಂಪರ್ಕಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ಚಾಲನೆಯಲ್ಲಿದೆ ಎಂದು ಖಚಿತಪಡಿಸಿ.",
    },
    "ml-IN": {
        "settings": "⚙️ ക്രമീകരണങ്ങൾ",
        "your_state": "📍 നിങ്ങളുടെ സംസ്ഥാനം",
        "district": "🏘️ ജില്ല (ഐച്ഛികം)",
        "language": "🌐 ഭാഷ",
        "quick_actions": "⚡ ദ്രുത പ്രവർത്തനങ്ങൾ",
        "browse_schemes": "📋 പദ്ധതികൾ കാണുക",
        "check_eligibility": "✅ യോഗ്യത പരിശോധിക്കുക",
        "footer": "നാഗരിക്മിത്ര v1.0 | Sarvam AI വഴി",
        "header_title": "🏛️ നാഗരിക്മിത്ര",
        "header_subtitle": "AI-പ്രവർത്തിത ബഹുഭാഷാ പൗര സേവന സഹായി",
        "header_powered": "Sarvam AI വഴി | 11 ഇന്ത്യൻ ഭാഷകൾ",
        "chat_title": "💬 നാഗരിക്മിത്രയുമായി ചാറ്റ്",
        "chat_placeholder": "നിങ്ങളുടെ സന്ദേശം ടൈപ്പ് ചെയ്യുക...",
        "voice_label": "🎤 നിങ്ങളുടെ ശബ്ദം റെക്കോർഡ് ചെയ്യുക",
        "listen": "🔊 കേൾക്കുക",
        "processing_voice": "🎧 ശബ്ദം പ്രോസസ്സ് ചെയ്യുന്നു...",
        "schemes_tab": "📋 പദ്ധതികൾ",
        "eligibility_tab": "✅ യോഗ്യത",
        "govt_schemes": "സർക്കാർ പദ്ധതികൾ",
        "filter_category": "വിഭാഗം അനുസരിച്ച് ഫിൽട്ടർ",
        "check_your_eligibility": "നിങ്ങളുടെ യോഗ്യത പരിശോധിക്കുക",
        "your_age": "നിങ്ങളുടെ പ്രായം",
        "annual_income": "വാർഷിക വരുമാനം (₹)",
        "gender": "ലിംഗം",
        "male": "പുരുഷൻ",
        "female": "സ്ത്രീ",
        "occupation": "തൊഴിൽ (ഉദാ., കർഷകൻ, വിദ്യാർത്ഥി)",
        "state": "സംസ്ഥാനം",
        "check_elig_btn": "യോഗ്യത പരിശോധിക്കുക",
        "no_schemes": "പദ്ധതികൾ കണ്ടെത്തിയില്ല. ഫിൽട്ടർ മാറ്റി നോക്കുക.",
        "matching_schemes": "{count} പൊരുത്തമുള്ള പദ്ധതികൾ കണ്ടെത്തി!",
        "no_matching": "നിലവിലെ മാനദണ്ഡങ്ങളിൽ പദ്ധതികൾ കണ്ടെത്തിയില്ല",
        "connect_backend": "പദ്ധതികൾ കാണാൻ ബാക്കെൻഡിലേക്ക് കണക്റ്റ് ചെയ്യുക",
        "tts_failed": "TTS പരാജയപ്പെട്ടു, വീണ്ടും ശ്രമിക്കുക.",
        "tts_connect_fail": "TTS സേവനത്തിലേക്ക് കണക്റ്റ് ചെയ്യാൻ കഴിഞ്ഞില്ല.",
        "voice_failed": "ശബ്ദ പ്രോസസ്സിംഗ് പരാജയപ്പെട്ടു",
        "backend_error": "ബാക്കെൻഡ് സെർവറിലേക്ക് കണക്റ്റ് ചെയ്യാൻ കഴിഞ്ഞില്ല.",
        "error_retry": "ക്ഷമിക്കുക, ഒരു പിശക് സംഭവിച്ചു. വീണ്ടും ശ്രമിക്കുക.",
        "backend_not_running": "ബാക്കെൻഡ് സെർവറിലേക്ക് കണക്റ്റ് ചെയ്യാൻ കഴിഞ്ഞില്ല. പ്രവർത്തിക്കുന്നുണ്ടെന്ന് ഉറപ്പാക്കുക.",
    },
    "od-IN": {
        "settings": "⚙️ ସେଟିଂସ୍",
        "your_state": "📍 ଆପଣଙ୍କ ରାଜ୍ୟ",
        "district": "🏘️ ଜିଲ୍ଲା (ଐଚ୍ଛିକ)",
        "language": "🌐 ଭାଷା",
        "quick_actions": "⚡ ଦ୍ରୁତ କାର୍ଯ୍ୟ",
        "browse_schemes": "📋 ଯୋଜନା ଦେଖନ୍ତୁ",
        "check_eligibility": "✅ ଯୋଗ୍ୟତା ଯାଞ୍ଚ",
        "footer": "ନାଗରିକମିତ୍ର v1.0 | Sarvam AI ଦ୍ୱାରା",
        "header_title": "🏛️ ନାଗରିକମିତ୍ର",
        "header_subtitle": "AI-ଚାଳିତ ବହୁଭାଷା ନାଗରିକ ସେବା ସହାୟକ",
        "header_powered": "Sarvam AI ଦ୍ୱାରା | ୧୧ ଭାରତୀୟ ଭାଷା",
        "chat_title": "💬 ନାଗରିକମିତ୍ର ସହ ଚାଟ୍",
        "chat_placeholder": "ଆପଣଙ୍କ ସନ୍ଦେଶ ଲେଖନ୍ତୁ...",
        "voice_label": "🎤 ଆପଣଙ୍କ ସ୍ୱର ରେକର୍ଡ କରନ୍ତୁ",
        "listen": "🔊 ଶୁଣନ୍ତୁ",
        "processing_voice": "🎧 ସ୍ୱର ପ୍ରକ୍ରିୟା ହେଉଛି...",
        "schemes_tab": "📋 ଯୋଜନା",
        "eligibility_tab": "✅ ଯୋଗ୍ୟତା",
        "govt_schemes": "ସରକାରୀ ଯୋଜନା",
        "filter_category": "ବିଭାଗ ଅନୁସାରେ ଫିଲ୍ଟର",
        "check_your_eligibility": "ଆପଣଙ୍କ ଯୋଗ୍ୟତା ଯାଞ୍ଚ କରନ୍ତୁ",
        "your_age": "ଆପଣଙ୍କ ବୟସ",
        "annual_income": "ବାର୍ଷିକ ଆୟ (₹)",
        "gender": "ଲିଙ୍ଗ",
        "male": "ପୁରୁଷ",
        "female": "ମହିଳା",
        "occupation": "ପେଶା (ଯଥା, ଚାଷୀ, ଛାତ୍ର)",
        "state": "ରାଜ୍ୟ",
        "check_elig_btn": "ଯୋଗ୍ୟତା ଯାଞ୍ଚ",
        "no_schemes": "କୌଣସି ଯୋଜନା ମିଳିଲା ନାହିଁ। ଫିଲ୍ଟର ବଦଳାଇ ଦେଖନ୍ତୁ।",
        "matching_schemes": "{count} ମେଳ ଖାଉଥିବା ଯୋଜନା ମିଳିଲା!",
        "no_matching": "ବର୍ତ୍ତମାନ ମାନଦଣ୍ଡରେ କୌଣସି ଯୋଜନା ମିଳିଲା ନାହିଁ",
        "connect_backend": "ଯୋଜନା ଦେଖିବାକୁ ବ୍ୟାକେଣ୍ଡ ସହ ସଂଯୋଗ କରନ୍ତୁ",
        "tts_failed": "TTS ବିଫଳ, ପୁନଃ ଚେଷ୍ଟା କରନ୍ତୁ।",
        "tts_connect_fail": "TTS ସେବା ସହ ସଂଯୋଗ ହୋଇପାରିଲା ନାହିଁ।",
        "voice_failed": "ସ୍ୱର ପ୍ରକ୍ରିୟା ବିଫଳ",
        "backend_error": "ବ୍ୟାକେଣ୍ଡ ସର୍ଭର ସହ ସଂଯୋଗ ହୋଇପାରିଲା ନାହିଁ।",
        "error_retry": "କ୍ଷମା କରନ୍ତୁ, ତ୍ରୁଟି ହୋଇଛି। ପୁନଃ ଚେଷ୍ଟା କରନ୍ତୁ।",
        "backend_not_running": "ବ୍ୟାକେଣ୍ଡ ସର୍ଭର ସହ ସଂଯୋଗ ହୋଇପାରିଲା ନାହିଁ। ଚାଲୁଛି କି ନିଶ୍ଚିତ କରନ୍ତୁ।",
    },
    "pa-IN": {
        "settings": "⚙️ ਸੈਟਿੰਗਾਂ",
        "your_state": "📍 ਤੁਹਾਡਾ ਰਾਜ",
        "district": "🏘️ ਜ਼ਿਲ੍ਹਾ (ਵਿਕਲਪਿਕ)",
        "language": "🌐 ਭਾਸ਼ਾ",
        "quick_actions": "⚡ ਤੇਜ਼ ਕਿਰਿਆਵਾਂ",
        "browse_schemes": "📋 ਯੋਜਨਾਵਾਂ ਵੇਖੋ",
        "check_eligibility": "✅ ਯੋਗਤਾ ਜਾਂਚੋ",
        "footer": "ਨਾਗਰਿਕਮਿੱਤਰ v1.0 | Sarvam AI ਦੁਆਰਾ",
        "header_title": "🏛️ ਨਾਗਰਿਕਮਿੱਤਰ",
        "header_subtitle": "AI-ਸੰਚਾਲਿਤ ਬਹੁਭਾਸ਼ੀ ਨਾਗਰਿਕ ਸੇਵਾ ਸਹਾਇਕ",
        "header_powered": "Sarvam AI ਦੁਆਰਾ | ੧੧ ਭਾਰਤੀ ਭਾਸ਼ਾਵਾਂ",
        "chat_title": "💬 ਨਾਗਰਿਕਮਿੱਤਰ ਨਾਲ ਗੱਲ ਕਰੋ",
        "chat_placeholder": "ਆਪਣਾ ਸੁਨੇਹਾ ਲਿਖੋ...",
        "voice_label": "🎤 ਆਪਣੀ ਆਵਾਜ਼ ਰਿਕਾਰਡ ਕਰੋ",
        "listen": "🔊 ਸੁਣੋ",
        "processing_voice": "🎧 ਆਵਾਜ਼ ਪ੍ਰੋਸੈਸ ਹੋ ਰਹੀ ਹੈ...",
        "schemes_tab": "📋 ਯੋਜਨਾਵਾਂ",
        "eligibility_tab": "✅ ਯੋਗਤਾ",
        "govt_schemes": "ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ",
        "filter_category": "ਸ਼੍ਰੇਣੀ ਅਨੁਸਾਰ ਫ਼ਿਲਟਰ",
        "check_your_eligibility": "ਆਪਣੀ ਯੋਗਤਾ ਜਾਂਚੋ",
        "your_age": "ਤੁਹਾਡੀ ਉਮਰ",
        "annual_income": "ਸਾਲਾਨਾ ਆਮਦਨ (₹)",
        "gender": "ਲਿੰਗ",
        "male": "ਪੁਰਸ਼",
        "female": "ਔਰਤ",
        "occupation": "ਕਿੱਤਾ (ਜਿਵੇਂ, ਕਿਸਾਨ, ਵਿਦਿਆਰਥੀ)",
        "state": "ਰਾਜ",
        "check_elig_btn": "ਯੋਗਤਾ ਜਾਂਚੋ",
        "no_schemes": "ਕੋਈ ਯੋਜਨਾ ਨਹੀਂ ਮਿਲੀ। ਫ਼ਿਲਟਰ ਬਦਲ ਕੇ ਵੇਖੋ।",
        "matching_schemes": "{count} ਮੇਲ ਖਾਂਦੀਆਂ ਯੋਜਨਾਵਾਂ ਮਿਲੀਆਂ!",
        "no_matching": "ਮੌਜੂਦਾ ਮਾਪਦੰਡਾਂ ਨਾਲ ਕੋਈ ਯੋਜਨਾ ਨਹੀਂ ਮਿਲੀ",
        "connect_backend": "ਯੋਜਨਾਵਾਂ ਵੇਖਣ ਲਈ ਬੈਕਐਂਡ ਨਾਲ ਕਨੈਕਟ ਕਰੋ",
        "tts_failed": "TTS ਅਸਫ਼ਲ, ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
        "tts_connect_fail": "TTS ਸੇਵਾ ਨਾਲ ਕਨੈਕਟ ਨਹੀਂ ਹੋ ਸਕਿਆ।",
        "voice_failed": "ਆਵਾਜ਼ ਪ੍ਰੋਸੈਸਿੰਗ ਅਸਫ਼ਲ",
        "backend_error": "ਬੈਕਐਂਡ ਸਰਵਰ ਨਾਲ ਕਨੈਕਟ ਨਹੀਂ ਹੋ ਸਕਿਆ।",
        "error_retry": "ਮਾਫ਼ ਕਰੋ, ਗਲਤੀ ਹੋਈ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
        "backend_not_running": "ਬੈਕਐਂਡ ਸਰਵਰ ਨਾਲ ਕਨੈਕਟ ਨਹੀਂ ਹੋ ਸਕਿਆ। ਚੱਲ ਰਿਹਾ ਹੈ ਯਕੀਨੀ ਕਰੋ।",
    },
}

# Default to English for Auto-Detect and missing codes
UI_STRINGS[""] = UI_STRINGS["en-IN"]


def t(key: str) -> str:
    """Get translated UI string for the current language."""
    lang_code = LANGUAGES.get(selected_language, "")
    strings = UI_STRINGS.get(lang_code, UI_STRINGS["en-IN"])
    return strings.get(key, UI_STRINGS["en-IN"].get(key, key))

STATES = [
    "", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal",
]

CATEGORIES = [
    "All", "Agriculture", "Education", "Health", "Housing", "Employment",
    "Women & Child", "Social Security", "Financial Inclusion",
    "Rural Development", "Skill Development",
]


# ─── SIDEBAR ─────────────────────────────────────────────────────────

# Language selector first (needed by t() for all other labels)
if "ui_language" not in st.session_state:
    st.session_state.ui_language = "Auto-Detect"

with st.sidebar:
    # Language selector at the top so t() works for remaining labels
    selected_language = st.selectbox("🌐 Language", list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index(st.session_state.ui_language), key="lang_select")

    # Track language change — clear chat so welcome message updates
    if selected_language != st.session_state.ui_language:
        st.session_state.ui_language = selected_language
        st.session_state.chat_history = []
        st.rerun()

    st.markdown(f"### {t('settings')}")

    # Location
    selected_state = st.selectbox(t("your_state"), STATES, index=0)
    district = st.text_input(t("district"))

    st.markdown("---")
    st.markdown(f"### {t('quick_actions')}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("browse_schemes"), use_container_width=True):
            st.session_state.show_schemes = True
    with col2:
        if st.button(t("check_eligibility"), use_container_width=True):
            st.session_state.show_eligibility = True

    st.markdown("---")
    st.caption(t("footer"))


# ─── MAIN CONTENT ────────────────────────────────────────────────────

# Header
st.markdown(f"""
<div class="main-header">
    <h1>{t('header_title')}</h1>
    <p>{t('header_subtitle')}</p>
    <p style="font-size: 0.8rem; opacity: 0.7;">{t('header_powered')}</p>
</div>
""", unsafe_allow_html=True)

# Main layout: Chat (left) + Info Panel (right)
# Responsive columns: 1 column on mobile, 2 on desktop
chat_col, info_col = st.columns([3, 2])

# ─── CHAT INTERFACE ──────────────────────────────────────────────────

with chat_col:
    st.markdown(f"### {t('chat_title')}")

    # Play pending voice response audio
    if st.session_state.get("pending_audio"):
        st.audio(st.session_state.pending_audio, format="audio/wav", autoplay=True)
        st.session_state.pending_audio = None

    # Display chat history
    chat_container = st.container(height=450)
    with chat_container:
        if not st.session_state.chat_history:
            lang_code = LANGUAGES.get(selected_language, "")
            welcome = WELCOME_MESSAGES.get(lang_code, WELCOME_MESSAGES[""])
            with st.chat_message("assistant"):
                st.markdown(welcome)

        for msg_idx, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])

                    if msg.get("meta"):
                        meta = msg["meta"]
                        chips = []
                        if meta.get("detected_language"):
                            chips.append(f'<span class="info-chip">🌐 {meta["detected_language"]}</span>')
                        if meta.get("intent"):
                            chips.append(f'<span class="info-chip">🎯 {meta["intent"]}</span>')
                        if meta.get("from_cache"):
                            chips.append(f'<span class="info-chip">⚡ Cached</span>')
                        if meta.get("pii_detected"):
                            chips.append(f'<span class="info-chip">🔒 PII Masked</span>')
                        if chips:
                            st.markdown(f'<div class="pipeline-info">{"".join(chips)}</div>', unsafe_allow_html=True)

                # Listen button
                if st.button(t("listen"), key=f"listen_{msg_idx}"):
                    lang = LANGUAGES.get(selected_language, "") or msg.get("meta", {}).get("detected_language", "hi-IN") or "hi-IN"
                    import re
                    clean_text = msg["content"]
                    clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_text)
                    clean_text = re.sub(r'\*(.+?)\*', r'\1', clean_text)
                    clean_text = re.sub(r'#{1,6}\s*', '', clean_text)
                    clean_text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean_text)
                    clean_text = re.sub(r'[`~\*]', '', clean_text)
                    try:
                        tts_resp = requests.post(
                            f"{API_BASE}/api/tts",
                            data={
                                "text": clean_text[:500],
                                "language_code": lang,
                            },
                            timeout=30,
                        )
                        if tts_resp.status_code == 200:
                            st.audio(tts_resp.content, format="audio/wav", autoplay=True)
                        else:
                            st.toast(t("tts_failed"))
                    except Exception:
                        st.toast(t("tts_connect_fail"))

    # Input area
    user_input = st.chat_input(t("chat_placeholder"))

    # Voice input
    audio_input = st.audio_input(t("voice_label"))
    if audio_input:
        audio_id = hash(audio_input.getvalue())
        if audio_id != st.session_state.get("last_audio_id"):
            st.session_state.last_audio_id = audio_id
            with st.spinner(t("processing_voice")):
                try:
                    files = {"audio": ("recording.wav", audio_input.getvalue(), "audio/wav")}
                    data = {
                        "session_id": st.session_state.session_id,
                        "state": selected_state or "",
                        "language_preference": LANGUAGES.get(selected_language, ""),
                    }
                    response = requests.post(
                        f"{API_BASE}/api/voice",
                        files=files,
                        data=data,
                        timeout=60,
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": f"🎤 {result['transcribed_text']}",
                        })
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": result["response_text"],
                            "meta": {
                                "detected_language": result.get("detected_language", ""),
                                "intent": result.get("intent", ""),
                            },
                        })
                        if result.get("audio_base64"):
                            st.session_state.pending_audio = base64.b64decode(result["audio_base64"])
                        st.rerun()
                    else:
                        st.error(f"{t('voice_failed')}: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error(t("backend_error"))
                except Exception as e:
                    st.error(f"{t('voice_failed')}: {e}")

    # Process text input
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        try:
            response = requests.post(
                f"{API_BASE}/api/chat",
                json={
                    "message": user_input,
                    "session_id": st.session_state.session_id,
                    "state": selected_state or None,
                    "district": district or None,
                    "language_preference": LANGUAGES.get(selected_language, ""),
                },
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": data["response"],
                    "meta": {
                        "detected_language": data.get("detected_language", ""),
                        "intent": data.get("intent", ""),
                        "from_cache": data.get("from_cache", False),
                        "pii_detected": data.get("pii_detected", False),
                        "schemes_referenced": data.get("schemes_referenced", []),
                    },
                })
                # Update scheme cards if schemes were referenced
                if data.get("schemes_referenced"):
                    st.session_state.selected_schemes = data["schemes_referenced"]
            else:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": t("error_retry"),
                })
        except requests.exceptions.ConnectionError:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": t("backend_not_running"),
            })
        except Exception as e:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Error: {str(e)}",
            })
        st.rerun()


# ─── INFO PANEL ──────────────────────────────────────────────────────

with info_col:
    tab1, tab2 = st.tabs([t("eligibility_tab"), t("schemes_tab")])

    # ── Eligibility Tab ─────────────────────────────────────────
    with tab1:
        st.markdown(f"#### {t('check_your_eligibility')}")

        with st.form("eligibility_form"):
            elig_age = st.number_input(t("your_age"), min_value=0, max_value=120, value=30)
            elig_income = st.number_input(t("annual_income"), min_value=0, value=200000, step=50000)
            elig_gender = st.selectbox(t("gender"), [t("male"), t("female")])
            elig_occupation = st.text_input(t("occupation"))
            elig_state = st.selectbox(t("state"), STATES[1:], key="elig_state")

            if st.form_submit_button(t("check_elig_btn"), type="primary"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/eligibility",
                        json={
                            "age": elig_age,
                            "income": elig_income,
                            "gender": elig_gender,
                            "state": elig_state,
                            "occupation": elig_occupation,
                        },
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        results = resp.json()
                        if results:
                            st.success(t("matching_schemes").format(count=len(results)))
                            for r in results:
                                icon = "✅" if r["eligible"] else "❌"
                                st.markdown(f"""
                                **{icon} {r['scheme_name']}**
                                - Match Score: {'⭐' * int(r['match_score'] * 5)}
                                - {', '.join(r['reasons'][:3])}
                                """)
                                if r.get("missing_criteria"):
                                    st.caption(f"ℹ️ Missing: {', '.join(r['missing_criteria'])}")
                        else:
                            st.warning(t("no_matching"))
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── Schemes Tab ─────────────────────────────────────────────
    with tab2:
        st.markdown(f"#### {t('govt_schemes')}")

        scheme_cat = st.selectbox(t("filter_category"), CATEGORIES, key="scheme_cat")
        try:
            params = {}
            if selected_state:
                params["state"] = selected_state
            if scheme_cat and scheme_cat != "All":
                params["category"] = scheme_cat
            resp = requests.get(f"{API_BASE}/api/schemes", params=params, timeout=5)
            if resp.status_code == 200:
                schemes = resp.json()
                if not schemes:
                    st.info(t("no_schemes"))
                for scheme in schemes[:10]:
                    badge_type = "badge-central" if scheme.get("is_central") else "badge-state"
                    badge_label = "Central" if scheme.get("is_central") else "State"
                    st.markdown(f"""
                    <div class="scheme-card">
                        <h4>{scheme['name_en']}</h4>
                        <p style="color: #666; font-size: 0.85rem;">{scheme.get('name_hi', '')}</p>
                        <span class="scheme-badge badge-category">{scheme.get('category', '')}</span>
                        <span class="scheme-badge {badge_type}">{badge_label}</span>
                        <p style="margin-top: 0.5rem; font-size: 0.9rem;">{scheme.get('description_en', '')[:150]}...</p>
                        <p style="color: #2e7d32; font-weight: 600;">💰 {scheme.get('benefits', '')[:100]}</p>
                    </div>
                    """, unsafe_allow_html=True)
        except Exception:
            st.info(t("connect_backend"))


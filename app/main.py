"""FastAPI application — NagrikMitra API server.

Routes:
- POST /api/chat          — Text chat through 10-step pipeline
- POST /api/voice         — Voice input (ASR → pipeline → TTS)
- POST /api/document      — Document upload (OCR → process)
- POST /api/grievance     — File a grievance
- GET  /api/grievance/{id}— Check grievance status
- POST /api/feedback      — Submit feedback
- GET  /api/analytics     — Feedback analytics
- GET  /api/schemes       — Browse schemes
- /mock/*                 — Mock government APIs
"""

import base64
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import settings
from app.models import (
    ChatRequest, ChatResponse, VoiceResponse, DocumentResponse,
    GrievanceRequest, FeedbackRequest, EligibilityRequest,
)
from app.services.orchestrator import process_message
from app.services import rag_engine, scheme_service, semantic_cache
from app.services.grievance_service import (
    file_grievance, get_grievance, list_grievances,
)
from app.feedback.collector import submit_feedback, get_analytics
from app.sarvam.client import sarvam_client
from app.mock.government_api import router as mock_router

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown."""
    logger.info("=" * 60)
    logger.info("  NagrikMitra - Unified Citizen Interaction Assistant")
    logger.info("=" * 60)

    # Initialize RAG engine and scheme service
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    try:
        rag_engine.initialize_rag(data_dir)
    except Exception as e:
        logger.error(f"RAG engine init failed: {e}")
    
    try:
        scheme_service.load_schemes(data_dir)
    except Exception as e:
        logger.error(f"Scheme service init failed: {e}")

    # Initialize semantic cache
    try:
        semantic_cache.init()
    except Exception as e:
        logger.error(f"Semantic cache init failed: {e}")

    logger.info("All services initialized successfully")
    yield

    # Cleanup
    await sarvam_client.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="NagrikMitra API",
    description="AI-Powered Unified Multilingual Citizen Service Assistant",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount mock government APIs
app.include_router(mock_router)

@app.get("/")
async def root():
    return {"message": "NagrikMitra API is running successfully!"}


# ─── CHAT ENDPOINT ──────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a text message through the 10-step orchestrator pipeline."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return await process_message(request)


# ─── VOICE ENDPOINT ─────────────────────────────────────────────────

@app.post("/api/voice", response_model=VoiceResponse)
async def voice(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
    state: str = Form(default=""),
    language_preference: str = Form(default=""),
):
    """Process voice input: ASR → Pipeline → TTS.

    Uses Sarvam Speech-to-Text and Text-to-Speech APIs.
    Ensures output language matches input language preference.
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    sid = session_id or uuid.uuid4().hex[:16]

    # Step 1: Speech-to-Text (Sarvam ASR — use language_preference if set, else auto-detect)
    try:
        transcribed_text = await sarvam_client.speech_to_text(
            audio_bytes=audio_bytes,
            language_code=language_preference or None,
        )
        logger.info(f"[Voice] ASR completed. Language: {language_preference or 'auto-detected'}")
    except Exception as e:
        logger.error(f"ASR failed: {e}")
        raise HTTPException(status_code=500, detail="Speech recognition failed")

    if not transcribed_text.strip():
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    # Step 2: Process through chat pipeline (pass language_preference so pipeline responds in selected language)
    chat_request = ChatRequest(
        message=transcribed_text,
        session_id=sid,
        state=state or None,
        language_preference=language_preference or None,
    )
    chat_response = await process_message(chat_request)
    logger.info(f"[Voice] Response language: {chat_response.detected_language}")

    # Step 3: Text-to-Speech (ensure output language matches input language)
    # If explicit language_preference was provided, use it. Otherwise use detected language from response.
    if language_preference:
        tts_language = language_preference
        logger.info(f"[Voice] Using explicit language preference for TTS: {tts_language}")
    else:
        tts_language = chat_response.detected_language
        logger.info(f"[Voice] Using detected language for TTS: {tts_language}")
    
    audio_base64 = None
    try:
        # Clean special characters and asterisks that TTS shouldn't pronounce
        cleaned_response = re.sub(r'[*`~]', '', chat_response.response)[:500]
        
        tts_audio = await sarvam_client.text_to_speech(
            text=cleaned_response,
            language_code=tts_language,
        )
        if tts_audio:
            audio_base64 = base64.b64encode(tts_audio).decode("utf-8")
            logger.info(f"[Voice] TTS audio generated successfully in {tts_language}")
    except Exception as e:
        logger.warning(f"TTS failed (continuing without audio): {e}")

    return VoiceResponse(
        transcribed_text=transcribed_text,
        response_text=chat_response.response,
        audio_base64=audio_base64,
        detected_language=chat_response.detected_language,
        intent=chat_response.intent,
        session_id=sid,
    )


# ─── DOCUMENT ENDPOINT ──────────────────────────────────────────────

@app.post("/api/document", response_model=DocumentResponse)
async def process_document(
    file: UploadFile = File(...),
    session_id: str = Form(default=""),
):
    """Upload a document for OCR processing using Sarvam Document Intelligence API."""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Determine file type
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
    if ext not in ("pdf", "jpg", "jpeg", "png"):
        raise HTTPException(status_code=400, detail="Supported formats: PDF, JPG, PNG")

    file_type = "pdf" if ext == "pdf" else "image"

    # Call Sarvam Document OCR API
    try:
        extracted_text = await sarvam_client.document_ocr(
            file_bytes=file_bytes,
            file_type=file_type,
        )
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail="Document processing failed")

    # Detect language of extracted text
    lang_result = await sarvam_client.detect_language(extracted_text[:500])

    # Generate summary through chat pipeline
    summary = None
    if extracted_text.strip():
        try:
            summary_request = ChatRequest(
                message=f"Summarize this document content briefly: {extracted_text[:1000]}",
                session_id=session_id or uuid.uuid4().hex[:16],
            )
            summary_response = await process_message(summary_request)
            summary = summary_response.response
        except Exception:
            pass

    return DocumentResponse(
        extracted_text=extracted_text,
        language_detected=lang_result["language_code"],
        summary=summary,
        document_type=file_type,
    )


# ─── GRIEVANCE ENDPOINTS ────────────────────────────────────────────

@app.post("/api/grievance")
async def create_grievance(request: GrievanceRequest):
    """File a new grievance."""
    ticket = file_grievance(request)
    return ticket


@app.get("/api/grievance/{ticket_id}")
async def get_grievance_status(ticket_id: str):
    """Check grievance status by ticket ID."""
    ticket = get_grievance(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found")
    return ticket


@app.get("/api/grievances")
async def get_all_grievances(state: str = None):
    """List all grievances."""
    return list_grievances(state)


# ─── FEEDBACK ENDPOINT ──────────────────────────────────────────────

@app.post("/api/feedback")
async def submit_user_feedback(request: FeedbackRequest):
    """Submit user feedback for a response."""
    entry = submit_feedback(request)
    return entry


@app.get("/api/analytics")
async def feedback_analytics():
    """Get feedback analytics dashboard data."""
    return get_analytics()


# ─── SCHEME ENDPOINTS ────────────────────────────────────────────────

@app.get("/api/schemes")
async def browse_schemes(state: str = None, category: str = None, query: str = None):
    """Browse available government schemes."""
    return scheme_service.search_schemes(query=query or "", state=state, category=category)


@app.post("/api/eligibility")
async def check_eligibility(request: EligibilityRequest):
    """Check eligibility for schemes."""
    results = scheme_service.check_eligibility(request)
    return results


# ─── TTS ENDPOINT ───────────────────────────────────────────────────

@app.post("/api/tts")
async def text_to_speech(
    text: str = Form(...),
    language_code: str = Form(default="hi-IN"),
):
    """Convert text to speech audio using Sarvam Bulbul TTS."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        # Clean special characters and asterisks that TTS shouldn't pronounce
        cleaned_text = re.sub(r'[*`~]', '', text)[:500]
        
        logger.info(f"[TTS] Converting text to speech in language: {language_code}")
        audio_bytes = await sarvam_client.text_to_speech(
            text=cleaned_text,
            language_code=language_code,
        )
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="TTS returned empty audio")
        logger.info(f"[TTS] Audio generated successfully for language: {language_code}")
        return Response(content=audio_bytes, media_type="audio/wav")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS failed for language {language_code}: {e}")
        raise HTTPException(status_code=500, detail="Text-to-speech failed")


# ─── UTILITY ENDPOINTS ───────────────────────────────────────────────

@app.get("/api/token-usage")
async def get_token_usage():
    """Get current Sarvam API token/call usage statistics."""
    return sarvam_client.get_token_usage()


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "sarvam_configured": bool(settings.SARVAM_API_KEY),
        "tavily_configured": bool(settings.TAVILY_API_KEY),
        "semantic_cache": semantic_cache.get_stats(),
    }

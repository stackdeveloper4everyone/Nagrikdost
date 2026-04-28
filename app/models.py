"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# --- Enums ---

class IntentType(str, Enum):
    SCHEME_QUERY = "scheme_query"
    ELIGIBILITY_CHECK = "eligibility_check"
    GRIEVANCE_FILE = "grievance_file"
    GRIEVANCE_STATUS = "grievance_status"
    DOCUMENT_QUERY = "document_query"
    GENERAL = "general"
    GREETING = "greeting"


class GrievanceStatus(str, Enum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


# --- Chat ---

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000, description="User message text")
    session_id: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    language_preference: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    detected_language: str
    intent: str
    session_id: str
    schemes_referenced: List[str] = []
    pii_detected: bool = False
    from_cache: bool = False
    token_usage: Dict[str, int] = {}


# --- Voice ---

class VoiceResponse(BaseModel):
    transcribed_text: str
    response_text: str
    audio_base64: Optional[str] = None
    detected_language: str
    intent: str
    session_id: str


# --- Schemes ---

class SchemeEligibility(BaseModel):
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    max_income: Optional[int] = None
    gender: Optional[str] = None
    category: Optional[List[str]] = None
    states: Optional[List[str]] = None  # None = all states (central scheme)
    occupation: Optional[List[str]] = None
    other_criteria: List[str] = []


class Scheme(BaseModel):
    id: str
    name_en: str
    name_hi: str
    category: str
    description_en: str
    description_hi: str
    eligibility: SchemeEligibility
    benefits: str
    required_documents: List[str]
    application_url: Optional[str] = None
    ministry: str
    is_central: bool = True
    states: Optional[List[str]] = None


class EligibilityRequest(BaseModel):
    scheme_id: Optional[str] = None
    age: Optional[int] = None
    income: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    occupation: Optional[str] = None


class EligibilityResult(BaseModel):
    scheme_id: str
    scheme_name: str
    eligible: bool
    reasons: List[str] = []
    missing_criteria: List[str] = []
    match_score: float = 0.0


# --- Grievance ---

class GrievanceRequest(BaseModel):
    subject: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    category: str
    state: str
    district: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class GrievanceTicket(BaseModel):
    ticket_id: str
    subject: str
    description: str
    category: str
    state: str
    district: Optional[str] = None
    status: GrievanceStatus = GrievanceStatus.SUBMITTED
    created_at: datetime
    updated_at: datetime
    resolution_notes: Optional[str] = None
    documents: List[str] = []


# --- Feedback ---

class FeedbackRequest(BaseModel):
    session_id: str
    message_index: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class FeedbackEntry(BaseModel):
    id: str
    session_id: str
    message_index: int
    rating: int
    comment: Optional[str] = None
    timestamp: datetime
    detected_intent: Optional[str] = None
    detected_language: Optional[str] = None


class FeedbackAnalytics(BaseModel):
    total_interactions: int
    average_rating: float
    total_feedback: int
    rating_distribution: Dict[int, int]
    top_intents: Dict[str, int]
    language_distribution: Dict[str, int]
    satisfaction_trend: List[Dict[str, Any]]


# --- Document ---

class DocumentResponse(BaseModel):
    extracted_text: str
    language_detected: str
    summary: Optional[str] = None
    document_type: Optional[str] = None


# --- Pipeline Internal ---

class PipelineContext(BaseModel):
    """Internal context passed through the 10-step orchestrator pipeline."""
    original_input: str
    masked_input: Optional[str] = None
    pii_map: Dict[str, str] = {}
    detected_language: str = "en-IN"
    intent: IntentType = IntentType.GENERAL
    rag_context: str = ""
    llm_response: str = ""
    translated_response: str = ""
    final_response: str = ""
    from_cache: bool = False
    token_usage: Dict[str, int] = {}
    risk_score: float = 0.0
    session_id: str = ""
    state: Optional[str] = None
    district: Optional[str] = None
    schemes_referenced: List[str] = []
    pii_detected: bool = False

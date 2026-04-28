"""Configuration management using Pydantic Settings."""

import os
from pydantic_settings import BaseSettings
from typing import Dict, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Sarvam AI
    SARVAM_API_KEY: str = ""
    SARVAM_BASE_URL: str = "https://api.sarvam.ai"

    # Application
    APP_NAME: str = "NagrikMitra - Unified Citizen Interaction Assistant"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    STREAMLIT_PORT: int = 8501

    # Security
    MAX_INPUT_LENGTH: int = 2000
    PROMPT_GUARD_THRESHOLD: float = 0.7
    RATE_LIMIT_PER_MINUTE: int = 30

    # Tavily Web Search
    TAVILY_API_KEY: str = ""
    TAVILY_SEARCH_DEPTH: str = "basic"
    TAVILY_MAX_RESULTS: int = 5

    # Semantic Cache (Qdrant)
    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_SIZE: int = 500
    CACHE_SIMILARITY_THRESHOLD: float = 0.85
    QDRANT_PERSIST_PATH: str = ""  # empty = in-memory, or set a directory path for persistence
    QDRANT_URL: str = ""  # e.g. http://localhost:6333 — when set, connects to external Qdrant server

    # Token Optimization (higher values for reasoning models that use thinking tokens)
    MAX_TOKENS_GENERAL: int = 1024
    MAX_TOKENS_SCHEME_DETAIL: int = 1500
    MAX_TOKENS_ELIGIBILITY: int = 1200

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Supported Indian languages with Sarvam language codes
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "mr-IN": "Marathi",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "od-IN": "Odia",
    "pa-IN": "Punjabi",
    "en-IN": "English",
}

# State list for location-aware filtering
INDIAN_STATES: List[str] = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Jammu & Kashmir", "Ladakh",
]

# Scheme categories
SCHEME_CATEGORIES: List[str] = [
    "Agriculture", "Education", "Health", "Housing", "Employment",
    "Women & Child", "Social Security", "Financial Inclusion",
    "Rural Development", "Urban Development", "Skill Development",
]

# Singleton settings instance
settings = Settings()

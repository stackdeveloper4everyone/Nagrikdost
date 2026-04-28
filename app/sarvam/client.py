"""Unified Sarvam AI API client covering all 6 API categories.

APIs used:
1. Language Detection  - POST /api/language/identify
2. Speech-to-Text (ASR) - POST /api/speech-to-text
3. Text-to-Speech (TTS) - POST /api/text-to-speech
4. Translation          - POST /api/translate
5. Chat Completion      - POST /api/chat/completions  (sarvam-m model)
6. Document Intelligence- POST /api/document/ocr
"""

import httpx
import base64
import logging
import re
import time
from typing import Optional, List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class TokenTracker:
    """Track API token usage for optimization metrics."""

    def __init__(self):
        self.usage: Dict[str, int] = {
            "chat_tokens": 0,
            "translate_calls": 0,
            "stt_calls": 0,
            "tts_calls": 0,
            "language_detect_calls": 0,
            "ocr_calls": 0,
            "total_api_calls": 0,
        }

    def track(self, api_type: str, tokens: int = 1):
        self.usage[api_type] = self.usage.get(api_type, 0) + tokens
        self.usage["total_api_calls"] += 1

    def get_usage(self) -> Dict[str, int]:
        return self.usage.copy()

    def reset(self):
        for key in self.usage:
            self.usage[key] = 0


class SarvamClient:
    """Unified client for all Sarvam AI APIs with retry and token tracking."""

    def __init__(self):
        self.base_url = settings.SARVAM_BASE_URL
        self.api_key = settings.SARVAM_API_KEY
        self.tracker = TokenTracker()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "API-Subscription-Key": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
                verify=False,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request with retry logic."""
        client = await self._get_client()
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = await client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Sarvam API error {e.response.status_code}: {e.response.text}")
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.info(f"Rate limited, retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                raise
            except httpx.RequestError as e:
                logger.error(f"Sarvam API request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise

    # ─── 1. LANGUAGE DETECTION ───────────────────────────────────────

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of input text.

        Returns: {"language_code": "hi-IN", "language_name": "Hindi", "confidence": 0.95}
        """
        try:
            result = await self._request(
                "POST",
                "/text-lid",
                json={"input": text},
            )
            self.tracker.track("language_detect_calls")
            lang_code = result.get("language_code", "en-IN")
            return {
                "language_code": lang_code,
                "language_name": result.get("language_name", "English"),
                "confidence": result.get("confidence", 0.0),
            }
        except Exception as e:
            logger.warning(f"Language detection failed, defaulting to en-IN: {e}")
            return {"language_code": "en-IN", "language_name": "English", "confidence": 0.0}

    # ─── 2. SPEECH-TO-TEXT (ASR) ─────────────────────────────────────

    async def speech_to_text(
        self,
        audio_bytes: bytes,
        language_code: str = None,
    ) -> str:
        """Convert speech audio to text using Sarvam Saaras v3 ASR.

        Uses multipart/form-data as required by the API.
        If language_code is None, Saaras v3 auto-detects the language.

        Args:
            audio_bytes: Audio file bytes (WAV/MP3)
            language_code: Optional language code; auto-detected if not provided

        Returns: Transcribed text string
        """
        try:
            form_data = {
                "model": "saaras:v3",
                "mode": "transcribe",
            }
            if language_code:
                form_data["language_code"] = language_code

            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers={"API-Subscription-Key": self.api_key},
                timeout=30.0,
                verify=False,
            ) as client:
                response = await client.post(
                    "/speech-to-text",
                    files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                    data=form_data,
                )
                response.raise_for_status()
                result = response.json()

            self.tracker.track("stt_calls")
            return result.get("transcript", "")
        except Exception as e:
            logger.error(f"Speech-to-text failed: {e}")
            raise

    # ─── 3. TEXT-TO-SPEECH (TTS) ─────────────────────────────────────

    async def text_to_speech(
        self,
        text: str,
        language_code: str = "hi-IN",
        speaker: str = "anushka",
        pace: float = 1.0,
    ) -> bytes:
        """Convert text to natural speech using Sarvam TTS.

        Args:
            text: Text to convert to speech
            language_code: Language code for synthesis
            speaker: Voice model name (meera, arvind, etc.)
            pace: Speech speed (0.5 - 2.0)

        Returns: Audio bytes (WAV format)
        """
        try:
            result = await self._request(
                "POST",
                "/text-to-speech",
                json={
                    "inputs": [text[:500]],
                    "target_language_code": language_code,
                    "speaker": speaker,
                    "pace": pace,
                },
            )
            self.tracker.track("tts_calls")
            audios = result.get("audios", [])
            audio_b64 = audios[0] if audios else ""
            return base64.b64decode(audio_b64) if audio_b64 else b""
        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            raise

    # ─── 4. TRANSLATION ──────────────────────────────────────────────

    async def translate(
        self,
        text: str,
        source_language: str = "en-IN",
        target_language: str = "hi-IN",
    ) -> str:
        """Translate text between Indian languages and English.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code

        Returns: Translated text string
        """
        if source_language == target_language:
            return text

        try:
            result = await self._request(
                "POST",
                "/translate",
                json={
                    "input": text,
                    "source_language_code": source_language,
                    "target_language_code": target_language,
                    "mode": "formal",
                    "model": "mayura:v1",
                    "enable_preprocessing": True,
                },
            )
            self.tracker.track("translate_calls")
            return result.get("translated_text", text)
        except Exception as e:
            logger.warning(f"Translation failed, returning original: {e}")
            return text

    # ─── 5. CHAT COMPLETION (LLM) ────────────────────────────────────

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> Dict[str, Any]:
        """Generate chat completion using Sarvam LLM.

        Args:
            messages: List of {"role": "...", "content": "..."} messages
            temperature: Creativity level (0.0 - 1.0)
            max_tokens: Maximum response tokens

        Returns: {"response": str, "usage": {"prompt_tokens": int, "completion_tokens": int}}
        """
        try:
            result = await self._request(
                "POST",
                "/v1/chat/completions",
                json={
                    "model": "sarvam-m",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            usage = result.get("usage", {})
            # Filter out None values that break Dict[str, int] validation
            usage = {k: v for k, v in usage.items() if v is not None}
            self.tracker.track("chat_tokens", usage.get("total_tokens", 0))

            # Extract response text from the completion
            choices = result.get("choices", [])
            response_text = ""
            if choices:
                response_text = choices[0].get("message", {}).get("content", "")
            # Strip <think>...</think> blocks from reasoning model output
            response_text = re.sub(r"<think>.*?</think>\s*", "", response_text, flags=re.DOTALL)
            # Also strip incomplete <think> blocks (when max_tokens cuts off)
            response_text = re.sub(r"<think>.*", "", response_text, flags=re.DOTALL)
            response_text = response_text.strip()

            return {
                "response": response_text,
                "usage": usage,
            }
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise

    # ─── 6. DOCUMENT INTELLIGENCE (OCR) ──────────────────────────────

    async def document_ocr(
        self,
        file_bytes: bytes,
        file_type: str = "pdf",
    ) -> str:
        """Extract text from documents using Sarvam OCR.

        Args:
            file_bytes: Document file bytes
            file_type: File type (pdf, jpg, png)

        Returns: Extracted text string
        """
        try:
            file_b64 = base64.b64encode(file_bytes).decode("utf-8")
            result = await self._request(
                "POST",
                "/document/ocr",
                json={
                    "input": file_b64,
                    "config": {
                        "file_type": file_type,
                    },
                },
            )
            self.tracker.track("ocr_calls")
            return result.get("text", "")
        except Exception as e:
            logger.error(f"Document OCR failed: {e}")
            raise

    def get_token_usage(self) -> Dict[str, int]:
        """Get current token/API usage statistics."""
        return self.tracker.get_usage()

    def reset_usage(self):
        """Reset usage counters."""
        self.tracker.reset()


# Global client instance
sarvam_client = SarvamClient()

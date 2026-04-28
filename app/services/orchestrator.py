"""10-Step Pipeline Orchestrator — the brain of NagrikMitra.

Every user request flows through this pipeline:
1. Language Detection   → Detect user's language via Sarvam API
2. PII Masking          → Mask sensitive data (Aadhaar, PAN, phone, etc.)
3. Prompt Guard         → Check for injection attacks / off-topic content
4. Cache Check          → Semantic cache lookup to avoid duplicate LLM calls
5. Intent Classification→ Classify what the user wants (scheme, eligibility, grievance, etc.)
6. RAG Retrieval        → Retrieve relevant scheme information from knowledge base
7. LLM Chat             → Generate response using Sarvam Chat API with context
8. Translation          → Translate response back to user's language
9. PII Unmask           → Restore masked values for display (not for LLM)
10. Cache Store          → Store response in semantic cache for future use
"""

import re
import uuid
import logging
from typing import Optional

from app.config import settings
from app.models import PipelineContext, IntentType, ChatRequest, ChatResponse
from app.security.pii_masker import pii_masker
from app.security.prompt_guard import prompt_guard
from app.sarvam.client import sarvam_client
from app.services import rag_engine
from app.services import semantic_cache
from app.feedback.collector import track_interaction

logger = logging.getLogger(__name__)

# ─── INTENT CLASSIFICATION ──────────────────────────────────────────

INTENT_KEYWORDS = {
    IntentType.SCHEME_QUERY: [
        "scheme", "yojana", "program", "benefit", "subsidy", "grant",
        "योजना", "लाभ", "सब्सिडी", "अनुदान", "सरकारी",
        "tell me about", "what is", "how to apply", "kya hai", "batao",
        "information", "details", "list", "available",
    ],
    IntentType.ELIGIBILITY_CHECK: [
        "eligible", "eligibility", "qualify", "can i apply", "am i eligible",
        "पात्र", "पात्रता", "योग्य", "क्या मैं",
        "check eligibility", "criteria", "requirement", "who can apply",
        "age limit", "income limit",
    ],
    IntentType.GRIEVANCE_FILE: [
        "complaint", "grievance", "file", "report", "submit",
        "शिकायत", "दर्ज", "समस्या", "problem",
        "issue", "not working", "corruption", "delay",
    ],
    IntentType.GRIEVANCE_STATUS: [
        "status", "track", "check status", "ticket", "GRV-",
        "स्थिति", "ट्रैक", "टिकट",
        "where is my", "update on",
    ],
    IntentType.DOCUMENT_QUERY: [
        "document", "upload", "certificate", "proof",
        "दस्तावेज़", "प्रमाण पत्र", "अपलोड",
        "aadhaar", "pan card", "ration card",
    ],
    IntentType.GREETING: [
        "hello", "hi", "namaste", "namaskar", "good morning", "good evening",
        "नमस्ते", "नमस्कार", "हैलो",
        "help", "start", "शुरू",
    ],
}


def classify_intent(text: str) -> IntentType:
    """Classify user intent based on keywords."""
    text_lower = text.lower()
    scores = {intent: 0 for intent in IntentType}

    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                scores[intent] += 1

    # Find highest scoring intent
    best_intent = max(scores, key=scores.get)
    if scores[best_intent] == 0:
        return IntentType.GENERAL

    return best_intent


# ─── SYSTEM PROMPTS BY INTENT ────────────────────────────────────────

SYSTEM_PROMPTS = {
    IntentType.SCHEME_QUERY: (
        "You are NagrikMitra, an AI-powered government services assistant for Indian citizens. "
        "You help citizens understand government schemes, their benefits, and how to apply. "
        "Use the provided context to give accurate, helpful information. "
        "Always mention the scheme name, key benefits, and eligibility criteria. "
        "Be concise and clear. If you don't have information, say so honestly. "
        "IMPORTANT: Always respond in English only. Translation to the user's language is handled separately."
    ),
    IntentType.ELIGIBILITY_CHECK: (
        "You are NagrikMitra, helping citizens check their eligibility for government schemes. "
        "Based on the user's information and scheme criteria provided in context, "
        "clearly state whether they are eligible or not, and explain why. "
        "List any missing information they need to provide. Be encouraging and helpful."
    ),
    IntentType.GRIEVANCE_FILE: (
        "You are NagrikMitra, helping citizens file grievances with the government. "
        "Help them articulate their complaint clearly. Ask for necessary details: "
        "subject, description, category, and location. "
        "Be empathetic and assure them their complaint will be tracked."
    ),
    IntentType.GRIEVANCE_STATUS: (
        "You are NagrikMitra, helping citizens track their grievance status. "
        "Provide clear status updates and expected timelines. "
        "Be reassuring and professional."
    ),
    IntentType.GENERAL: (
        "You are NagrikMitra, an AI-powered government services assistant for Indian citizens. "
        "You help with: government schemes, eligibility checks, grievance filing, and document assistance. "
        "Be helpful, concise, and guide users to specific services they might need. "
        "IMPORTANT: Always respond in English only. Translation to the user's language is handled separately."
    ),
    IntentType.GREETING: (
        "You are NagrikMitra, a friendly government services assistant. "
        "Greet the user warmly and briefly explain what you can help with: "
        "1) Government scheme information, 2) Eligibility checks, "
        "3) Grievance filing & tracking, 4) Document assistance. "
        "Keep it brief and inviting. "
        "IMPORTANT: Always respond in English only. Translation to the user's language is handled separately."
    ),
    IntentType.DOCUMENT_QUERY: (
        "You are NagrikMitra, helping citizens with document-related queries. "
        "Assist with understanding which documents are needed for various schemes, "
        "how to obtain them, and document verification processes."
    ),
}


def _get_max_tokens(intent: IntentType) -> int:
    """Get max tokens based on intent type for optimization."""
    token_map = {
        IntentType.GREETING: 500,
        IntentType.GENERAL: settings.MAX_TOKENS_GENERAL,
        IntentType.SCHEME_QUERY: settings.MAX_TOKENS_SCHEME_DETAIL,
        IntentType.ELIGIBILITY_CHECK: settings.MAX_TOKENS_ELIGIBILITY,
        IntentType.GRIEVANCE_FILE: 600,
        IntentType.GRIEVANCE_STATUS: 500,
        IntentType.DOCUMENT_QUERY: 600,
    }
    return token_map.get(intent, 300)


# ─── MAIN PIPELINE ───────────────────────────────────────────────────

async def process_message(request: ChatRequest) -> ChatResponse:
    """Process a user message through the 10-step pipeline."""

    ctx = PipelineContext(
        original_input=request.message,
        session_id=request.session_id or uuid.uuid4().hex[:16],
        state=request.state,
        district=request.district,
    )

    try:
        # ── Step 1: Language Detection ──────────────────────────────
        if request.language_preference:
            ctx.detected_language = request.language_preference
        else:
            lang_result = await sarvam_client.detect_language(request.message)
            ctx.detected_language = lang_result["language_code"]
        logger.info(f"[Step 1] Language detected: {ctx.detected_language}")

        # ── Step 2: PII Masking ─────────────────────────────────────
        ctx.masked_input, ctx.pii_map = pii_masker.mask(request.message)
        ctx.pii_detected = len(ctx.pii_map) > 0
        if ctx.pii_detected:
            logger.info(f"[Step 2] PII masked: {pii_masker.get_masked_summary(ctx.pii_map)}")

        # ── Step 3: Prompt Guard ────────────────────────────────────
        ctx.risk_score, guard_reasons, should_block = prompt_guard.check(ctx.masked_input)
        if should_block:
            logger.warning(f"[Step 3] Input blocked (risk={ctx.risk_score}): {guard_reasons}")
            return ChatResponse(
                response=prompt_guard.get_safe_response(guard_reasons),
                detected_language=ctx.detected_language,
                intent="blocked",
                session_id=ctx.session_id,
                pii_detected=ctx.pii_detected,
            )
        logger.info(f"[Step 3] Prompt guard passed (risk={ctx.risk_score:.2f})")

        # ── Step 4: Semantic Cache Check (Qdrant) ────────────────────
        cached_response = semantic_cache.check_cache(ctx.masked_input)
        if cached_response:
            logger.info("[Step 4] Semantic cache hit — translating cached response")
            ctx.from_cache = True
            # Cached response is in English; translate to user's language
            if ctx.detected_language != "en-IN":
                try:
                    cached_response = await sarvam_client.translate(
                        cached_response,
                        source_language="en-IN",
                        target_language=ctx.detected_language,
                    )
                except Exception:
                    pass  # return English if translation fails
            ctx.final_response = cached_response
            return _build_response(ctx)

        # ── Step 5: Intent Classification ───────────────────────────
        ctx.intent = classify_intent(ctx.masked_input)
        logger.info(f"[Step 5] Intent classified: {ctx.intent}")

        # ── Step 6: RAG Retrieval ───────────────────────────────────
        # Translate to English for better retrieval if needed
        query_for_rag = ctx.masked_input
        if ctx.detected_language != "en-IN":
            try:
                query_for_rag = await sarvam_client.translate(
                    ctx.masked_input,
                    source_language=ctx.detected_language,
                    target_language="en-IN",
                )
            except Exception:
                query_for_rag = ctx.masked_input

        chunks = await rag_engine.retrieve(query_for_rag, top_k=settings.TAVILY_MAX_RESULTS)
        ctx.rag_context = rag_engine.build_rag_context(chunks)
        ctx.schemes_referenced = list(set(c["scheme_name"] for c in chunks if "scheme_name" in c))
        logger.info(f"[Step 6] RAG retrieved {len(chunks)} chunks")

        # ── Step 7: LLM Chat ──────────────────────────────────────
        system_prompt = SYSTEM_PROMPTS.get(ctx.intent, SYSTEM_PROMPTS[IntentType.GENERAL])
        system_parts = [system_prompt]
        if ctx.rag_context:
            system_parts.append(f"Relevant information from web search:\n{ctx.rag_context}")
        if ctx.state:
            system_parts.append(f"User's location: State={ctx.state}, District={ctx.district or 'Not specified'}")

        # If user input is not English, translate it to English for the LLM
        llm_input = ctx.masked_input
        if ctx.detected_language != "en-IN":
            try:
                llm_input = await sarvam_client.translate(
                    ctx.masked_input,
                    source_language=ctx.detected_language,
                    target_language="en-IN",
                )
            except Exception:
                llm_input = ctx.masked_input

        messages = [
            {"role": "system", "content": "\n\n".join(system_parts)},
            {"role": "user", "content": llm_input},
        ]

        chat_result = await sarvam_client.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=_get_max_tokens(ctx.intent),
        )
        ctx.llm_response = chat_result["response"]
        ctx.token_usage = chat_result.get("usage", {})
        logger.info(f"[Step 7] LLM response generated ({len(ctx.llm_response)} chars)")

        # ── Step 8: Translation ────────────────────────────────────
        if ctx.detected_language != "en-IN":
            try:
                ctx.translated_response = await sarvam_client.translate(
                    ctx.llm_response,
                    source_language="en-IN",
                    target_language=ctx.detected_language,
                )
            except Exception:
                ctx.translated_response = ctx.llm_response
        else:
            ctx.translated_response = ctx.llm_response
        logger.info(f"[Step 8] Response translated to {ctx.detected_language}")

        # ── Step 9: PII Unmask ─────────────────────────────────────
        ctx.final_response = pii_masker.unmask(ctx.translated_response, ctx.pii_map)
        logger.info("[Step 9] PII unmasked for display")

        # ── Step 10: Semantic Cache Store (Qdrant) ──────────────────
        # Store the English LLM response (pre-translation) so cache is language-neutral
        semantic_cache.store_cache(ctx.masked_input, ctx.llm_response)
        logger.info("[Step 10] English response cached in Qdrant")

        # Track interaction for analytics
        track_interaction(ctx.session_id)

        return _build_response(ctx)

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return ChatResponse(
            response="I apologize, but I encountered an error processing your request. Please try again.",
            detected_language=ctx.detected_language,
            intent=ctx.intent.value if isinstance(ctx.intent, IntentType) else "error",
            session_id=ctx.session_id,
        )


def _build_response(ctx: PipelineContext) -> ChatResponse:
    """Build the final ChatResponse from pipeline context."""
    return ChatResponse(
        response=ctx.final_response,
        detected_language=ctx.detected_language,
        intent=ctx.intent.value if isinstance(ctx.intent, IntentType) else str(ctx.intent),
        session_id=ctx.session_id,
        schemes_referenced=ctx.schemes_referenced,
        pii_detected=ctx.pii_detected,
        from_cache=ctx.from_cache,
        token_usage=ctx.token_usage,
    )

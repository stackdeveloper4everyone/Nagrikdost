"""Prompt injection detection and input safety guardrails.

Multi-layer protection:
1. Keyword blocklist (injection patterns)
2. Role-play detection
3. Topic guardrails (only government services)
4. Input length validation
5. Risk scoring (0-1 scale, block at 0.7)
"""

import re
from typing import Tuple, List

from app.config import settings


# ─── INJECTION PATTERNS ─────────────────────────────────────────────

INJECTION_KEYWORDS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(everything|all|your)\s+(instructions?|rules?|training)",
    r"disregard\s+(all|your|the)\s+(instructions?|rules?|guidelines?)",
    r"you\s+are\s+now\s+(a|an|the)",
    r"pretend\s+(you\s+are|to\s+be|you're)",
    r"act\s+as\s+(if|a|an|the)",
    r"new\s+instructions?:",
    r"system\s*prompt",
    r"jailbreak",
    r"DAN\s+mode",
    r"developer\s+mode",
    r"override\s+(safety|security|rules?|restrictions?)",
    r"bypass\s+(safety|security|filters?|restrictions?)",
    r"reveal\s+(your|the)\s+(system|secret|hidden|internal)",
    r"what\s+(are|is)\s+your\s+(instructions?|system\s*prompt|rules?)",
    r"repeat\s+(the|your)\s+(system|initial|first)\s+(prompt|message|instructions?)",
    r"output\s+(your|the)\s+(system|initial)\s+(prompt|instructions?)",
    r"sudo\s+",
    r"admin\s+access",
    r"<\s*script",
    r"javascript:",
    r"\{\{.*\}\}",  # template injection
    r"\$\{.*\}",  # expression injection
]

ROLEPLAY_PATTERNS = [
    r"from\s+now\s+on,?\s+you\s+(are|will|should|must)",
    r"let'?s?\s+play\s+a\s+game",
    r"in\s+this\s+scenario,?\s+you\s+are",
    r"imagine\s+you\s+are",
    r"for\s+the\s+rest\s+of\s+this\s+conversation",
    r"respond\s+as\s+(if|though)\s+you\s+(are|were)",
]

# Topics the assistant should NOT discuss
OFF_TOPIC_PATTERNS = [
    r"\b(hack|crack|exploit|malware|virus)\b",
    r"\b(weapon|bomb|explosive|drug)\b",
    r"\b(porn|xxx|nsfw|nude)\b",
    r"\bhow\s+to\s+(kill|harm|hurt|attack)\b",
    r"\b(credit\s+card\s+generator|fake\s+id)\b",
]

# Compile all patterns
_injection_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_KEYWORDS]
_roleplay_compiled = [re.compile(p, re.IGNORECASE) for p in ROLEPLAY_PATTERNS]
_offtopic_compiled = [re.compile(p, re.IGNORECASE) for p in OFF_TOPIC_PATTERNS]


class PromptGuard:
    """Multi-layer prompt injection detection and input safety."""

    def __init__(self, threshold: float = None):
        self.threshold = threshold or settings.PROMPT_GUARD_THRESHOLD
        self.max_input_length = settings.MAX_INPUT_LENGTH

    def check(self, text: str) -> Tuple[float, List[str], bool]:
        """Analyze input text for injection attempts and safety violations.

        Returns:
            Tuple of (risk_score, reasons, should_block)
            - risk_score: 0.0 (safe) to 1.0 (dangerous)
            - reasons: List of detected issues
            - should_block: Whether to block this input
        """
        reasons: List[str] = []
        risk_score = 0.0

        # Layer 1: Input length check
        if len(text) > self.max_input_length:
            reasons.append(f"Input exceeds maximum length ({len(text)}/{self.max_input_length})")
            risk_score += 0.3

        # Layer 2: Injection keyword detection
        injection_hits = 0
        for pattern in _injection_compiled:
            if pattern.search(text):
                injection_hits += 1
        if injection_hits > 0:
            reasons.append(f"Injection pattern detected ({injection_hits} matches)")
            risk_score += min(0.5, injection_hits * 0.25)

        # Layer 3: Role-play detection
        roleplay_hits = 0
        for pattern in _roleplay_compiled:
            if pattern.search(text):
                roleplay_hits += 1
        if roleplay_hits > 0:
            reasons.append("Role-play/persona manipulation attempt detected")
            risk_score += 0.4

        # Layer 4: Off-topic content
        offtopic_hits = 0
        for pattern in _offtopic_compiled:
            if pattern.search(text):
                offtopic_hits += 1
        if offtopic_hits > 0:
            reasons.append("Off-topic or potentially harmful content detected")
            risk_score += 0.5

        # Layer 5: Suspicious patterns
        # Excessive special characters (possible injection)
        special_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        if special_ratio > 0.3:
            reasons.append("Unusually high ratio of special characters")
            risk_score += 0.2

        # Multiple languages mixed with code-like patterns
        if re.search(r'[\x00-\x1f]', text):
            reasons.append("Control characters detected")
            risk_score += 0.3

        # Cap at 1.0
        risk_score = min(1.0, risk_score)
        should_block = risk_score >= self.threshold

        return risk_score, reasons, should_block

    def get_safe_response(self, reasons: List[str]) -> str:
        """Generate a safe, helpful response when input is blocked."""
        return (
            "I'm sorry, but I cannot process this request. As a government services assistant, "
            "I can only help with:\n\n"
            "- Government scheme information and eligibility\n"
            "- Grievance filing and status tracking\n"
            "- Document verification assistance\n"
            "- General questions about public services\n\n"
            "Please rephrase your question related to government services."
        )


# Global instance
prompt_guard = PromptGuard()

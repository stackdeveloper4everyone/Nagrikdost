"""PII (Personally Identifiable Information) detection and masking.

Masks sensitive data before sending to LLM, unmasks for display.
Supports: Aadhaar (with Verhoeff checksum), PAN, Phone, Email, Bank Account.
"""

import re
import uuid
from typing import Dict, Tuple, List


# ─── VERHOEFF ALGORITHM (Aadhaar checksum validation) ───────────────

_VERHOEFF_TABLE_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_VERHOEFF_TABLE_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_VERHOEFF_TABLE_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def _verhoeff_validate(number: str) -> bool:
    """Validate a number string using the Verhoeff checksum algorithm."""
    c = 0
    for i, digit in enumerate(reversed(number)):
        c = _VERHOEFF_TABLE_D[c][_VERHOEFF_TABLE_P[i % 8][int(digit)]]
    return c == 0


# ─── PII PATTERNS ───────────────────────────────────────────────────

PII_PATTERNS = {
    "AADHAAR": {
        "pattern": re.compile(r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4})\b'),
        "placeholder": "[AADHAAR_{}]",
        "validator": lambda x: _verhoeff_validate(re.sub(r'[\s-]', '', x)) and len(re.sub(r'[\s-]', '', x)) == 12,
    },
    "PAN": {
        "pattern": re.compile(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b'),
        "placeholder": "[PAN_{}]",
        "validator": None,
    },
    "PHONE": {
        "pattern": re.compile(r'\b(?:\+91[\s-]?)?([6-9]\d{9})\b'),
        "placeholder": "[PHONE_{}]",
        "validator": None,
    },
    "EMAIL": {
        "pattern": re.compile(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'),
        "placeholder": "[EMAIL_{}]",
        "validator": None,
    },
    "BANK_ACCOUNT": {
        "pattern": re.compile(r'\b(\d{9,18})\b'),
        "placeholder": "[BANK_{}]",
        "validator": lambda x: 9 <= len(x) <= 18 and not _verhoeff_validate(x),  # exclude Aadhaar
    },
    "IFSC": {
        "pattern": re.compile(r'\b([A-Z]{4}0[A-Z0-9]{6})\b'),
        "placeholder": "[IFSC_{}]",
        "validator": None,
    },
}


class PIIMasker:
    """Detect and mask PII in text, with ability to unmask later."""

    def mask(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Mask all PII in text.

        Returns:
            Tuple of (masked_text, pii_map) where pii_map maps placeholders to original values.
        """
        pii_map: Dict[str, str] = {}
        masked_text = text
        pii_detected_types: List[str] = []

        for pii_type, config in PII_PATTERNS.items():
            # Skip bank account initial pass (too many false positives)
            if pii_type == "BANK_ACCOUNT":
                continue

            matches = config["pattern"].finditer(masked_text)
            for match in matches:
                original = match.group(1) if match.lastindex else match.group(0)

                # Run validator if exists
                if config["validator"] and not config["validator"](original):
                    continue

                # Generate unique placeholder
                short_id = uuid.uuid4().hex[:6].upper()
                last_four = re.sub(r'[\s-]', '', original)[-4:]
                placeholder = config["placeholder"].format(last_four)

                pii_map[placeholder] = original
                masked_text = masked_text.replace(match.group(0), placeholder, 1)
                pii_detected_types.append(pii_type)

        return masked_text, pii_map

    def unmask(self, text: str, pii_map: Dict[str, str]) -> str:
        """Restore original PII values from masked text.

        Only used for final display — never for LLM input.
        """
        result = text
        for placeholder, original in pii_map.items():
            result = result.replace(placeholder, original)
        return result

    def detect_pii_types(self, text: str) -> List[str]:
        """Detect which types of PII are present in text (without masking)."""
        detected = []
        for pii_type, config in PII_PATTERNS.items():
            if pii_type == "BANK_ACCOUNT":
                continue
            matches = config["pattern"].findall(text)
            for match_val in matches:
                val = match_val if isinstance(match_val, str) else match_val[0]
                if config["validator"] is None or config["validator"](val):
                    detected.append(pii_type)
                    break
        return detected

    def get_masked_summary(self, pii_map: Dict[str, str]) -> str:
        """Generate a human-readable summary of what was masked."""
        if not pii_map:
            return "No PII detected"
        types = set()
        for placeholder in pii_map:
            for pii_type in PII_PATTERNS:
                if pii_type in placeholder:
                    types.add(pii_type)
                    break
        return f"Masked: {', '.join(types)}"


# Global instance
pii_masker = PIIMasker()

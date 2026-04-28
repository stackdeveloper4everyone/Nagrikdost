"""Scheme service for eligibility checking and scheme recommendations."""

import json
import os
import logging
from typing import List, Dict, Optional

from app.models import EligibilityRequest, EligibilityResult

logger = logging.getLogger(__name__)

_schemes_data: List[Dict] = []


def load_schemes(data_dir: str = None):
    """Load schemes data from JSON."""
    global _schemes_data
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")

    schemes_path = os.path.join(data_dir, "schemes.json")
    try:
        with open(schemes_path, "r", encoding="utf-8") as f:
            _schemes_data = json.load(f)
        logger.info(f"Loaded {len(_schemes_data)} schemes for eligibility engine")
    except FileNotFoundError:
        logger.warning("Schemes data not found")
        _schemes_data = []


def get_all_schemes() -> List[Dict]:
    """Return all loaded schemes."""
    return _schemes_data


def get_scheme_by_id(scheme_id: str) -> Optional[Dict]:
    """Look up a scheme by its ID."""
    return next((s for s in _schemes_data if s["id"] == scheme_id), None)


def search_schemes(
    query: str = "",
    state: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Dict]:
    """Search schemes by keyword, state, and category."""
    results = _schemes_data

    if state:
        results = [
            s for s in results
            if s.get("is_central", True) or (s.get("states") and state in s["states"])
        ]

    if category:
        results = [s for s in results if s.get("category", "").lower() == category.lower()]

    if query:
        query_lower = query.lower()
        results = [
            s for s in results
            if query_lower in s.get("name_en", "").lower()
            or query_lower in s.get("description_en", "").lower()
            or query_lower in s.get("category", "").lower()
        ]

    return results


def check_eligibility(request: EligibilityRequest) -> List[EligibilityResult]:
    """Check eligibility for a specific scheme or all schemes.

    Returns a list of EligibilityResult with match scores.
    """
    if request.scheme_id:
        scheme = get_scheme_by_id(request.scheme_id)
        if scheme:
            return [_evaluate_scheme(scheme, request)]
        return []

    # Check all schemes and return top matches
    results = []
    for scheme in _schemes_data:
        result = _evaluate_scheme(scheme, request)
        if result.match_score > 0:
            results.append(result)

    results.sort(key=lambda r: r.match_score, reverse=True)
    return results[:10]


def _evaluate_scheme(scheme: Dict, request: EligibilityRequest) -> EligibilityResult:
    """Evaluate a single scheme against user criteria."""
    elig = scheme.get("eligibility", {})
    eligible = True
    reasons = []
    missing = []
    total_criteria = 0
    met_criteria = 0

    # Age check
    if elig.get("min_age") or elig.get("max_age"):
        total_criteria += 1
        if request.age is not None:
            if elig.get("min_age") and request.age < elig["min_age"]:
                eligible = False
                reasons.append(f"Minimum age requirement: {elig['min_age']} (your age: {request.age})")
            elif elig.get("max_age") and request.age > elig["max_age"]:
                eligible = False
                reasons.append(f"Maximum age limit: {elig['max_age']} (your age: {request.age})")
            else:
                met_criteria += 1
                reasons.append("Age requirement met")
        else:
            missing.append("Age information needed")

    # Income check
    if elig.get("max_income"):
        total_criteria += 1
        if request.income is not None:
            if request.income > elig["max_income"]:
                eligible = False
                reasons.append(f"Income limit: ₹{elig['max_income']:,}/year (your income: ₹{request.income:,})")
            else:
                met_criteria += 1
                reasons.append("Income requirement met")
        else:
            missing.append("Income information needed")

    # Gender check
    if elig.get("gender") and elig["gender"] != "all":
        total_criteria += 1
        if request.gender:
            if request.gender.lower() != elig["gender"].lower():
                eligible = False
                reasons.append(f"This scheme is for {elig['gender']} applicants")
            else:
                met_criteria += 1
                reasons.append("Gender requirement met")
        else:
            missing.append("Gender information needed")

    # State check
    if elig.get("states"):
        total_criteria += 1
        if request.state:
            if request.state not in elig["states"]:
                eligible = False
                reasons.append(f"Available in: {', '.join(elig['states'])}")
            else:
                met_criteria += 1
                reasons.append("State requirement met")
        else:
            missing.append("State information needed")

    # Occupation check
    if elig.get("occupation"):
        total_criteria += 1
        if request.occupation:
            if request.occupation.lower() not in [o.lower() for o in elig["occupation"]]:
                eligible = False
                reasons.append(f"Required occupation: {', '.join(elig['occupation'])}")
            else:
                met_criteria += 1
                reasons.append("Occupation requirement met")
        else:
            missing.append("Occupation information needed")

    # Calculate match score
    match_score = met_criteria / max(total_criteria, 1)

    return EligibilityResult(
        scheme_id=scheme["id"],
        scheme_name=scheme["name_en"],
        eligible=eligible and len(missing) == 0,
        reasons=reasons,
        missing_criteria=missing,
        match_score=match_score,
    )

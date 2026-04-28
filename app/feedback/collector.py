"""Feedback collection and analytics for continuous improvement."""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.models import FeedbackRequest, FeedbackEntry, FeedbackAnalytics

logger = logging.getLogger(__name__)

# In-memory feedback store
_feedback: List[FeedbackEntry] = []

# Track session interaction counts
_session_counts: Dict[str, int] = {}


def submit_feedback(request: FeedbackRequest, intent: str = None, language: str = None) -> FeedbackEntry:
    """Record user feedback for a response."""
    entry = FeedbackEntry(
        id=uuid.uuid4().hex[:12],
        session_id=request.session_id,
        message_index=request.message_index,
        rating=request.rating,
        comment=request.comment,
        timestamp=datetime.now(),
        detected_intent=intent,
        detected_language=language,
    )
    _feedback.append(entry)
    logger.info(f"Feedback received: session={request.session_id}, rating={request.rating}")
    return entry


def track_interaction(session_id: str):
    """Track an interaction for analytics."""
    _session_counts[session_id] = _session_counts.get(session_id, 0) + 1


def get_analytics() -> FeedbackAnalytics:
    """Compute feedback analytics."""
    total_feedback = len(_feedback)
    total_interactions = sum(_session_counts.values())

    if total_feedback == 0:
        return FeedbackAnalytics(
            total_interactions=total_interactions,
            average_rating=0.0,
            total_feedback=0,
            rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            top_intents={},
            language_distribution={},
            satisfaction_trend=[],
        )

    # Rating distribution
    rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    intent_counts: Dict[str, int] = {}
    lang_counts: Dict[str, int] = {}
    total_rating = 0

    for entry in _feedback:
        total_rating += entry.rating
        rating_dist[entry.rating] = rating_dist.get(entry.rating, 0) + 1

        if entry.detected_intent:
            intent_counts[entry.detected_intent] = intent_counts.get(entry.detected_intent, 0) + 1
        if entry.detected_language:
            lang_counts[entry.detected_language] = lang_counts.get(entry.detected_language, 0) + 1

    avg_rating = total_rating / total_feedback

    # Satisfaction trend (last 20 entries)
    recent = _feedback[-20:]
    trend = [
        {"index": i, "rating": e.rating, "timestamp": e.timestamp.isoformat()}
        for i, e in enumerate(recent)
    ]

    return FeedbackAnalytics(
        total_interactions=total_interactions,
        average_rating=round(avg_rating, 2),
        total_feedback=total_feedback,
        rating_distribution=rating_dist,
        top_intents=intent_counts,
        language_distribution=lang_counts,
        satisfaction_trend=trend,
    )

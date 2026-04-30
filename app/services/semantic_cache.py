"""Semantic cache using simple in-memory dictionary + sklearn embeddings.

Stores query-response pairs with vector similarity matching.
Uses sklearn HashingVectorizer for embeddings (no model download needed).

Falls back gracefully if dependencies are unavailable.
"""

import logging
import time
import uuid
from typing import Optional, Dict, List

from app.config import settings

logger = logging.getLogger(__name__)

# Embedding dimension — HashingVectorizer n_features
EMBEDDING_DIM = 256

# Module-level singletons (initialized in init())
_vectorizer = None
_cache_store: Dict[str, dict] = {}  # id -> {query, response, vector, timestamp}
_initialized = False

COLLECTION_NAME = "semantic_cache"


def _embed(text: str) -> list:
    """Convert text to a dense vector using HashingVectorizer."""
    if _vectorizer is None:
        return None
    try:
        import numpy as np
        vec = _vectorizer.transform([text.lower()])
        dense = vec.toarray()[0]
        # L2-normalize for cosine similarity
        norm = np.linalg.norm(dense)
        if norm > 0:
            dense = dense / norm
        return dense.tolist()
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return None


def _cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity between two vectors."""
    try:
        import numpy as np
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
    except Exception:
        return 0.0


def init(persist_path: str = None):
    """Initialize embedding vectorizer and in-memory cache store.

    Uses a simple Python dictionary instead of Qdrant to minimize
    memory usage and avoid embedded server overhead.
    """
    global _vectorizer, _initialized

    try:
        from sklearn.feature_extraction.text import HashingVectorizer
        # Initialize vectorizer (character + word n-grams for better semantic matching)
        _vectorizer = HashingVectorizer(
            n_features=EMBEDDING_DIM,
            analyzer="char_wb",
            ngram_range=(2, 4),
            norm="l2",
        )
        logger.info("Semantic cache vectorizer initialized (sklearn HashingVectorizer)")
    except ImportError:
        logger.warning("scikit-learn not available — semantic cache will use exact matching only")
        _vectorizer = None
    except Exception as e:
        logger.warning(f"Vectorizer init failed: {e} — semantic cache will use exact matching only")
        _vectorizer = None

    _initialized = True
    logger.info("Semantic cache ready (in-memory dict mode) — 0 cached entries")


def check_cache(query: str) -> Optional[str]:
    """Search for a semantically similar cached query.

    Returns the cached response if similarity >= threshold and TTL hasn't expired.
    """
    if not _initialized or not _cache_store:
        return None

    try:
        query_vector = _embed(query)
        now = time.time()
        best_score = 0.0
        best_response = None
        expired_ids = []

        for entry_id, entry in _cache_store.items():
            # Check TTL
            if now - entry.get("timestamp", 0) > settings.CACHE_TTL_SECONDS:
                expired_ids.append(entry_id)
                continue

            # Try vector similarity if we have vectors
            if query_vector and entry.get("vector"):
                score = _cosine_similarity(query_vector, entry["vector"])
                if score >= settings.CACHE_SIMILARITY_THRESHOLD and score > best_score:
                    best_score = score
                    best_response = entry.get("response")
            # Fallback: exact match
            elif query.lower().strip() == entry.get("query", "").lower().strip():
                best_score = 1.0
                best_response = entry.get("response")

        # Cleanup expired entries
        for eid in expired_ids:
            _cache_store.pop(eid, None)

        if best_response:
            logger.info(f"Semantic cache HIT: '{query[:50]}...' (score={best_score:.3f})")
            return best_response

        return None

    except Exception as e:
        logger.error(f"Cache check error: {e}")
        return None


def store_cache(query: str, response: str):
    """Store a query-response pair in the semantic cache."""
    if not _initialized:
        return

    try:
        query_vector = _embed(query)
        entry_id = uuid.uuid4().hex[:12]

        _cache_store[entry_id] = {
            "query": query,
            "response": response,
            "vector": query_vector,
            "timestamp": time.time(),
        }

        # Enforce max cache size — delete oldest entries
        if len(_cache_store) > settings.CACHE_MAX_SIZE:
            _evict_oldest(len(_cache_store) - settings.CACHE_MAX_SIZE)

        logger.info(f"Cached response for: '{query[:50]}...'")

    except Exception as e:
        logger.error(f"Cache store error: {e}")


def _evict_oldest(count: int):
    """Remove the oldest `count` entries from the cache."""
    try:
        sorted_entries = sorted(
            _cache_store.items(),
            key=lambda x: x[1].get("timestamp", 0),
        )
        for entry_id, _ in sorted_entries[:count]:
            _cache_store.pop(entry_id, None)
        logger.info(f"Evicted {count} oldest cache entries")
    except Exception as e:
        logger.warning(f"Cache eviction failed: {e}")


def get_stats() -> Dict:
    """Return cache statistics."""
    if not _initialized:
        return {"status": "not_initialized", "total_cached": 0}

    return {
        "status": "active",
        "total_cached": len(_cache_store),
        "similarity_threshold": settings.CACHE_SIMILARITY_THRESHOLD,
        "ttl_seconds": settings.CACHE_TTL_SECONDS,
        "mode": "in-memory-dict",
    }

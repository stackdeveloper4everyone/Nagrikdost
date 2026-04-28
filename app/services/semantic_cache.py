"""Semantic cache using Qdrant vector database + sklearn embeddings.

Stores query-response pairs as vectors in Qdrant. On each new query,
searches for semantically similar cached queries to avoid duplicate
LLM calls. Uses sklearn HashingVectorizer for embeddings (no model
download needed, works offline behind corporate proxies).
"""

import logging
import time
import uuid
from typing import Optional, Dict

from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import HashingVectorizer
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# Embedding dimension — HashingVectorizer n_features
EMBEDDING_DIM = 256

# Module-level singletons (initialized in init())
_client: Optional[QdrantClient] = None
_vectorizer: Optional[HashingVectorizer] = None

COLLECTION_NAME = "semantic_cache"


def _embed(text: str) -> list:
    """Convert text to a dense vector using HashingVectorizer."""
    vec = _vectorizer.transform([text.lower()])
    dense = vec.toarray()[0]
    # L2-normalize for cosine similarity
    norm = np.linalg.norm(dense)
    if norm > 0:
        dense = dense / norm
    return dense.tolist()


def init(persist_path: str = None):
    """Initialize Qdrant client and embedding vectorizer.

    Connection priority:
      1. QDRANT_URL env var (external Qdrant server, e.g. Docker)
      2. persist_path (local file-based storage)
      3. In-memory mode (data lost on restart)
    """
    global _client, _vectorizer

    # Initialize vectorizer (character + word n-grams for better semantic matching)
    _vectorizer = HashingVectorizer(
        n_features=EMBEDDING_DIM,
        analyzer="char_wb",
        ngram_range=(2, 4),
        norm="l2",
    )

    # Initialize Qdrant client
    if settings.QDRANT_URL:
        _client = QdrantClient(url=settings.QDRANT_URL)
        logger.info(f"Qdrant connected to external server: {settings.QDRANT_URL}")
    elif persist_path:
        _client = QdrantClient(path=persist_path)
        logger.info(f"Qdrant initialized with persistent storage at: {persist_path}")
    else:
        _client = QdrantClient(":memory:")
        logger.info("Qdrant initialized in-memory mode")

    # Create collection if it doesn't exist
    collections = [c.name for c in _client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        _client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIM,
                distance=models.Distance.COSINE,
            ),
        )
        logger.info(f"Created Qdrant collection '{COLLECTION_NAME}' (dim={EMBEDDING_DIM})")
    else:
        logger.info(f"Qdrant collection '{COLLECTION_NAME}' already exists")

    info = _client.get_collection(COLLECTION_NAME)
    logger.info(f"Semantic cache ready — {info.points_count} cached entries")


def check_cache(query: str) -> Optional[str]:
    """Search for a semantically similar cached query.

    Returns the cached response if similarity >= threshold and TTL hasn't expired.
    """
    if _client is None:
        return None

    try:
        query_vector = _embed(query)

        results = _client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=1,
            score_threshold=settings.CACHE_SIMILARITY_THRESHOLD,
        ).points

        if not results:
            return None

        point = results[0]
        timestamp = point.payload.get("timestamp", 0)
        score = point.score

        # Check TTL
        if time.time() - timestamp > settings.CACHE_TTL_SECONDS:
            # Expired — delete it
            _client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.PointIdsList(points=[point.id]),
            )
            logger.info(f"Cache expired for: '{query[:50]}...' (score={score:.3f})")
            return None

        logger.info(f"Semantic cache HIT: '{query[:50]}...' (score={score:.3f})")
        return point.payload.get("response")

    except Exception as e:
        logger.error(f"Cache check error: {e}")
        return None


def store_cache(query: str, response: str):
    """Store a query-response pair in the semantic cache."""
    if _client is None:
        return

    try:
        query_vector = _embed(query)
        point_id = str(uuid.uuid4())

        _client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=query_vector,
                    payload={
                        "query": query,
                        "response": response,
                        "timestamp": time.time(),
                    },
                )
            ],
        )

        # Enforce max cache size — delete oldest entries
        info = _client.get_collection(COLLECTION_NAME)
        if info.points_count > settings.CACHE_MAX_SIZE:
            _evict_oldest(info.points_count - settings.CACHE_MAX_SIZE)

        logger.info(f"Cached response for: '{query[:50]}...'")

    except Exception as e:
        logger.error(f"Cache store error: {e}")


def _evict_oldest(count: int):
    """Remove the oldest `count` entries from the cache."""
    try:
        # Scroll all points, sorted by timestamp
        records, _ = _client.scroll(
            collection_name=COLLECTION_NAME,
            limit=count,
            order_by=models.OrderBy(key="timestamp", direction=models.Direction.ASC),
        )
        if records:
            ids = [r.id for r in records]
            _client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.PointIdsList(points=ids),
            )
            logger.info(f"Evicted {len(ids)} oldest cache entries")
    except Exception as e:
        logger.warning(f"Cache eviction failed: {e}")


def get_stats() -> Dict:
    """Return cache statistics."""
    if _client is None:
        return {"status": "not_initialized", "total_cached": 0}

    try:
        info = _client.get_collection(COLLECTION_NAME)
        return {
            "status": "active",
            "total_cached": info.points_count,
            "vectors_count": info.vectors_count,
            "similarity_threshold": settings.CACHE_SIMILARITY_THRESHOLD,
            "ttl_seconds": settings.CACHE_TTL_SECONDS,
        }
    except Exception:
        return {"status": "error", "total_cached": 0}

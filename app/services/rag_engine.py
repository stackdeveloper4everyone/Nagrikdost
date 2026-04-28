"""Web search engine using Tavily API — replaces local FAISS RAG.

Provides real-time web search results for the LLM context.
Semantic caching is handled separately by semantic_cache.py (Qdrant).
"""

import httpx
import logging
import time
from typing import List, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# HTTP client for Tavily API
_http_client: Optional[httpx.AsyncClient] = None

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def initialize_rag(data_dir: str = None):
    """Initialize the Tavily web search engine.

    The data_dir parameter is accepted for backward compatibility but ignored.
    """
    if not settings.TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not set — web search will be unavailable")
    else:
        logger.info("Tavily web search engine initialized")
    logger.info("RAG engine ready (Tavily web search mode)")


async def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=15.0, verify=False)
    return _http_client


async def retrieve(query: str, top_k: int = 5) -> List[Dict]:
    """Search the web using Tavily API for relevant information.

    Args:
        query: User query text
        top_k: Number of results to return

    Returns:
        List of result dicts with scheme_name, text, url, similarity_score
    """
    if not settings.TAVILY_API_KEY:
        logger.warning("Tavily API key not configured, skipping web search")
        return []

    search_query = f"{query} Indian government scheme"

    try:
        client = await _get_http_client()
        response = await client.post(
            TAVILY_SEARCH_URL,
            json={
                "api_key": settings.TAVILY_API_KEY,
                "query": search_query,
                "search_depth": settings.TAVILY_SEARCH_DEPTH,
                "max_results": top_k,
                "include_answer": True,
                "include_raw_content": False,
            },
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return []

    results = []

    # Include Tavily's generated answer as the first chunk
    answer = data.get("answer")
    if answer:
        results.append({
            "scheme_name": "Web Search Summary",
            "text": answer,
            "url": "",
            "similarity_score": 1.0,
        })

    # Include individual search results
    for item in data.get("results", []):
        results.append({
            "scheme_name": item.get("title", ""),
            "text": item.get("content", ""),
            "url": item.get("url", ""),
            "similarity_score": item.get("score", 0.0),
        })

    logger.info(f"Tavily returned {len(results)} results for: {query[:80]}")
    return results


def build_rag_context(chunks: List[Dict], max_chars: int = 3000) -> str:
    """Build a context string from search results for the LLM prompt."""
    if not chunks:
        return "No specific information found for this query from web search."

    context_parts = []
    total_chars = 0

    for chunk in chunks:
        text = chunk["text"]
        url = chunk.get("url", "")
        entry = f"{text}\nSource: {url}" if url else text
        if total_chars + len(entry) > max_chars:
            break
        context_parts.append(entry)
        total_chars += len(entry)

    return "\n\n".join(context_parts)


def get_all_schemes() -> List[Dict]:
    """Stub for backward compatibility."""
    return []

"""Milimo Quantum — Semantic Search Routes."""
from __future__ import annotations

import logging
from fastapi import APIRouter

from app.vector_store import search, reindex_all, get_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/")
async def semantic_search(q: str, n: int = 10, type: str | None = None):
    """Semantic search across experiments and conversations.

    Query params:
        q: natural language query
        n: max results (default 10)
        type: filter by 'conversation' or 'experiment'
    """
    results = await search(q, n_results=n, doc_type=type)
    return {"query": q, "results": results, "count": len(results)}


@router.post("/reindex")
async def reindex():
    """Re-index all conversations into the vector store."""
    result = await reindex_all()
    return result


@router.get("/status")
async def search_status():
    """Get vector store status."""
    return get_status()

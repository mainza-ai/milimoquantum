"""Milimo Quantum — arXiv Agent Wrapper.

Provides an async interface to the arXiv research feed.
"""
from __future__ import annotations

import anyio
from app.feeds.arxiv import search_papers


async def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """Search arXiv for papers (async wrapper)."""
    return await search_papers(query, max_results=max_results)

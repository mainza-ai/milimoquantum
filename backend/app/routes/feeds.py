"""Milimo Quantum — Live Data Feeds Routes.

Exposes endpoints for Yahoo Finance, arXiv, and PubChem data feeds.
"""
from __future__ import annotations

import logging
from app.auth import get_current_user
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/feeds", tags=["feeds"], dependencies=[Depends(get_current_user)])


@router.get("/arxiv")
async def search_arxiv(query: str, max_results: int = 5, category: str = "quant-ph"):
    """Search arXiv for quantum computing papers."""
    from app.feeds.arxiv import search_papers
    papers = await search_papers(query, max_results=max_results, category=category)
    return {"query": query, "papers": papers, "count": len(papers)}


@router.get("/pubchem")
async def search_pubchem_compound(name: str):
    """Search PubChem for a compound by name."""
    from app.feeds.pubchem import search_compound, format_molecule_markdown, get_molecule_qubits
    compound = await search_compound(name)
    if compound:
        return {
            "compound": compound,
            "markdown": format_molecule_markdown(compound),
            "estimated_qubits": get_molecule_qubits(compound),
        }
    return {"error": f"Compound '{name}' not found", "compound": None}


@router.get("/finance")
async def get_stock_data(symbols: str):
    """Fetch stock prices for given symbols (comma-separated)."""
    from app.feeds import get_stock_prices, get_portfolio_summary
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        return {"error": "No symbols provided", "prices": {}}

    prices = get_stock_prices(symbol_list)
    summary = get_portfolio_summary(symbol_list)
    return {"prices": prices, "markdown_summary": summary}

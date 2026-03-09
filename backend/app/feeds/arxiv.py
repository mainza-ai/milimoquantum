"""Milimo Quantum — arXiv Paper Feed.

Fetches quantum computing papers from arXiv for the Research Agent.
Uses the free arXiv API (no API key required).
"""
from __future__ import annotations

import logging
import urllib.parse
import httpx
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"


async def search_papers(
    query: str,
    max_results: int = 5,
    category: str = "quant-ph",
) -> list[dict]:
    """Search arXiv for papers matching a query.

    Args:
        query: Search terms (e.g., "quantum error correction surface code")
        max_results: Maximum papers to return
        category: arXiv category filter (default: quant-ph)

    Returns:
        List of dicts with: title, authors, abstract, url, published, category
    """
    try:
        # Build query
        search_query = f"cat:{category} AND all:{query}" if category else f"all:{query}"
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"

        # Fetch
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "MilimoQuantum/1.0"}) as client:
            response = await client.get(url)
            response.raise_for_status()
            xml_data = response.text

        # Parse Atom XML
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        root = ET.fromstring(xml_data)
        papers = []

        for entry in root.findall("atom:entry", ns):
            title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
            abstract = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")

            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.findtext("atom:name", "", ns)
                if name:
                    authors.append(name)

            # Get PDF link
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href", "")

            published = entry.findtext("atom:published", "", ns)[:10]  # YYYY-MM-DD

            # Primary category
            primary_cat = ""
            cat_elem = entry.find("arxiv:primary_category", ns)
            if cat_elem is not None:
                primary_cat = cat_elem.get("term", "")

            papers.append({
                "title": title,
                "authors": authors[:5],  # Cap at 5 authors
                "abstract": abstract[:500],  # Cap abstract length
                "url": pdf_url or entry.findtext("atom:id", "", ns),
                "published": published,
                "category": primary_cat,
            })

        return papers

    except Exception as e:
        logger.error(f"arXiv API error: {e}")
        return []


def format_papers_markdown(papers: list[dict]) -> str:
    """Format papers as a markdown summary for the Research Agent."""
    if not papers:
        return "No papers found for this query."

    lines = ["## Recent Papers from arXiv\n"]
    for i, paper in enumerate(papers, 1):
        authors_str = ", ".join(paper["authors"][:3])
        if len(paper["authors"]) > 3:
            authors_str += " et al."
        lines.append(f"### {i}. {paper['title']}")
        lines.append(f"**Authors:** {authors_str}")
        lines.append(f"**Published:** {paper['published']} | **Category:** `{paper['category']}`")
        lines.append(f"**Link:** [{paper['url']}]({paper['url']})")
        lines.append(f"\n> {paper['abstract'][:300]}...\n")

    return "\n".join(lines)

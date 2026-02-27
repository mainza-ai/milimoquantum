"""Milimo Quantum - PubMed Medical Research Feed.

Fetches medical and biophysics abstracts from NCBI PubMed.
Used by the Research Agent to ground drug discovery logic.
"""
from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

def search_pubmed(query: str, max_results: int = 3) -> list[dict[str, Any]]:
    """Search PubMed and return latest paper metadata."""
    try:
        # Step 1: ESearch to get UIDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "sort": "date"
        }
        url = f"{PUBMED_ESEARCH}?{urllib.parse.urlencode(search_params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "MilimoQuantum/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            esearch_data = json.loads(response.read())
            
        idlist = esearch_data.get("esearchresult", {}).get("idlist", [])
        if not idlist:
            return []
            
        # Step 2: ESummary to get paper details
        summary_params = {
            "db": "pubmed",
            "id": ",".join(idlist),
            "retmode": "json"
        }
        sum_url = f"{PUBMED_ESUMMARY}?{urllib.parse.urlencode(summary_params)}"
        sum_req = urllib.request.Request(sum_url, headers={"User-Agent": "MilimoQuantum/1.0"})
        with urllib.request.urlopen(sum_req, timeout=10) as response:
            esum_data = json.loads(response.read())
            
        result = esum_data.get("result", {})
        papers = []
        
        for uid in idlist:
            paper_info = result.get(uid, {})
            if not paper_info:
                continue
                
            authors = [a.get("name") for a in paper_info.get("authors", [])]
            
            papers.append({
                "uid": uid,
                "title": paper_info.get("title", ""),
                "authors": authors[:5],
                "journal": paper_info.get("fulljournalname", ""),
                "published": paper_info.get("pubdate", ""),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
            })
            
        return papers
        
    except Exception as e:
        logger.error(f"PubMed API Error: {e}")
        return []

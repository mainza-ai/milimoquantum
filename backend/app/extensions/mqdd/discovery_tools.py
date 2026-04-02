import httpx
import logging
import json
import re
from typing import List, Dict, Any, Optional

from app.cache import (
    cache_pubchem_result,
    get_cached_pubchem,
    cache_arxiv_result,
    get_cached_arxiv,
    cache_chembl_result,
    get_cached_chembl,
    cache_pdb_result,
    get_cached_pdb,
)

logger = logging.getLogger(__name__)

def is_valid_smiles_for_search(smiles: str) -> bool:
    """Validate that input looks like a SMILES string before API call."""
    if not smiles or not isinstance(smiles, str):
        return False
    smiles = smiles.strip()
    # Exclude filenames, sentences, and PDB IDs
    if '.pdb' in smiles.lower():
        return False
    if ' ' in smiles:
        return False
    if len(smiles) > 200:
        return False
    if len(smiles) < 2:
        return False
    # Exclude text that looks like natural language or filenames
    # Valid SMILES typically has: lowercase letters, brackets, special chars, or mixed case
    has_lower = any(c.islower() for c in smiles)
    has_special = any(c in smiles for c in '()[]=#@$:/\\+-')
    has_upper_after_lower = bool(re.search(r'[a-z][A-Z]', smiles))
    # Allow if: has lowercase, has special chars, or has upper after lower pattern
    if not (has_lower or has_special or has_upper_after_lower):
        # Check for repeated uppercase letters (like "CCO", "CCCC")
        # These are valid simple SMILES
        if re.match(r'^[A-Z]+$', smiles):
            return True  # Simple carbon chain like CCO
        # Looks like a word like "Analyze" or "File"
        if re.match(r'^[A-Za-z]{3,}$', smiles):
            return False
    # Basic SMILES character check
    if not re.match(r'^[A-Za-z0-9@\[\]\(\)\=\#\$\:\.\/\\+\-]+$', smiles):
        return False
    return True

async def search_pdb_structures(query: str, limit: int = 5) -> List[str]:
    """
    Search RCSB PDB for structure IDs matching a query string.
    Results are cached for 24 hours.
    """
    # Check cache first
    cached = get_cached_pdb(query)
    if cached:
        logger.debug(f"Cache hit for PDB query: {query}")
        return cached.get("pdb_ids", [])
    
    url = "https://search.rcsb.org/rcsbsearch/v2/query"
    search_payload = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {
                "value": query
            }
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {
                "start": 0,
                "rows": limit
            }
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=search_payload, timeout=10.0)
            if response.status_code == 204 or not response.content:
                return []
            response.raise_for_status()
            data = response.json()

            pdb_ids = [result["identifier"] for result in data.get("result_set", [])]
            
            # Cache result
            cache_pdb_result(query, {"pdb_ids": pdb_ids})
            
            return pdb_ids
    except Exception as e:
        logger.error(f"RCSB Search failed: {e}")
        return []

async def search_literature_pubmed(query: str, limit: int = 3) -> List[Dict[str, str]]:
    """
    Search PubMed for research papers and return summaries.
    Results are cached for 1 hour.
    """
    # Check cache first
    cached = get_cached_arxiv(query)  # Reuse arxiv cache for PubMed
    if cached:
        logger.debug(f"Cache hit for PubMed query: {query}")
        return cached.get("results", [])

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    try:
        async with httpx.AsyncClient() as client:
            # 1. Search for IDs
            search_res = await client.get(
                f"{base_url}esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": limit
                }
            )
            search_res.raise_for_status()
            id_list = search_res.json().get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return []

            # 2. Fetch summaries
            summary_res = await client.get(
                f"{base_url}esummary.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(id_list),
                    "retmode": "json"
                }
            )
            summary_res.raise_for_status()
            summary_data = summary_res.json().get("result", {})

            results = []
            for uid in id_list:
                doc = summary_data.get(uid, {})
                results.append({
                    "title": doc.get("title", "No Title"),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    "summary": doc.get("description") or doc.get("source") or "Biomedical research article."
                })

            # Cache result
            cache_arxiv_result(query, {"results": results})

            return results
    except Exception as e:
        logger.error(f"PubMed Search failed: {e}")
        return []

async def search_chemical_library(smiles: str, similarity_threshold: int = 70, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search ChEMBL for molecules similar to a SMILES string.
    Results are cached for 24 hours.
    """
    # VALIDATION: Skip if not a valid SMILES
    if not is_valid_smiles_for_search(smiles):
        logger.warning(f"Skipping ChEMBL search: input is not a valid SMILES string: {smiles[:50] if smiles else 'None'}...")
        return []

    # Check cache first
    cached = get_cached_chembl(smiles)
    if cached:
        logger.debug(f"Cache hit for ChEMBL: {smiles[:30]}...")
        return cached.get("molecules", [])

    # ChEMBL similarity search endpoint
    url = f"https://www.ebi.ac.uk/chembl/api/data/similarity/{smiles}/{similarity_threshold}.json"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"limit": limit}, timeout=15.0)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()

            molecules = []
            for mol in data.get("molecules", []):
                molecules.append({
                    "name": mol.get("pref_name") or mol.get("molecule_chembl_id"),
                    "smiles": mol.get("molecule_structures", {}).get("canonical_smiles"),
                    "similarity": mol.get("similarity")
                })

            # Cache result
            cache_chembl_result(smiles, {"molecules": molecules})

            return molecules
    except Exception as e:
        logger.error(f"ChEMBL Search failed: {e}")
        return []

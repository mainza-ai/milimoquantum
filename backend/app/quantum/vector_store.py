"""Milimo Quantum — Vector Store for Semantic Experiment Search.

ChromaDB-based vector store for embedding-based search over experiments,
code artifacts, notes, and conversation history. Enables "find similar
experiments" and context injection for agents.
"""
from __future__ import annotations

import hashlib
import logging

logger = logging.getLogger(__name__)

_collection = None


def is_chromadb_available() -> bool:
    """Check if ChromaDB is installed."""
    try:
        import chromadb  # noqa: F401
        return True
    except ImportError:
        return False


def _get_collection():
    """Get or create the experiments collection."""
    global _collection
    if _collection is not None:
        return _collection

    try:
        import chromadb
        from pathlib import Path

        persist_dir = str(Path.home() / ".milimoquantum" / "vectorstore")
        client = chromadb.PersistentClient(path=persist_dir)
        _collection = client.get_or_create_collection(
            name="quantum_experiments",
            metadata={"hnsw:space": "cosine"},
        )
        return _collection
    except ImportError:
        return None


def index_experiment(
    experiment_id: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    """Index an experiment into the vector store.

    Args:
        experiment_id: Unique identifier for the experiment
        content: Text content to embed (code, notes, results description)
        metadata: Optional metadata (project, agent, circuit_type, etc.)
    """
    collection = _get_collection()
    if collection is None:
        return {"error": "ChromaDB not installed. pip install chromadb"}

    try:
        doc_id = hashlib.sha256(experiment_id.encode()).hexdigest()[:16]
        meta = metadata or {}
        meta["experiment_id"] = experiment_id

        collection.upsert(
            documents=[content],
            metadatas=[meta],
            ids=[doc_id],
        )

        return {
            "indexed": True,
            "id": doc_id,
            "collection_count": collection.count(),
        }
    except Exception as e:
        return {"error": str(e)}


def search_similar(
    query: str,
    n_results: int = 5,
    filter_metadata: dict | None = None,
    project_id: str | None = None,
) -> dict:
    """Search for similar experiments using semantic similarity.

    Args:
        query: Natural language query or code snippet
        n_results: Number of results to return
        filter_metadata: Optional metadata filter (e.g. {"project": "vqe"})
    """
    collection = _get_collection()
    if collection is None:
        return {"error": "ChromaDB not installed. pip install chromadb"}

    if collection.count() == 0:
        return {"results": [], "message": "No experiments indexed yet"}

    try:
        where = filter_metadata or {}
        if project_id:
            where["project_id"] = project_id
            
        if not where:
            where = None

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
            where=where,
        )

        matches = []
        for i in range(len(results["ids"][0])):
            matches.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i][:500],  # truncate
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })

        return {
            "query": query,
            "results": matches,
            "total_indexed": collection.count(),
        }
    except Exception as e:
        return {"error": str(e)}


def get_context_for_agent(
    query: str,
    n_results: int = 3,
    project_id: str | None = None,
) -> str:
    """Get relevant context from past experiments for agent prompts.

    Returns a formatted string of relevant past experiments that can be
    injected into agent system prompts for context-aware responses.
    """
    result = search_similar(query, n_results=n_results, project_id=project_id)

    if "error" in result or not result.get("results"):
        return ""

    context_parts = ["## Relevant Past Experiments\n"]
    for match in result["results"]:
        meta = match.get("metadata", {})
        context_parts.append(
            f"**{meta.get('experiment_id', 'Unknown')}** "
            f"(project: {meta.get('project', 'default')})\n"
            f"{match['document'][:300]}\n"
        )

    return "\n".join(context_parts)


def get_store_stats() -> dict:
    """Get vector store statistics."""
    collection = _get_collection()
    if collection is None:
        return {
            "available": False,
            "error": "ChromaDB not installed. pip install chromadb",
        }

    return {
        "available": True,
        "total_documents": collection.count(),
        "collection_name": "quantum_experiments",
    }

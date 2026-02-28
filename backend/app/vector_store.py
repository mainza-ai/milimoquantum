"""Milimo Quantum — Vector Store for Semantic Search.

Uses Ollama embeddings + ChromaDB for local vector search
across conversations and experiment results.
"""
from __future__ import annotations

import json
import logging
import hashlib
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CHROMA_AVAILABLE = False
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    logger.info("chromadb not installed — vector search disabled. Install: pip install chromadb")

STORAGE_DIR = Path.home() / ".milimoquantum"
VECTOR_DIR = STORAGE_DIR / "vector_db"
MODEL_CACHE_DIR = STORAGE_DIR / "models"

# Runtime client
_client = None
_collection = None


def _get_collection(dimension: int = 384):
    """Get or create the ChromaDB collection based on embedding dimension."""
    global _client, _collection
    
    # Collection name includes dimension to avoid mismatch errors
    collection_name = f"milimoquantum_{dimension}"
    
    if _collection is not None and _collection.name == collection_name:
        return _collection

    if not CHROMA_AVAILABLE:
        return None

    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    if _client is None:
        _client = chromadb.PersistentClient(path=str(VECTOR_DIR))
    
    _collection = _client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"Vector store initialized (dim={dimension}) — {_collection.count()} documents indexed")
    return _collection


async def _get_embedding(text: str) -> list[float] | None:
    """Generate embedding via Ollama, falling back to local sentence‑transformer."""
    # Try Ollama first (if available)
    try:
        import httpx
        from app.config import settings

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/embed",
                json={
                    "model": "nomic-embed-text",
                    "input": text,
                },
                timeout=30.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                embeddings = data.get("embeddings", [])
                if embeddings:
                    return embeddings[0]
    except Exception:
        pass  # Ollama not reachable, fall through

    # Fallback: local sentence‑transformer (all‑MiniLM‑L6‑v2)
    try:
        from sentence_transformers import SentenceTransformer
        import os
        
        # Lazy load the model (cached globally)
        if not hasattr(_get_embedding, "_local_model"):
            MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            model_id = 'all-MiniLM-L6-v2'
            
            # Check if model folder exists to avoid network calls
            # sentence-transformers replaces / with _ in folder names typically
            model_folder = os.path.join(MODEL_CACHE_DIR, model_id.replace("/", "_"))
            
            # Use local_files_only=True if we have reason to believe it's already there
            # snapshot_download often creates a folder with the repo name
            is_cached = os.path.exists(model_folder) or any(model_id in d for d in os.listdir(MODEL_CACHE_DIR) if os.path.isdir(os.path.join(MODEL_CACHE_DIR, d)))
            
            _get_embedding._local_model = SentenceTransformer(
                model_id, 
                cache_folder=str(MODEL_CACHE_DIR),
                model_kwargs={"local_files_only": is_cached}
            )
        model = _get_embedding._local_model
        embedding = model.encode(text, normalize_embeddings=True).tolist()
        logger.debug("Generated embedding via local sentence‑transformer")
        return embedding
    except ImportError:
        logger.warning("sentence‑transformers not installed; install with 'pip install sentence‑transformers'")
    except Exception as e:
        logger.warning(f"Local embedding generation failed: {e}")
    return None


async def index_conversation(conversation_id: str, messages: list[dict], title: str = "") -> bool:
    """Index a conversation's messages into the vector store."""
    # Combine messages into a searchable document
    text_parts = []
    if title:
        text_parts.append(f"Title: {title}")

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if content and role in ("user", "assistant"):
            text_parts.append(f"{role}: {content[:500]}")

    full_text = "\n".join(text_parts)
    if not full_text.strip():
        return False

    # Generate embedding
    embedding = await _get_embedding(full_text[:2000])  # Limit to 2k chars for embedding
    
    # Get dimension from embedding or default to 384
    dim = len(embedding) if embedding else 384
    collection = _get_collection(dimension=dim)
    
    if collection is None:
        return False

    doc_id = f"conv_{conversation_id}"
    metadata = {
        "type": "conversation",
        "conversation_id": conversation_id,
        "title": title or "Untitled",
        "message_count": len(messages),
    }

    try:
        if embedding:
            collection.upsert(
                ids=[doc_id],
                documents=[full_text[:5000]],
                embeddings=[embedding],
                metadatas=[metadata],
            )
        else:
            # Fall back to ChromaDB's default embedding
            collection.upsert(
                ids=[doc_id],
                documents=[full_text[:5000]],
                metadatas=[metadata],
            )
        return True
    except Exception as e:
        logger.error(f"Failed to index conversation {conversation_id} (dim={dim}): {e}")
        return False


async def index_experiment(experiment_id: str, description: str, results: dict) -> bool:
    """Index an experiment result into the vector store."""
    collection = _get_collection()
    if collection is None:
        return False

    text = f"Experiment: {description}\nResults: {json.dumps(results)[:1000]}"
    embedding = await _get_embedding(text)

    doc_id = f"exp_{experiment_id}"
    metadata = {
        "type": "experiment",
        "experiment_id": experiment_id,
    }

    try:
        if embedding:
            collection.upsert(ids=[doc_id], documents=[text], embeddings=[embedding], metadatas=[metadata])
        else:
            collection.upsert(ids=[doc_id], documents=[text], metadatas=[metadata])
        return True
    except Exception as e:
        logger.error(f"Failed to index experiment {experiment_id}: {e}")
        return False


async def search(query: str, n_results: int = 10, doc_type: str | None = None) -> list[dict]:
    """Semantic search across indexed content.

    Args:
        query: Natural language search query.
        n_results: Maximum number of results to return.
        doc_type: Filter by type ('conversation' or 'experiment').

    Returns:
        List of search results with scores.
    """
    collection = _get_collection()
    if collection is None:
        return []

    if collection.count() == 0:
        return []

    try:
        where_filter = {"type": doc_type} if doc_type else None
        embedding = await _get_embedding(query)

        if embedding:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=min(n_results, collection.count()),
                where=where_filter,
            )
        else:
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count()),
                where=where_filter,
            )

        items = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"][0]):
                score = 1.0 - (results["distances"][0][i] if results.get("distances") else 0)
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                document = results["documents"][0][i] if results.get("documents") else ""
                items.append({
                    "id": doc_id,
                    "score": round(score, 4),
                    "type": metadata.get("type", "unknown"),
                    "title": metadata.get("title", ""),
                    "preview": document[:200] + "..." if len(document) > 200 else document,
                    "metadata": metadata,
                })
        return items
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []


async def reindex_all() -> dict:
    """Re-index all conversations from disk."""
    from app.storage import list_conversations, load_conversation

    convos = list_conversations()
    indexed = 0
    failed = 0

    for conv_summary in convos:
        conv_id = conv_summary["id"]
        data = load_conversation(conv_id)
        if data:
            success = await index_conversation(
                conv_id,
                data.get("messages", []),
                data.get("title", ""),
            )
            if success:
                indexed += 1
            else:
                failed += 1

    return {"indexed": indexed, "failed": failed, "total": len(convos)}


def get_status() -> dict:
    """Get vector store status."""
    collection = _get_collection()
    return {
        "available": CHROMA_AVAILABLE,
        "document_count": collection.count() if collection else 0,
        "storage_path": str(VECTOR_DIR),
    }

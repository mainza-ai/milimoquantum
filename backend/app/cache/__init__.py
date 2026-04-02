"""Milimo Quantum — Redis Caching Layer.

Provides caching for API responses, external API calls, and computed results.
"""
from __future__ import annotations

import json
import logging
import os
import hashlib
from typing import Any, Optional, Dict
from datetime import timedelta

logger = logging.getLogger(__name__)

# Redis connection
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.info("Redis not installed. Caching disabled. Install with: pip install redis")

# Cache configuration
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL_DEFAULT = int(os.getenv("CACHE_TTL_DEFAULT", "3600"))  # 1 hour
CACHE_TTL_SHORT = int(os.getenv("CACHE_TTL_SHORT", "60"))  # 1 minute
CACHE_TTL_LONG = int(os.getenv("CACHE_TTL_LONG", "86400"))  # 24 hours

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global _redis_client
    
    if not REDIS_AVAILABLE:
        return None
    
    if _redis_client is None:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            _redis_client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None
    
    return _redis_client


def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_data = json.dumps({"args": args, "kwargs": sorted(kwargs.items())}, sort_keys=True)
    key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
    return f"milimo:{prefix}:{key_hash}"


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    if not CACHE_ENABLED:
        return None
    
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache get failed for {key}: {e}")
    
    return None


def cache_set(key: str, value: Any, ttl: int = CACHE_TTL_DEFAULT) -> bool:
    """Set value in cache with TTL."""
    if not CACHE_ENABLED:
        return False
    
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete key from cache."""
    if not CACHE_ENABLED:
        return False
    
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete failed for {key}: {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching pattern."""
    if not CACHE_ENABLED:
        return 0
    
    client = get_redis_client()
    if client is None:
        return 0
    
    try:
        keys = client.keys(f"milimo:{pattern}")
        if keys:
            return client.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache delete pattern failed for {pattern}: {e}")
    
    return 0


# ── Decorator for caching function results ─────────────────────────

def cached(prefix: str, ttl: int = CACHE_TTL_DEFAULT):
    """
    Decorator to cache function results.
    
    Usage:
        @cached("pubchem", ttl=3600)
        async def search_pubchem(name: str):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Skip 'self' or 'cls' for methods
            cache_args = args[1:] if args and hasattr(args[0], '__class__') else args
            
            key = _generate_cache_key(prefix, *cache_args, **kwargs)
            
            # Try cache first
            cached_result = cache_get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                cache_set(key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# ── Specific Cache Functions ─────────────────────────────────────

def cache_pubchem_result(name: str, result: Dict) -> bool:
    """Cache PubChem API result."""
    key = _generate_cache_key("pubchem", name=name)
    return cache_set(key, result, ttl=CACHE_TTL_LONG)


def get_cached_pubchem(name: str) -> Optional[Dict]:
    """Get cached PubChem result."""
    key = _generate_cache_key("pubchem", name=name)
    return cache_get(key)


def cache_arxiv_result(query: str, result: Dict) -> bool:
    """Cache arXiv API result."""
    key = _generate_cache_key("arxiv", query=query)
    return cache_set(key, result, ttl=CACHE_TTL_DEFAULT)


def get_cached_arxiv(query: str) -> Optional[Dict]:
    """Get cached arXiv result."""
    key = _generate_cache_key("arxiv", query=query)
    return cache_get(key)


def cache_chembl_result(smiles: str, result: Dict) -> bool:
    """Cache ChEMBL similarity search result."""
    key = _generate_cache_key("chembl", smiles=smiles)
    return cache_set(key, result, ttl=CACHE_TTL_LONG)


def get_cached_chembl(smiles: str) -> Optional[Dict]:
    """Get cached ChEMBL result."""
    key = _generate_cache_key("chembl", smiles=smiles)
    return cache_get(key)


def cache_pdb_result(pdb_id: str, result: Dict) -> bool:
    """Cache PDB structure result."""
    key = _generate_cache_key("pdb", pdb_id=pdb_id)
    return cache_set(key, result, ttl=CACHE_TTL_LONG)


def get_cached_pdb(pdb_id: str) -> Optional[Dict]:
    """Get cached PDB result."""
    key = _generate_cache_key("pdb", pdb_id=pdb_id)
    return cache_get(key)


def cache_benchmark_result(circuit_type: str, params: Dict, result: Dict) -> bool:
    """Cache benchmark result."""
    key = _generate_cache_key("benchmark", circuit_type=circuit_type, **params)
    return cache_set(key, result, ttl=CACHE_TTL_SHORT)


def get_cached_benchmark(circuit_type: str, params: Dict) -> Optional[Dict]:
    """Get cached benchmark result."""
    key = _generate_cache_key("benchmark", circuit_type=circuit_type, **params)
    return cache_get(key)


def cache_vqe_result(hamiltonian: str, ansatz: str, result: Dict) -> bool:
    """Cache VQE execution result."""
    key = _generate_cache_key("vqe", hamiltonian=hamiltonian, ansatz=ansatz)
    return cache_set(key, result, ttl=CACHE_TTL_DEFAULT)


def get_cached_vqe(hamiltonian: str, ansatz: str) -> Optional[Dict]:
    """Get cached VQE result."""
    key = _generate_cache_key("vqe", hamiltonian=hamiltonian, ansatz=ansatz)
    return cache_get(key)


# ── Cache Statistics ─────────────────────────────────────────────

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    client = get_redis_client()
    if client is None:
        return {
            "enabled": False,
            "connected": False,
            "reason": "Redis not available"
        }
    
    try:
        info = client.info("memory")
        dbsize = client.dbsize()
        
        return {
            "enabled": CACHE_ENABLED,
            "connected": True,
            "keys": dbsize,
            "used_memory": info.get("used_memory_human", "unknown"),
            "peak_memory": info.get("used_memory_peak_human", "unknown"),
        }
    except Exception as e:
        return {
            "enabled": CACHE_ENABLED,
            "connected": False,
            "error": str(e)
        }


def clear_all_caches() -> Dict[str, int]:
    """Clear all Milimo caches."""
    results = {}
    
    patterns = [
        "pubchem:*",
        "arxiv:*",
        "chembl:*",
        "pdb:*",
        "benchmark:*",
        "vqe:*",
    ]
    
    for pattern in patterns:
        count = cache_delete_pattern(pattern)
        results[pattern] = count
    
    return results

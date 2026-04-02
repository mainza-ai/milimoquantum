"""Milimo Quantum — Cache Management Routes."""
from fastapi import APIRouter, HTTPException
from app.cache import (
    get_cache_stats,
    clear_all_caches,
    CACHE_ENABLED,
)

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/status")
async def cache_status():
    """Get cache status and statistics."""
    return {
        "enabled": CACHE_ENABLED,
        **get_cache_stats()
    }


@router.post("/clear")
async def clear_cache():
    """Clear all caches."""
    if not CACHE_ENABLED:
        raise HTTPException(status_code=400, detail="Caching is disabled")
    
    results = clear_all_caches()
    return {
        "message": "Caches cleared",
        "keys_deleted": results
    }


@router.get("/health")
async def cache_health():
    """Health check for cache."""
    stats = get_cache_stats()
    return {
        "healthy": stats.get("connected", False),
        "details": stats
    }

"""Milimo Quantum - QRNG API Endpoints.

Exposes the quantum random number generator to the outside world.
"""
from __future__ import annotations

from typing import Dict, List, Any
from fastapi import APIRouter

from app.quantum.qrng import qrng_provider

router = APIRouter(prefix="/api/qrng", tags=["qrng"])


@router.get("/status")
async def get_qrng_status():
    """Get the current status of the quantum entropy pool."""
    return qrng_provider.get_status()


@router.get("/bits/{length}")
async def get_random_bits(length: int):
    """Fetch random bits from the quantum entropy pool."""
    if length > 10000:
        return {"error": "Maximum length is 10000 bits at a time"}
    bits = await qrng_provider.get_random_bitstring(length)
    return {
        "format": "bitstring",
        "length": length,
        "data": bits,
        "quantum_certified": qrng_provider.get_status().get("quantum", False)
    }


@router.get("/integers")
async def get_random_ints(count: int = 1, min_val: int = 0, max_val: int = 100):
    """Fetch random integers between min_val and max_val using quantum entropy."""
    if count > 1000:
        return {"error": "Maximum count is 1000 integers at a time"}
    if min_val >= max_val:
        return {"error": "min_val must be less than max_val"}
    
    ints = await qrng_provider.get_random_integers(count, min_val, max_val)
    return {
        "format": "integers",
        "count": count,
        "min": min_val,
        "max": max_val,
        "data": ints,
        "quantum_certified": qrng_provider.get_status().get("quantum", False)
    }

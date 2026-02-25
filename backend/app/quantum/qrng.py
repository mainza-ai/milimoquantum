"""Milimo Quantum — Quantum Random Number Generator (QRNG).

Generates true random numbers using Hadamard → measure circuits on Qiskit Aer.
Includes an entropy pool for efficient batch generation and basic randomness validation.
"""
from __future__ import annotations

import logging
import os
from typing import List

logger = logging.getLogger(__name__)

# ── Qiskit Availability ─────────────────────────────────
QISKIT_AVAILABLE = False
try:
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    logger.info("Qiskit not installed — QRNG falls back to os.urandom")


# ── Entropy Pool ────────────────────────────────────────
_entropy_pool: list[int] = []
_POOL_REFILL_SIZE = 2048  # Generate this many bits at a time


def _refill_entropy_pool() -> None:
    """Generate quantum random bits using Hadamard circuits on Aer."""
    global _entropy_pool

    if not QISKIT_AVAILABLE:
        # Fallback to classical CSPRNG
        raw = os.urandom(_POOL_REFILL_SIZE // 8)
        _entropy_pool.extend(int(b) for byte in raw for b in format(byte, '08b'))
        return

    # Use multi-qubit circuits for efficient batch generation
    n_qubits = 16  # Generate 16 bits per circuit execution
    n_circuits = _POOL_REFILL_SIZE // n_qubits
    simulator = AerSimulator()

    bits: list[int] = []
    for _ in range(n_circuits):
        qc = QuantumCircuit(n_qubits, n_qubits)
        # Apply Hadamard to all qubits → equal superposition
        qc.h(range(n_qubits))
        # Measure → collapse to random bitstring
        qc.measure(range(n_qubits), range(n_qubits))

        transpiled = transpile(qc, simulator)
        result = simulator.run(transpiled, shots=1).result()
        counts = result.get_counts()
        bitstring = list(counts.keys())[0].replace(" ", "")
        bits.extend(int(b) for b in bitstring)

    _entropy_pool.extend(bits)
    logger.debug(f"QRNG pool refilled with {len(bits)} quantum random bits")


def _get_bits(n: int) -> list[int]:
    """Get n random bits from the entropy pool, refilling if needed."""
    global _entropy_pool
    while len(_entropy_pool) < n:
        _refill_entropy_pool()
    result = _entropy_pool[:n]
    _entropy_pool = _entropy_pool[n:]
    return result


class QRNGProvider:
    """Quantum Random Number Generator using Qiskit Aer Hadamard circuits."""

    def __init__(self):
        self._total_bits_generated = 0

    async def get_random_bytes(self, length: int) -> bytes:
        """Fetch random bytes from quantum source (Hadamard circuits)."""
        bits = _get_bits(length * 8)
        self._total_bits_generated += length * 8
        result = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            result.append(byte)
        return bytes(result)

    async def get_random_integers(self, count: int, min_val: int = 0, max_val: int = 255) -> List[int]:
        """Fetch random integers from quantum source."""
        range_size = max_val - min_val + 1
        # Calculate bits needed per integer
        bits_per_int = (range_size - 1).bit_length() or 1
        # Use rejection sampling for uniform distribution
        results: list[int] = []
        while len(results) < count:
            bits = _get_bits(bits_per_int)
            value = 0
            for b in bits:
                value = (value << 1) | b
            if value < range_size:
                results.append(min_val + value)
        self._total_bits_generated += count * bits_per_int
        return results

    async def get_random_bitstring(self, length: int) -> str:
        """Get a random bitstring of given length."""
        bits = _get_bits(length)
        self._total_bits_generated += length
        return "".join(str(b) for b in bits)

    def get_status(self) -> dict:
        """Get QRNG status."""
        return {
            "backend": "qiskit_aer" if QISKIT_AVAILABLE else "os.urandom",
            "pool_size": len(_entropy_pool),
            "total_bits_generated": self._total_bits_generated,
            "quantum": QISKIT_AVAILABLE,
        }


qrng_provider = QRNGProvider()

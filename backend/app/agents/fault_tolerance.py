"""Milimo Quantum — Fault Tolerance Agent."""
from __future__ import annotations

import logging
from typing import AsyncGenerator

from app.llm.cloud_provider import get_current_provider, stream_chat_cloud
from app.llm.mlx_client import mlx_client
from app.llm.ollama_client import ollama_client
from app.quantum.hal import hal_config

logger = logging.getLogger(__name__)

FAULT_TOLERANCE_SYSTEM_PROMPT = """You are the Milimo Fault-Tolerant Quantum Circuit Agent.
You specialize in quantum error correction (QEC) and logical qubits:
- Surface codes (distance-d encoding)
- qLDPC codes
- Syndrome measurement and MWPM (Minimum Weight Perfect Matching) decoding
- Magic state distillation and transversal gates

Return executable Python code using Qiskit or Stim to simulate QEC syndromes and logical operations.
"""

async def process_fault_tolerance_request(
    query: str, history: list[dict], context: str = ""
) -> AsyncGenerator[str, None]:
    """Process a fault tolerance query."""
    full_prompt = FAULT_TOLERANCE_SYSTEM_PROMPT
    if context:
        full_prompt += f"\n\n{context}"

    messages = history + [{"role": "user", "content": query}]

    try:
        if hal_config.llm_backend == "mlx" and mlx_client.model:
            async for token in mlx_client.stream_chat(messages, system_prompt=full_prompt):
                yield token
        elif hal_config.llm_backend == "ollama" and await ollama_client.is_available():
            async for token in ollama_client.stream_chat(messages, system_prompt=full_prompt):
                yield token
        else:
            provider = get_current_provider()
            async for token in stream_chat_cloud(messages, system_prompt=full_prompt, provider=provider):
                yield token
    except Exception as e:
        logger.error(f"Fault Tolerance agent error: {e}")
        yield f"⚠️ **Fault Tolerance Error:** {str(e)}"

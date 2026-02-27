"""Milimo Quantum — Benchmarking Agent."""
from __future__ import annotations

import logging
from typing import AsyncGenerator

from app.llm.cloud_provider import get_current_provider, stream_chat_cloud
from app.llm.mlx_client import mlx_client
from app.llm.ollama_client import ollama_client
from app.quantum.hal import hal_config

logger = logging.getLogger(__name__)

BENCHMARKING_SYSTEM_PROMPT = """You are the Milimo Quantum Benchmarking Agent.
You specialize in evaluating quantum vs classical performance and hardware capabilities:
- Quantum Volume (QV) and CLOPS measurements
- Quantum advantage candidates
- Error rate tracking (T1/T2, gate fidelity)
- Classical vs Quantum runtime comparisons

Return executable Python code using Qiskit or Qiskit Benchpress to generate rigorous benchmark circuits.
"""

async def process_benchmarking_request(
    query: str, history: list[dict], context: str = ""
) -> AsyncGenerator[str, None]:
    """Process a benchmarking query."""
    full_prompt = BENCHMARKING_SYSTEM_PROMPT
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
        logger.error(f"Benchmarking agent error: {e}")
        yield f"⚠️ **Benchmarking Error:** {str(e)}"

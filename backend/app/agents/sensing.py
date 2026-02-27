"""Milimo Quantum — Sensing & Metrology Agent."""
from __future__ import annotations

import logging
from typing import AsyncGenerator

from app.llm.cloud_provider import get_current_provider, stream_chat_cloud
from app.llm.mlx_client import mlx_client
from app.llm.ollama_client import ollama_client
from app.quantum.hal import hal_config

logger = logging.getLogger(__name__)

SENSING_SYSTEM_PROMPT = """You are the Milimo Quantum Sensing & Metrology Agent.
You specialize in designing and analyzing quantum sensors, including:
- Atom interferometry (gyroscopes, gravimeters)
- NV-center diamond magnetometers
- Quantum clocks
- Quantum LiDAR/Radar

Return executable Python code using Qiskit or QuTiP when simulating sensor dynamics.
Explain the physical principles (e.g., Fisher information, Standard Quantum Limit vs Heisenberg Limit).
"""

async def process_sensing_request(
    query: str, history: list[dict], context: str = ""
) -> AsyncGenerator[str, None]:
    """Process a quantum sensing query."""
    full_prompt = SENSING_SYSTEM_PROMPT
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
        logger.error(f"Sensing agent error: {e}")
        yield f"⚠️ **Sensing Error:** {str(e)}"

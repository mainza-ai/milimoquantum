"""Milimo Quantum — Ollama LLM Client with streaming support."""
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for Ollama API with streaming."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
        self._auto_detected_model: str | None = None

    @property
    def model(self) -> str:
        """Read the current model from settings. Auto-detect if not set."""
        configured = settings.ollama_model
        if configured:
            return configured
        # Auto-detect: use cached result if available
        if self._auto_detected_model:
            return self._auto_detected_model
        # Try synchronous auto-detection
        try:
            import httpx as _httpx
            resp = _httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                if models:
                    # Sort by modified_at descending → most recently pulled
                    models.sort(key=lambda m: m.get("modified_at", ""), reverse=True)
                    self._auto_detected_model = models[0]["name"]
                    logger.info(f"Auto-detected Ollama model: {self._auto_detected_model}")
                    return self._auto_detected_model
        except Exception:
            pass
        return "llama3.2:latest"  # Fallback

    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            resp = await self._client.get("/api/tags")
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[str]:
        """List available models."""
        try:
            resp = await self._client.get("/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    async def stream_chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion tokens from Ollama."""
        model = model or self.model
        payload: dict = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if system_prompt:
            payload["messages"] = [
                {"role": "system", "content": system_prompt},
                *messages,
            ]

        try:
            async with self._client.stream(
                "POST", "/api/chat", json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            # Handle Ollama error responses (e.g. model not found)
                            if "error" in chunk:
                                error_msg = chunk["error"]
                                logger.error(f"Ollama error: {error_msg}")
                                yield f"⚠️ **Ollama Error:** {error_msg}\n\nPlease check your model selection in Settings."
                                return
                            if "message" in chunk and "content" in chunk["message"]:
                                token = chunk["message"]["content"]
                                if token:
                                    yield token
                            if chunk.get("done", False):
                                return
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError:
            yield "⚠️ **Ollama is not running.** Please start Ollama with `ollama serve` and try again."
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"⚠️ **Error communicating with LLM:** {str(e)}"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        """Non-streaming single-shot generation."""
        model = model or self.model
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            resp = await self._client.post("/api/generate", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if "error" in data:
                    return f"⚠️ **Ollama Error:** {data['error']}"
                return data.get("response", "")
            return f"⚠️ **Ollama error:** HTTP {resp.status_code}"
        except httpx.ConnectError:
            return "⚠️ **Ollama is not running.** Please start Ollama."
        except Exception as e:
            return f"⚠️ **LLM Error:** {str(e)}"

    async def close(self):
        await self._client.aclose()


# Singleton instance
ollama_client = OllamaClient()

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

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

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
                            if "message" in chunk and "content" in chunk["message"]:
                                token = chunk["message"]["content"]
                                if token:
                                    yield token
                            if chunk.get("done", False):
                                return
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError:
            yield "[Ollama is not running. Please start Ollama with `ollama serve` and try again.]"
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"[Error communicating with LLM: {str(e)}]"

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
                return resp.json().get("response", "")
            return f"[Ollama error: HTTP {resp.status_code}]"
        except httpx.ConnectError:
            return "[Ollama is not running. Please start Ollama.]"
        except Exception as e:
            return f"[LLM Error: {str(e)}]"

    async def close(self):
        await self._client.aclose()


# Singleton instance
ollama_client = OllamaClient()

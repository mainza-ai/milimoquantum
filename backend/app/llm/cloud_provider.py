"""Milimo Quantum — Cloud AI Provider.

Supports Anthropic, OpenAI, and Google Gemini as alternative LLM backends.
Falls back to Ollama if no API keys are configured.
"""
from __future__ import annotations

import logging
import os
from typing import AsyncIterator

logger = logging.getLogger(__name__)

# ── Provider Configuration ──────────────────────────────
CLOUD_PROVIDERS = {
    "anthropic": {
        "name": "Anthropic Claude",
        "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-3-5-haiku-20241022"],
        "env_key": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
        "env_key": "OPENAI_API_KEY",
    },
    "gemini": {
        "name": "Google Gemini",
        "models": ["gemini-2.0-flash", "gemini-1.5-pro"],
        "env_key": "GOOGLE_API_KEY",
    },
}

# Runtime state
_active_provider: str | None = None
_active_model: str | None = None


def get_available_providers() -> list[dict]:
    """Return list of available cloud providers (those with API keys set)."""
    available = []
    for provider_id, info in CLOUD_PROVIDERS.items():
        key = os.environ.get(info["env_key"], "")
        available.append({
            "id": provider_id,
            "name": info["name"],
            "models": info["models"],
            "configured": bool(key),
        })
    return available


def set_provider(provider: str, model: str | None = None) -> dict:
    """Set the active cloud provider and model."""
    global _active_provider, _active_model

    if provider == "ollama":
        _active_provider = None
        _active_model = None
        return {"provider": "ollama", "model": None, "status": "Using local Ollama"}

    if provider not in CLOUD_PROVIDERS:
        return {"error": f"Unknown provider: {provider}"}

    info = CLOUD_PROVIDERS[provider]
    key = os.environ.get(info["env_key"], "")
    if not key:
        return {"error": f"API key not set. Set {info['env_key']} environment variable."}

    _active_provider = provider
    _active_model = model or info["models"][0]
    logger.info(f"Cloud AI provider set to {provider}/{_active_model}")
    return {"provider": provider, "model": _active_model, "status": "active"}


def get_current_provider() -> dict:
    """Get the currently active provider."""
    if _active_provider is None:
        return {"provider": "ollama", "model": None}
    return {"provider": _active_provider, "model": _active_model}


async def stream_chat_cloud(
    messages: list[dict],
    system_prompt: str = "",
) -> AsyncIterator[str]:
    """Stream chat via the active cloud provider."""
    if _active_provider is None:
        yield "[Cloud AI not configured — using Ollama]"
        return

    try:
        if _active_provider == "anthropic":
            async for token in _stream_anthropic(messages, system_prompt):
                yield token
        elif _active_provider == "openai":
            async for token in _stream_openai(messages, system_prompt):
                yield token
        elif _active_provider == "gemini":
            async for token in _stream_gemini(messages, system_prompt):
                yield token
    except ImportError as e:
        yield f"[Error: {_active_provider} SDK not installed. Install with pip. {e}]"
    except Exception as e:
        yield f"[Cloud AI error: {str(e)}]"


async def _stream_anthropic(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via Anthropic Claude API."""
    import anthropic

    client = anthropic.AsyncAnthropic()
    formatted = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]

    async with client.messages.stream(
        model=_active_model or "claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=formatted,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def _stream_openai(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via OpenAI API."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    formatted = [{"role": "system", "content": system_prompt}] if system_prompt else []
    formatted += [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]

    stream = await client.chat.completions.create(
        model=_active_model or "gpt-4o",
        messages=formatted,
        max_tokens=4096,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def _stream_gemini(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via Google Gemini API."""
    from google import genai

    client = genai.Client()
    formatted_history = []
    for m in messages[:-1]:
        if m["role"] in ("user", "assistant"):
            role = "user" if m["role"] == "user" else "model"
            formatted_history.append({"role": role, "parts": [{"text": m["content"]}]})

    last_msg = messages[-1]["content"] if messages else ""

    config = {"system_instruction": system_prompt} if system_prompt else {}
    response = client.models.generate_content_stream(
        model=_active_model or "gemini-2.0-flash",
        contents=[*formatted_history, {"role": "user", "parts": [{"text": last_msg}]}],
        config=config,
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text

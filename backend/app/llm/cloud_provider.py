"""Milimo Quantum — Cloud AI Provider.

Supports Anthropic, OpenAI, Google Gemini, Cohere, Mistral, DeepSeek, OpenRouter, and NVIDIA NIM
as alternative LLM backends. Falls back to Ollama if no API keys are configured.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import AsyncIterator

logger = logging.getLogger(__name__)

from app.config import settings

# ── Provider Configuration ──────────────────────────────
CLOUD_PROVIDERS = {
    "anthropic": {
        "name": "Anthropic Claude",
        "models": settings.anthropic_models,
        "env_key": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "name": "OpenAI",
        "models": settings.openai_models,
        "env_key": "OPENAI_API_KEY",
    },
    "gemini": {
        "name": "Google Gemini",
        "models": settings.gemini_models,
        "env_key": "GOOGLE_API_KEY",
    },
    "cohere": {
        "name": "Cohere Command R+",
        "models": settings.cohere_models,
        "env_key": "COHERE_API_KEY",
    },
    "mistral": {
        "name": "Mistral AI",
        "models": settings.mistral_models,
        "env_key": "MISTRAL_API_KEY",
    },
    "deepseek": {
        "name": "DeepSeek",
        "models": settings.deepseek_models,
        "env_key": "DEEPSEEK_API_KEY",
    },
    "openrouter": {
        "name": "OpenRouter",
        "models": settings.openrouter_models,
        "env_key": "OPENROUTER_API_KEY",
    },
    "nvidia": {
        "name": "NVIDIA NIM",
        "models": settings.nvidia_models,
        "env_key": "NVIDIA_API_KEY",
    },
}

# Runtime state
_active_provider: str | None = None
_active_model: str | None = None

_CLOUD_SETTINGS_FILE = Path.home() / ".milimoquantum" / "cloud_settings.json"


def _load_cloud_settings() -> None:
    """Load the saved cloud configurations from disk to os.environ and memory."""
    global _active_provider, _active_model

    if not _CLOUD_SETTINGS_FILE.exists():
        return

    try:
        data = json.loads(_CLOUD_SETTINGS_FILE.read_text(encoding="utf-8"))
        
        # Load keys into env
        keys = data.get("api_keys", {})
        for provider_id, key in keys.items():
            if provider_id in CLOUD_PROVIDERS and key:
                os.environ[CLOUD_PROVIDERS[provider_id]["env_key"]] = key

        # Load active provider selection
        saved_provider = data.get("active_provider")
        saved_model = data.get("active_model")
        
        if saved_provider == "ollama" or not saved_provider:
            _active_provider = None
            _active_model = None
        else:
            _active_provider = saved_provider
            _active_model = saved_model
            
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load cloud settings: {e}")


def _save_cloud_settings() -> None:
    """Persist current cloud configuration to disk."""
    _CLOUD_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load latest state from disk first to avoid overwriting other workers' keys
    if _CLOUD_SETTINGS_FILE.exists():
        try:
            existing = json.loads(_CLOUD_SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    else:
        existing = {}
        
    current_keys = existing.get("api_keys", {})
    for provider_id, info in CLOUD_PROVIDERS.items():
        key = os.environ.get(info["env_key"])
        if key:
            current_keys[provider_id] = key

    data = {
        "active_provider": _active_provider or "ollama",
        "active_model": _active_model,
        "api_keys": current_keys
    }
    
    _CLOUD_SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# Execute load upon startup
_load_cloud_settings()


def get_available_providers() -> list[dict]:
    """Return list of available cloud providers (those with API keys set)."""
    _load_cloud_settings()
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


def set_provider(provider: str, model: str | None = None, api_key: str | None = None) -> dict:
    """Set the active cloud provider, model, and optionally API key."""
    global _active_provider, _active_model
    _load_cloud_settings()

    if provider == "ollama":
        _active_provider = None
        _active_model = None
        _save_cloud_settings()
        return {"provider": "ollama", "model": None, "status": "Using local Ollama"}

    if provider not in CLOUD_PROVIDERS:
        return {"error": f"Unknown provider: {provider}"}

    info = CLOUD_PROVIDERS[provider]
    
    if api_key:
        os.environ[info["env_key"]] = api_key

    key = os.environ.get(info["env_key"], "")
    if not key:
        return {"error": f"API key not set. Set {info['env_key']} environment variable.", "missing_key": True}

    _active_provider = provider
    _active_model = model or info["models"][0]
    
    _save_cloud_settings()
    logger.info(f"Cloud AI provider set to {provider}/{_active_model}")
    return {"provider": provider, "model": _active_model, "status": "active"}


def get_current_provider() -> dict:
    """Get the currently active provider."""
    _load_cloud_settings()
    if _active_provider is None:
        return {"provider": "ollama", "model": None}
    return {"provider": _active_provider, "model": _active_model}


async def stream_chat_cloud(
    messages: list[dict],
    system_prompt: str = "",
) -> AsyncIterator[str]:
    """Stream chat via the active cloud provider with automatic fallback."""
    _load_cloud_settings()
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
        elif _active_provider == "cohere":
            async for token in _stream_cohere(messages, system_prompt):
                yield token
        elif _active_provider == "mistral":
            async for token in _stream_mistral(messages, system_prompt):
                yield token
        elif _active_provider == "deepseek":
            async for token in _stream_deepseek(messages, system_prompt):
                yield token
        elif _active_provider == "openrouter":
            async for token in _stream_openrouter(messages, system_prompt):
                yield token
        elif _active_provider == "nvidia":
            async for token in _stream_nvidia(messages, system_prompt):
                yield token
    except ImportError as e:
        logger.warning(f"Provider {_active_provider} SDK not installed: {e}. Trying fallback.")
        async for token in _stream_fallback(messages, system_prompt):
            yield token
    except Exception as e:
        logger.warning(f"Provider {_active_provider} error: {e}. Trying fallback.")
        async for token in _stream_fallback(messages, system_prompt):
            yield token


async def _stream_fallback(
    messages: list[dict],
    system_prompt: str = "",
) -> AsyncIterator[str]:
    """Fallback streaming through configured providers in priority order."""
    fallback_order = ["openrouter", "nvidia", "deepseek", "mistral", "cohere", "gemini", "openai", "anthropic"]
    tried = set()
    tried.add(_active_provider)

    for provider_id in fallback_order:
        if provider_id in tried:
            continue
        info = CLOUD_PROVIDERS.get(provider_id)
        if not info:
            continue
        key = os.environ.get(info["env_key"], "")
        if not key:
            continue

        tried.add(provider_id)
        logger.info(f"Falling back to provider: {provider_id}")
        try:
            if provider_id == "anthropic":
                async for token in _stream_anthropic(messages, system_prompt):
                    yield token
                return
            elif provider_id == "openai":
                async for token in _stream_openai(messages, system_prompt):
                    yield token
                return
            elif provider_id == "gemini":
                async for token in _stream_gemini(messages, system_prompt):
                    yield token
                return
            elif provider_id == "cohere":
                async for token in _stream_cohere(messages, system_prompt):
                    yield token
                return
            elif provider_id == "mistral":
                async for token in _stream_mistral(messages, system_prompt):
                    yield token
                return
            elif provider_id == "deepseek":
                async for token in _stream_deepseek(messages, system_prompt):
                    yield token
                return
            elif provider_id == "openrouter":
                async for token in _stream_openrouter(messages, system_prompt):
                    yield token
                return
            elif provider_id == "nvidia":
                async for token in _stream_nvidia(messages, system_prompt):
                    yield token
                return
        except Exception as e:
            logger.warning(f"Fallback provider {provider_id} also failed: {e}")
            continue

    yield f"[Error: All configured providers failed. Last tried: {_active_provider}]"


async def _stream_anthropic(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via Anthropic Claude API."""
    import anthropic

    client = anthropic.AsyncAnthropic()
    formatted = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]

    async with client.messages.stream(
        model=_active_model or settings.anthropic_models[0],
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
        model=_active_model or settings.openai_models[0],
        messages=formatted,
        max_tokens=4096,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def _stream_gemini(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via Google Gemini API (async, non-blocking)."""
    from google import genai

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        yield "[ERROR] GOOGLE_API_KEY not set"
        return

    client = genai.Client(api_key=api_key)
    formatted_history = []
    for m in messages[:-1]:
        if m["role"] in ("user", "assistant"):
            role = "user" if m["role"] == "user" else "model"
            formatted_history.append({"role": role, "parts": [{"text": m["content"]}]})

    last_msg = messages[-1]["content"] if messages else ""

    config = {"system_instruction": system_prompt} if system_prompt else {}

    # Use asyncio.to_thread to offload the blocking sync call to a thread pool
    import asyncio

    def _generate():
        return client.models.generate_content_stream(
            model=_active_model or settings.gemini_models[0],
            contents=[*formatted_history, {"role": "user", "parts": [{"text": last_msg}]}],
            config=config,
        )

    response = await asyncio.to_thread(_generate)

    for chunk in response:
        if chunk.text:
            yield chunk.text


async def _stream_cohere(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via Cohere Command R+ API (OpenAI-compatible endpoint)."""
    import httpx

    api_key = os.environ.get("COHERE_API_KEY", "")
    formatted = [{"role": "system", "content": system_prompt}] if system_prompt else []
    formatted += [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            "https://api.cohere.ai/v2/chat",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": _active_model or settings.cohere_models[0],
                "messages": formatted,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    import json
                    try:
                        data = json.loads(line[5:].strip())
                        if data.get("type") == "content-delta":
                            text = data.get("delta", {}).get("message", {}).get("content", {}).get("text", "")
                            if text:
                                yield text
                    except json.JSONDecodeError:
                        pass


async def _stream_mistral(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via Mistral AI API (OpenAI-compatible endpoint)."""
    import httpx

    api_key = os.environ.get("MISTRAL_API_KEY", "")
    formatted = [{"role": "system", "content": system_prompt}] if system_prompt else []
    formatted += [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": _active_model or settings.mistral_models[0],
                "messages": formatted,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:") and line.strip() != "data: [DONE]":
                    import json
                    try:
                        data = json.loads(line[5:].strip())
                        content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        pass


async def _stream_deepseek(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via DeepSeek API (OpenAI-compatible endpoint)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url="https://api.deepseek.com",
    )
    formatted = [{"role": "system", "content": system_prompt}] if system_prompt else []
    formatted += [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]

    stream = await client.chat.completions.create(
        model=_active_model or settings.deepseek_models[0],
        messages=formatted,
        max_tokens=4096,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def _stream_openrouter(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via OpenRouter API (OpenAI-compatible endpoint).

    OpenRouter aggregates many models behind a single API key,
    making it easy to switch between providers without changing credentials.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url="https://openrouter.ai/api/v1",
    )
    formatted = [{"role": "system", "content": system_prompt}] if system_prompt else []
    formatted += [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]

    stream = await client.chat.completions.create(
        model=_active_model or settings.openrouter_models[0],
        messages=formatted,
        max_tokens=4096,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def _stream_nvidia(messages: list[dict], system_prompt: str) -> AsyncIterator[str]:
    """Stream via NVIDIA NIM API (OpenAI-compatible endpoint).

    NVIDIA NIM provides optimized inference for models like Llama,
    Mistral, and Nemotron through a single API endpoint.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=os.environ.get("NVIDIA_API_KEY", ""),
        base_url="https://integrate.api.nvidia.com/v1",
    )
    formatted = [{"role": "system", "content": system_prompt}] if system_prompt else []
    formatted += [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ("user", "assistant")]

    stream = await client.chat.completions.create(
        model=_active_model or settings.nvidia_models[0],
        messages=formatted,
        max_tokens=4096,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


# ── Dynamic Model Discovery ─────────────────────────────

async def fetch_cloud_models(provider: str) -> list[dict]:
    """Fetch available models for a cloud provider from their API.

    Returns a list of dicts with keys: id, name, owner, description, context_length.
    Falls back to hardcoded defaults if the API is unavailable.
    """
    if provider == "openrouter":
        return await _fetch_openrouter_models()
    elif provider == "nvidia":
        return await _fetch_nvidia_models()
    else:
        info = CLOUD_PROVIDERS.get(provider, {})
        return [{"id": m, "name": m, "owner": provider} for m in info.get("models", [])]


async def search_cloud_models(provider: str, query: str = "", limit: int = 50) -> list[dict]:
    """Search models for a cloud provider."""
    models = await fetch_cloud_models(provider)
    if not query:
        return models[:limit]
    q = query.lower()
    return [m for m in models if q in m["id"].lower() or q in m.get("name", "").lower() or q in m.get("owner", "").lower()][:limit]


async def _fetch_openrouter_models() -> list[dict]:
    """Fetch available models from OpenRouter's public API."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("data", [])
                return [
                    {
                        "id": m["id"],
                        "name": m.get("name", m["id"]),
                        "owner": m.get("id", "").split("/")[0] if "/" in m["id"] else "unknown",
                        "description": m.get("description", ""),
                        "context_length": m.get("context_length"),
                        "pricing": m.get("pricing", {}),
                    }
                    for m in sorted(models, key=lambda x: x.get("name", ""))
                ]
    except Exception as e:
        logger.warning(f"Failed to fetch OpenRouter models: {e}")

    return [{"id": m, "name": m, "owner": m.split("/")[0]} for m in settings.openrouter_models]


async def _fetch_nvidia_models() -> list[dict]:
    """Fetch available models from NVIDIA NIM API."""
    api_key = os.environ.get("NVIDIA_API_KEY", "")
    if not api_key:
        return [{"id": m, "name": m, "owner": "nvidia"} for m in settings.nvidia_models]

    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://integrate.api.nvidia.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("data", [])
                return [
                    {
                        "id": m["id"],
                        "name": m.get("name", m["id"]),
                        "owner": m.get("owned_by", "nvidia"),
                        "description": "",
                    }
                    for m in sorted(models, key=lambda x: x.get("id", ""))
                ]
    except Exception as e:
        logger.warning(f"Failed to fetch NVIDIA models: {e}")

    return [{"id": m, "name": m, "owner": "nvidia"} for m in settings.nvidia_models]


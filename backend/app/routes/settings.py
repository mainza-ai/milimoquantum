"""Milimo Quantum — Settings Routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config import settings
from app.llm.ollama_client import ollama_client
from app.llm.cloud_provider import get_available_providers, set_provider, get_current_provider
from app.quantum.hal import detect_platform
from app.quantum import ibm_runtime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/")
async def get_settings():
    """Get current application settings."""
    platform = detect_platform()
    cloud = get_current_provider()
    ibm_status = ibm_runtime.get_status()
    return {
        "ollama_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.DEFAULT_MODEL,
        "default_shots": settings.DEFAULT_SHOTS,
        "cloud_provider": cloud,
        "ibm_quantum": ibm_status,
        "explain_level": settings.explain_level,
        "agent_models": settings.agent_models,
        "platform": {
            "os": platform.os_name,
            "arch": platform.arch,
            "torch_device": platform.torch_device,
            "aer_device": platform.aer_device,
            "llm_backend": platform.llm_backend,
            "gpu_available": platform.gpu_available,
            "gpu_name": platform.gpu_name,
        },
    }


@router.get("/models")
async def list_models():
    """List available Ollama models."""
    try:
        models = await ollama_client.list_models()
        return {"models": models, "current": settings.DEFAULT_MODEL}
    except Exception as e:
        logger.warning(f"Failed to list Ollama models: {e}")
        return {"models": [], "current": settings.DEFAULT_MODEL, "error": "Ollama not available"}


@router.get("/cloud-providers")
async def list_cloud_providers():
    """List available cloud AI providers."""
    return {"providers": get_available_providers()}


@router.put("/cloud-provider")
async def set_cloud_provider(data: dict):
    """Set the active cloud AI provider."""
    provider = data.get("provider", "ollama")
    model = data.get("model")
    result = set_provider(provider, model)
    return result


@router.put("/")
async def update_settings(data: dict):
    """Update runtime settings."""
    updated = {}
    if "ollama_model" in data:
        settings.DEFAULT_MODEL = data["ollama_model"]
        updated["ollama_model"] = settings.DEFAULT_MODEL
    if "default_shots" in data:
        shots = max(100, min(8192, int(data["default_shots"])))
        settings.DEFAULT_SHOTS = shots
        updated["default_shots"] = shots
    if "ollama_url" in data:
        settings.OLLAMA_BASE_URL = data["ollama_url"]
        updated["ollama_url"] = settings.OLLAMA_BASE_URL
    if "explain_level" in data:
        level = data["explain_level"]
        if level in ("beginner", "intermediate", "expert"):
            settings.explain_level = level
            updated["explain_level"] = level

    # Cloud AI API keys — stored as environment variables
    import os
    for key_name in ("anthropic_api_key", "openai_api_key", "gemini_api_key",
                      "cohere_api_key", "mistral_api_key", "deepseek_api_key"):
        if key_name in data and data[key_name]:
            env_map = {
                "anthropic_api_key": "ANTHROPIC_API_KEY",
                "openai_api_key": "OPENAI_API_KEY",
                "gemini_api_key": "GOOGLE_API_KEY",
                "cohere_api_key": "COHERE_API_KEY",
                "mistral_api_key": "MISTRAL_API_KEY",
                "deepseek_api_key": "DEEPSEEK_API_KEY",
            }
            env_var = env_map[key_name]
            os.environ[env_var] = data[key_name]
            updated[key_name] = "***configured***"

    return {"updated": updated, "status": "ok"}


@router.get("/agent-models")
async def get_agent_models():
    """Get per-agent model assignments."""
    return {"agent_models": settings.agent_models}


@router.put("/agent-models")
async def update_agent_models(data: dict):
    """Update per-agent model assignments.

    Body: { "agent_models": { "code": "codellama:latest", "research": "qwen2.5:latest" } }
    """
    models = data.get("agent_models", {})
    settings.agent_models = {k: v for k, v in models.items() if v}  # remove empty
    settings.save_agent_models()
    return {"agent_models": settings.agent_models, "status": "ok"}


@router.put("/hot-swap-model")
async def hot_swap_model(data: dict):
    """Switch the active Ollama model mid-conversation.

    Body: { "model": "qwen2.5:latest" }
    This immediately changes the default model for all subsequent requests.
    """
    model = data.get("model", "")
    if not model:
        return {"error": "No model specified"}

    settings.DEFAULT_MODEL = model
    return {"model": model, "status": "ok", "message": f"Switched to {model}"}


@router.get("/vision/models")
async def list_vision_models_endpoint():
    """List available vision-capable models from Ollama."""
    from app.llm.vision import list_vision_models
    models = await list_vision_models()
    return {"vision_models": models}


@router.post("/vision/analyze")
async def analyze_image_endpoint(data: dict):
    """Analyze an image using a vision model.

    Body: { "image_base64": str, "question": str, "model": str }
    """
    from app.llm.vision import analyze_image
    return await analyze_image(
        image_base64=data.get("image_base64"),
        image_path=data.get("image_path"),
        question=data.get("question", "Describe this quantum circuit diagram in detail."),
        model=data.get("model", "llava"),
    )

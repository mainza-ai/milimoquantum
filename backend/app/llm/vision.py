"""Milimo Quantum — Vision Model Support.

Analyze circuit diagrams and quantum computing images
using Ollama's multimodal vision models (LLaVA, etc.).
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Vision-capable models in Ollama
VISION_MODELS = [
    "llava",
    "llava:13b",
    "llava:34b",
    "llava-llama3",
    "llava-phi3",
    "bakllava",
    "moondream",
    "minicpm-v",
]


async def analyze_image(
    image_path: str | None = None,
    image_base64: str | None = None,
    question: str = "Describe this quantum circuit diagram in detail.",
    model: str = "llava",
) -> dict:
    """Analyze an image using a vision-capable Ollama model.

    Args:
        image_path: Path to an image file
        image_base64: Base64-encoded image data
        question: Question to ask about the image
        model: Vision model to use

    Returns:
        {response: str, model: str} or {error: str}
    """
    try:
        import httpx
        from app.config import settings

        # Get base64 data
        if image_path and not image_base64:
            path = Path(image_path)
            if not path.exists():
                return {"error": f"Image file not found: {image_path}"}
            image_base64 = base64.b64encode(path.read_bytes()).decode("ascii")

        if not image_base64:
            return {"error": "No image provided (use image_path or image_base64)"}

        # Call Ollama generate with image
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": question,
                    "images": [image_base64],
                    "stream": False,
                },
            )

            if response.status_code != 200:
                return {"error": f"Ollama returned {response.status_code}: {response.text[:200]}"}

            data = response.json()
            return {
                "response": data.get("response", ""),
                "model": model,
                "eval_count": data.get("eval_count", 0),
            }

    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        return {"error": str(e)}


async def list_vision_models() -> list[str]:
    """List available vision-capable models from Ollama."""
    try:
        import httpx
        from app.config import settings

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.ollama_url}/api/tags")
            if response.status_code != 200:
                return []

            models = response.json().get("models", [])
            available = []
            for m in models:
                name = m.get("name", "").split(":")[0]
                if name in [v.split(":")[0] for v in VISION_MODELS]:
                    available.append(m.get("name", ""))
            return available
    except Exception:
        return []

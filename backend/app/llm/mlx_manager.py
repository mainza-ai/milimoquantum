"""Milimo Quantum — MLX Model Manager.

Provides HuggingFace Hub integration to search, manage, and download native MLX models.
"""
from __future__ import annotations

import logging
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    from huggingface_hub import HfApi
    from huggingface_hub.utils import RepositoryNotFoundError
    # Required for progress hooking
    import huggingface_hub.utils._tqdm as hf_tqdm
    HF_AVAILABLE = True
    api = HfApi()
except ImportError:
    HF_AVAILABLE = False
    logger.warning("huggingface_hub not installed. MLX Model Manager disabled.")

class MlxManager:
    """Manages MLX model discovery and downloads from HuggingFace."""
    
    def __init__(self):
        self.default_author = "mlx-community"
        self.download_progress = {
            "model_id": None,
            "status": "idle",
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "progress_percent": 0
        }
        self._setup_tqdm_hook()

    def _setup_tqdm_hook(self):
        """Override HuggingFace's tqdm to capture progress globally."""
        if not HF_AVAILABLE:
            return

        original_tqdm = hf_tqdm.tqdm

        class ProgressTqdm(original_tqdm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Keep a reference to the manager to update it
                self.manager = mlx_manager

            def update(self, n=1):
                super().update(n)
                # kwargs may contain 'total' but self.total holds the max value
                if self.manager and getattr(self, "total", 0):
                    self.manager.download_progress["total_bytes"] = self.total
                    self.manager.download_progress["downloaded_bytes"] = self.n
                    if self.total > 0:
                        self.manager.download_progress["progress_percent"] = int(
                            (self.n / self.total) * 100
                        )

        # Patch huggingface_hub tqdm
        hf_tqdm.tqdm = ProgressTqdm
        
    def search_models(self, query: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """Search HuggingFace for MLX compatible models."""
        if not HF_AVAILABLE:
            return []
            
        try:
            # We specifically target mlx-community as they host the officially converted safetensors
            search_query = query if query else "Qwen"
            models = api.list_models(
                author=self.default_author,
                search=search_query,
                sort="downloads",
                direction=-1,
                limit=limit
            )
            
            results = []
            for model in models:
                size_mb = 0
                try:
                    # Fetch repo tree to calculate total model size
                    files = api.list_repo_tree(model.id)
                    total_bytes = sum(getattr(f, "size", 0) or 0 for f in files)
                    size_mb = int(total_bytes / (1024 * 1024))
                except Exception as e:
                    logger.debug(f"Could not fetch size for {model.id}: {e}")

                results.append({
                    "id": model.id,
                    "downloads": getattr(model, "downloads", 0),
                    "tags": getattr(model, "tags", []),
                    "created_at": getattr(model, "created_at", None),
                    "size_mb": size_mb,
                })
            return results
        except Exception as e:
            logger.error(f"HF Search Error: {e}")
            return []

    def get_local_models(self) -> List[str]:
        """Scan the local HuggingFace cache directory for downloaded models."""
        # HF stores models in ~/.cache/huggingface/hub/models--<author>--<repo>
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        if not os.path.exists(cache_dir):
            return []
            
        local_models = []
        try:
            for item in os.listdir(cache_dir):
                if item.startswith("models--"):
                    # Convert models--mlx-community--Qwen2.5 to mlx-community/Qwen2.5
                    parts = item.split("--")
                    if len(parts) >= 3:
                        author = parts[1]
                        repo = parts[2]
                        local_models.append(f"{author}/{repo}")
        except Exception as e:
            logger.error(f"Error scanning local HF cache: {e}")
            
        return local_models

# Singleton
mlx_manager = MlxManager()

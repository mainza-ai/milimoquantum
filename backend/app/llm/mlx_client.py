"""Milimo Quantum — MLX Inference Client.

Provides native Apple Silicon LLM inference using the mlx-lm library.
"""
from __future__ import annotations

import json
import logging
import asyncio
import concurrent.futures
from typing import AsyncGenerator

try:
    from huggingface_hub import hf_hub_download, snapshot_download
except ImportError:
    # Fallback if not available at top level
    pass

logger = logging.getLogger(__name__)
from app.llm.mlx_manager import mlx_manager

# Try to import mlx libraries
try:
    import mlx.core as mx
    MLX_CORE_AVAILABLE = True
except ImportError:
    MLX_CORE_AVAILABLE = False

try:
    import mlx_lm
    MLX_LM_AVAILABLE = True
except ImportError:
    MLX_LM_AVAILABLE = False

try:
    import mlx_vlm
    MLX_VLM_AVAILABLE = True
except ImportError:
    MLX_VLM_AVAILABLE = False

MLX_AVAILABLE = MLX_LM_AVAILABLE or MLX_VLM_AVAILABLE


class MlxClient:
    """Native Apple Silicon MLX Client for local LLMs."""

    def __init__(self):
        # self.model_name = "mlx-community/Qwen3.5-35B-A3B-bf16"
        self.model_name = "mlx-community/GLM-4.7-Flash-4bit"
        self.model = None
        self.tokenizer = None
        self.processor = None # For mlx-vlm
        self.model_config = None
        self.is_vlm = False
        self.is_loaded = False
        self.system_prompt = "You are Milimo Quantum, an advanced AI assistant."
        self.config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 32768
        }

    def load_model(self, model_name: str | None = None, allow_download: bool = True) -> bool:
        """Load an MLX model into unified memory.
        
        If allow_download is False (default), only attempt to load from local cache.
        If model not cached, returns False.
        """
        if not MLX_AVAILABLE:
            return False

        if model_name:
            self.model_name = model_name

        # Check if model is already cached locally
        local_models = mlx_manager.get_local_models()
        if self.model_name not in local_models:
            if not allow_download:
                logger.warning(f"Model {self.model_name} not cached and download disabled. Skipping.")
                return False
            # Download the model
            try:
                logger.info(f"Downloading MLX model: {self.model_name}")
                from huggingface_hub import snapshot_download
                # This triggers mlx_manager's patched tqdm
                snapshot_download(repo_id=self.model_name)
            except Exception as e:
                logger.error(f"Failed to download MLX model: {e}")
                return False

        try:
            logger.info(f"Loading MLX model into memory: {self.model_name}")
            
            # Detect if model is VLM (multimodal)
            import os
            
            config_path = hf_hub_download(repo_id=self.model_name, filename="config.json")
            with open(config_path, "r") as f:
                self.model_config = json.load(f)
            
            # Use mlx-vlm if it looks multimodal or is known VLM architecture
            self.is_vlm = "vision_config" in self.model_config or "visual" in str(self.model_config)
            
            if self.is_vlm and MLX_VLM_AVAILABLE:
                logger.info(f"Detected multimodal model, loading with mlx-vlm")
                self.model, self.processor = mlx_vlm.load(self.model_name)
            else:
                logger.info(f"Loading as standard LLM with mlx-lm")
                self.model, self.tokenizer = mlx_lm.load(self.model_name)
                
            self.is_loaded = True
            logger.info(f"MLX {'VLM' if self.is_vlm else 'LM'} loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load MLX model {self.model_name}: {e}")
            self.is_loaded = False
            return False

    def unload_model(self) -> bool:
        """Unload the active MLX model to free Apple Silicon unified memory."""
        if not self.is_loaded:
            return True

        try:
            logger.info(f"Unloading MLX model: {self.model_name}")
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            self.is_loaded = False
            
            # Force garbage collection to reclaim memory immediately
            import gc
            gc.collect()
            
            logger.info("MLX model unloaded successfully. Memory freed.")
            return True
        except Exception as e:
            logger.error(f"Failed to unload MLX model: {e}")
            return False

    def get_status(self) -> dict:
        """Get MLX client status."""
        return {
            "available": MLX_AVAILABLE,
            "loaded": self.is_loaded,
            "model": self.model_name if self.is_loaded else None,
            "config": self.config
        }

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model: str | None = None,
        image_path: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completions using MLX."""
        if not MLX_AVAILABLE:
            yield '{"error": "MLX not available"}'
            return

        if not self.is_loaded or (model and model != self.model_name):
            # Load the requested model (or default) if not already loaded
            success = self.load_model(model, allow_download=False)
            if not success:
                yield '{"error": "Failed to load MLX model"}'
                return

        prompt_messages = []
        if system_prompt:
            prompt_messages.append({"role": "system", "content": system_prompt})
        elif self.system_prompt:
             prompt_messages.append({"role": "system", "content": self.system_prompt})
             
        prompt_messages.extend(messages)

        # Apply chat template
        try:
             if self.is_vlm:
                 if not self.processor:
                     yield '{"error": "Processor not loaded"}'
                     return
                 # mlx-vlm.apply_chat_template(processor, config, prompt)
                 prompt = mlx_vlm.apply_chat_template(self.processor, self.model_config, prompt_messages, enable_thinking=False)
             else:
                 if not self.tokenizer:
                     yield '{"error": "Tokenizer not loaded"}'
                     return
                 prompt = self.tokenizer.apply_chat_template(
                     prompt_messages, tokenize=False, add_generation_prompt=True,
                     enable_thinking=False # Force model to skip thinking block
                 )
        except Exception as e:
             logger.error(f"MLX chat template error: {e}")
             yield '{"error": "Tokenization error"}'
             return

        # Simple non-blocking generation simulation using mlx-lm generator
        # mlx-lm text generation is synchronous, so we generate it and yield chunks
        # A true async implementation would require running generate in a threadpool
        import asyncio
        import concurrent.futures
        import json

        loop = asyncio.get_running_loop()
        
        def _generate_iter():
            gen_args = {
                "max_tokens": self.config.get("max_tokens", 32768),
                "temp": self.config.get("temperature", 0.7),
            }
            if self.is_vlm:
                # If image_path is provided, use it.
                return mlx_vlm.stream_generate(
                    self.model, self.processor, prompt, 
                    image=image_path, 
                    **gen_args
                )
            else:
                return mlx_lm.stream_generate(
                    self.model, self.tokenizer, prompt=prompt, 
                    **gen_args
                )

        try:
            # We must wrap the iterator for non-blocking stream
            it = _generate_iter()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                def _get_next():
                    return next(it, None)
                
                while True:
                    try:
                        # Pull next token
                        token_msg = await loop.run_in_executor(pool, _get_next)
                        if token_msg is None:
                            break
                        
                        # Extract the text
                        text = ""
                        if isinstance(token_msg, str):
                            text = token_msg
                        elif hasattr(token_msg, 'text'):
                            text = getattr(token_msg, 'text')
                        else:
                            text = str(token_msg)

                        if text:
                            yield json.dumps({"model": self.model_name, "message": {"content": text}, "done": False})
                    except StopIteration:
                        break
            
            yield json.dumps({"model": self.model_name, "message": {"content": ""}, "done": True})
            
        except Exception as e:
            logger.error(f"MLX generation error: {e}")
            yield json.dumps({"error": str(e), "done": True})

    async def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None, image_path: str | None = None) -> str:
         """Generate a complete response (non-streaming)."""
         if not MLX_AVAILABLE:
            return ""
            
         if not self.is_loaded or (model and model != self.model_name):
             success = self.load_model(model, allow_download=False)
             if not success:
                 return ""
                
         messages = []
         if system_prompt:
             messages.append({"role": "system", "content": system_prompt})
         messages.append({"role": "user", "content": prompt})

         try:
             if self.is_vlm:
                 # mlx-vlm.apply_chat_template(processor, config, prompt)
                 formatted_prompt = mlx_vlm.apply_chat_template(self.processor, self.model_config, messages)
             else:
                 formatted_prompt = self.tokenizer.apply_chat_template(
                     messages, tokenize=False, add_generation_prompt=True,
                     enable_thinking=False # Force model to skip thinking block
                 )
         except Exception:
             formatted_prompt = prompt
             
         import asyncio
         import concurrent.futures
         loop = asyncio.get_running_loop()
         
         def _generate():
             gen_args = {
                 "max_tokens": self.config.get("max_tokens", 32768),
                 "temp": self.config.get("temperature", 0.7),
             }
             if self.is_vlm:
                 return mlx_vlm.generate(
                     self.model, self.processor, prompt=formatted_prompt, 
                     image=image_path, 
                     **gen_args
                 )
             else:
                 return mlx_lm.generate(
                     self.model, self.tokenizer, prompt=formatted_prompt, 
                     **gen_args
                 )
             
         try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, _generate)
            return response
         except Exception as e:
            logger.error(f"MLX generation error: {e}")
            return ""


# Singleton
mlx_client = MlxClient()

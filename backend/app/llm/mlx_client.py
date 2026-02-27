"""Milimo Quantum — MLX Inference Client.

Provides native Apple Silicon LLM inference using the mlx-lm library.
"""
from __future__ import annotations

import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Try to import mlx-lm, gracefully degrade if unavailable
try:
    import mlx.core as mx
    from mlx_lm import load, generate
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    logger.debug("mlx-lm not installed, MLX client disabled.")


class MlxClient:
    """Native Apple Silicon MLX Client for local LLMs."""

    def __init__(self):
        self.model_name = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.system_prompt = "You are Milimo Quantum, an advanced AI assistant."

    def load_model(self, model_name: str | None = None) -> bool:
        """Load an MLX model into unified memory."""
        if not MLX_AVAILABLE:
            return False

        if model_name:
            self.model_name = model_name

        try:
            logger.info(f"Loading MLX model: {self.model_name}")
            self.model, self.tokenizer = load(self.model_name)
            self.is_loaded = True
            logger.info("MLX model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load MLX model: {e}")
            self.is_loaded = False
            return False

    def get_status(self) -> dict:
        """Get MLX client status."""
        return {
            "available": MLX_AVAILABLE,
            "loaded": self.is_loaded,
            "model": self.model_name if self.is_loaded else None
        }

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completions using MLX."""
        if not MLX_AVAILABLE:
            yield '{"error": "MLX not available"}'
            return

        if not self.is_loaded or (model and model != self.model_name):
            # Load the requested model (or default) if not already loaded
            success = self.load_model(model)
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
             prompt = self.tokenizer.apply_chat_template(
                 prompt_messages, tokenize=False, add_generation_prompt=True
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

        loop = asyncio.get_running_loop()
        
        def _generate():
            # In MLX, generate returns the full string. For streaming, we'd normally
            # use stream_generate, but for simplicity we'll just yield the full block
            # or fake streams here if `stream_generate` isn't accessible.
            # Using generate with max_tokens
            return generate(self.model, self.tokenizer, prompt=prompt, max_tokens=1024, verbose=False)

        try:
            # Run the heavy generation in a thread
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, _generate)
            
            # Fake streaming the results back to the client
            chunk_size = 10
            for i in range(0, len(response), chunk_size):
                 chunk = response[i:i+chunk_size]
                 yield json.dumps({"model": self.model_name, "message": {"content": chunk}, "done": False})
                 await asyncio.sleep(0.01)

            yield json.dumps({"model": self.model_name, "message": {"content": ""}, "done": True})
            
        except Exception as e:
             logger.error(f"MLX generation error: {e}")
             yield '{"error": "Generation error"}'

    async def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None) -> str:
         """Generate a complete response (non-streaming)."""
         if not MLX_AVAILABLE:
            return ""
            
         if not self.is_loaded or (model and model != self.model_name):
            success = self.load_model(model)
            if not success:
                return ""
                
         messages = []
         if system_prompt:
             messages.append({"role": "system", "content": system_prompt})
         messages.append({"role": "user", "content": prompt})

         try:
             formatted_prompt = self.tokenizer.apply_chat_template(
                 messages, tokenize=False, add_generation_prompt=True
             )
         except Exception:
             formatted_prompt = prompt
             
         import asyncio
         import concurrent.futures
         loop = asyncio.get_running_loop()
         
         def _generate():
             return generate(self.model, self.tokenizer, prompt=formatted_prompt, max_tokens=2048, verbose=False)
             
         try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, _generate)
            return response
         except Exception as e:
            logger.error(f"MLX generation error: {e}")
            return ""


# Singleton
mlx_client = MlxClient()

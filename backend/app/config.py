"""Milimo Quantum — Application Configuration."""
import json
import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


@dataclass
class Settings:
    """Application settings with sensible defaults."""
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Ollama
    ollama_base_url: str = field(
        default_factory=lambda: os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    )
    ollama_model: str = ""  # Auto-detected from Ollama at startup

    # Cloud LLM Models (Configurable via ENV)
    anthropic_models: list[str] = field(
        default_factory=lambda: os.getenv("ANTHROPIC_MODELS", "claude-sonnet-4-20250514,claude-opus-4-20250514,claude-3-5-haiku-20241022").split(",")
    )
    openai_models: list[str] = field(
        default_factory=lambda: os.getenv("OPENAI_MODELS", "gpt-4o,gpt-4o-mini,o1,o3-mini").split(",")
    )
    gemini_models: list[str] = field(
        default_factory=lambda: os.getenv("GEMINI_MODELS", "gemini-2.0-flash,gemini-1.5-pro").split(",")
    )
    cohere_models: list[str] = field(
        default_factory=lambda: os.getenv("COHERE_MODELS", "command-r-plus,command-r,command-light").split(",")
    )
    mistral_models: list[str] = field(
        default_factory=lambda: os.getenv("MISTRAL_MODELS", "mistral-large-latest,mistral-medium-latest,codestral-latest").split(",")
    )
    deepseek_models: list[str] = field(
        default_factory=lambda: os.getenv("DEEPSEEK_MODELS", "deepseek-chat,deepseek-coder,deepseek-reasoner").split(",")
    )
    openrouter_models: list[str] = field(
        default_factory=lambda: os.getenv("OPENROUTER_MODELS", "openai/gpt-4o,anthropic/claude-sonnet-4,google/gemini-2.5-pro,meta-llama/llama-4-maverick").split(",")
    )
    nvidia_models: list[str] = field(
        default_factory=lambda: os.getenv("NVIDIA_MODELS", "meta/llama-3.1-405b-instruct,meta/llama-3.3-70b-instruct,mistralai/mistral-large-2,instruct/nemotron-nano-12b-v2-vl").split(",")
    )

    # Quantum
    default_shots: int = 1024
    max_qubits_local: int = 28

    # Platform detection
    platform_os: str = field(default_factory=lambda: platform.system())
    platform_arch: str = field(default_factory=lambda: platform.machine())

    # Project storage
    data_dir: str = field(
        default_factory=lambda: os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data"
        )
    )

    # Explain level: beginner, intermediate, expert
    explain_level: str = "intermediate"

    # Per-agent model overrides: {agent_type: model_name}
    agent_models: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        os.makedirs(self.data_dir, exist_ok=True)

    # Uppercase property aliases for settings route
    @property
    def OLLAMA_BASE_URL(self) -> str:
        return self.ollama_base_url

    @OLLAMA_BASE_URL.setter
    def OLLAMA_BASE_URL(self, val: str) -> None:
        self.ollama_base_url = val

    @property
    def DEFAULT_MODEL(self) -> str:
        return self.ollama_model

    @DEFAULT_MODEL.setter
    def DEFAULT_MODEL(self, val: str) -> None:
        self.ollama_model = val

    @property
    def DEFAULT_SHOTS(self) -> int:
        return self.default_shots

    @DEFAULT_SHOTS.setter
    def DEFAULT_SHOTS(self, val: int) -> None:
        self.default_shots = val

    # ── Agent model persistence ────────────────────────
    _AGENT_MODELS_FILE = Path.home() / ".milimoquantum" / "agent_models.json"

    def load_agent_models(self) -> Dict[str, str]:
        """Load per-agent model assignments from disk."""
        if self._AGENT_MODELS_FILE.exists():
            try:
                self.agent_models = json.loads(
                    self._AGENT_MODELS_FILE.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                pass
        return self.agent_models

    def save_agent_models(self) -> None:
        """Save per-agent model assignments to disk."""
        self._AGENT_MODELS_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._AGENT_MODELS_FILE.write_text(
            json.dumps(self.agent_models, indent=2), encoding="utf-8"
        )


settings = Settings()
settings.load_agent_models()

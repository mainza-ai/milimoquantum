"""Milimo Quantum — Application Configuration."""
import os
import platform
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings with sensible defaults."""
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

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

    def __post_init__(self):
        os.makedirs(self.data_dir, exist_ok=True)


settings = Settings()

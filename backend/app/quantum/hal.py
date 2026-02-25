"""Milimo Quantum — Hardware Abstraction Layer (HAL).

Detects platform capabilities and selects optimal quantum simulation
configuration per the Cross-Platform Guide.
"""
from __future__ import annotations

import logging
import platform
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PlatformConfig:
    """Platform-specific configuration for quantum execution."""
    os_name: str
    arch: str
    torch_device: str
    aer_device: str
    llm_backend: str
    gpu_available: bool
    gpu_name: str | None = None

    def simulation_method(self, num_qubits: int, is_clifford: bool = False) -> str:
        """Select optimal Aer simulation method based on qubit count."""
        if is_clifford:
            return "stabilizer"  # Use Stim-like path
        if num_qubits <= 20:
            return "statevector"
        if num_qubits <= 28:
            return "statevector"  # Still fine, might be slower
        if num_qubits <= 32:
            return "matrix_product_state"  # MPS tensor network
        return "statevector"  # Will be slow, warn user

    def aer_backend_options(self, num_qubits: int) -> dict:
        """Get Aer backend options for given qubit count."""
        method = self.simulation_method(num_qubits)
        opts: dict = {"method": method}
        if self.aer_device == "GPU":
            opts["device"] = "GPU"
        return opts


def detect_platform() -> PlatformConfig:
    """Detect current platform and capabilities."""
    os_name = platform.system()
    arch = platform.machine()

    # Default: CPU fallback
    torch_device = "cpu"
    aer_device = "CPU"
    llm_backend = "ollama"
    gpu_available = False
    gpu_name = None

    # macOS Apple Silicon
    if os_name == "Darwin" and arch == "arm64":
        torch_device = "mps"
        aer_device = "CPU"  # Aer has no MPS support
        llm_backend = "mlx"
        try:
            import torch
            if torch.backends.mps.is_available():
                gpu_available = True
                gpu_name = "Apple Silicon (MPS)"
        except ImportError:
            gpu_available = True  # Assume available on ARM Mac
            gpu_name = "Apple Silicon (MPS) — PyTorch not installed"
        logger.info("Detected macOS Apple Silicon — MPS for QML, CPU for Aer, MLX for LLM")

    # CUDA (Windows / Linux)
    elif os_name in ("Windows", "Linux"):
        try:
            import torch
            if torch.cuda.is_available():
                torch_device = "cuda"
                aer_device = "GPU"
                gpu_available = True
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"Detected CUDA GPU: {gpu_name}")
        except ImportError:
            pass
        llm_backend = "ollama"

    config = PlatformConfig(
        os_name=os_name,
        arch=arch,
        torch_device=torch_device,
        aer_device=aer_device,
        llm_backend=llm_backend,
        gpu_available=gpu_available,
        gpu_name=gpu_name,
    )
    logger.info(f"HAL config: {config}")
    return config


# Singleton
hal_config = detect_platform()

"""Milimo Quantum — Hardware Abstraction Layer (HAL).

Detects platform capabilities and selects optimal quantum simulation
configuration. Supports SIM_ONLY_MODE for local-only execution.
"""
from __future__ import annotations

import logging
import os
import platform
import psutil
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SIM_ONLY_MODE = os.getenv("SIM_ONLY_MODE", "true").lower() == "true"
IS_APPLE_SILICON = platform.machine() == "arm64" and platform.system() == "Darwin"


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
            return "stabilizer"
        if num_qubits <= 24:
            return "statevector"
        if num_qubits <= 40:
            return "matrix_product_state"
        return "matrix_product_state"

    def aer_backend_options(self, num_qubits: int) -> dict:
        """Get Aer backend options for given qubit count."""
        method = self.simulation_method(num_qubits)
        opts: dict = {"method": method}
        if self.aer_device == "GPU":
            opts["device"] = "GPU"
        return opts


def get_memory_gb() -> float:
    """Get available system memory in GB."""
    return psutil.virtual_memory().total / (1024 ** 3)


def select_aer_backend(num_qubits: int):
    """
    Select the best local Aer backend for the given qubit count.
    
    Statevector: exact, exponential memory (2^n complex128 amplitudes).
    - 24 qubits = 256 MB
    - 30 qubits = 16 GB (borderline)
    
    MPS: tensor-network, polynomial memory for low-entanglement circuits.
    - Handles 50-100 qubits for VQE ansatze (moderate entanglement).
    """
    try:
        from qiskit_aer import AerSimulator
    except ImportError:
        logger.error("qiskit_aer not installed")
        return None
    
    mem_gb = get_memory_gb()
    
    max_sv_qubits = min(int((mem_gb - 4) * 1024**3 / 16).bit_length() - 1, 28)
    max_sv_qubits = max(20, max_sv_qubits)
    
    if num_qubits <= max_sv_qubits:
        logger.debug(f"Selected statevector for {num_qubits} qubits")
        return AerSimulator(method='statevector')
    else:
        logger.debug(f"Selected MPS for {num_qubits} qubits")
        return AerSimulator(
            method='matrix_product_state',
            matrix_product_state_max_bond_dimension=128,
            matrix_product_state_truncation_threshold=1e-10,
        )


def select_backend(num_qubits: int):
    """
    Main backend selector. Returns local Aer backend in SIM_ONLY_MODE.
    Falls through to cloud routing only when SIM_ONLY_MODE=False.
    """
    if SIM_ONLY_MODE:
        return select_aer_backend(num_qubits)
    
    if num_qubits > 30:
        ibm_token = os.getenv("IBM_QUANTUM_TOKEN")
        if ibm_token:
            return _get_ibm_backend(num_qubits)
        else:
            logger.warning(
                f"IBM_QUANTUM_TOKEN not set for {num_qubits}-qubit circuit. "
                f"Falling back to local MPS simulation."
            )
    
    return select_aer_backend(num_qubits)


def _get_ibm_backend(num_qubits: int):
    """Lazy IBM cloud connection — only called when credentials exist."""
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        service = QiskitRuntimeService(token=os.getenv("IBM_QUANTUM_TOKEN"))
        return service.least_busy(
            operational=True,
            min_num_qubits=num_qubits,
            simulator=False
        )
    except Exception as e:
        logger.error(f"Failed to get IBM backend: {e}")
        return select_aer_backend(num_qubits)


def detect_platform() -> PlatformConfig:
    """Detect current platform and capabilities."""
    os_name = platform.system()
    arch = platform.machine()
    
    torch_device = "cpu"
    aer_device = "CPU"
    llm_backend = "ollama"
    gpu_available = False
    gpu_name = None
    
    if os_name == "Darwin" and arch == "arm64":
        torch_device = "mps"
        aer_device = "CPU"
        llm_backend = "mlx"
        try:
            import torch
            if torch.backends.mps.is_available():
                gpu_available = True
                gpu_name = "Apple Silicon (MPS)"
        except ImportError:
            gpu_available = True
            gpu_name = "Apple Silicon (MPS) — PyTorch not installed"
        logger.info("Detected macOS Apple Silicon — MPS for QML, CPU for Aer, MLX for LLM")
    
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
    logger.info(f"HAL config: {config}, SIM_ONLY_MODE={SIM_ONLY_MODE}")
    return config


hal_config = detect_platform()

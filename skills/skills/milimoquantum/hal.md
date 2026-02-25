---
description: Hardware Abstraction Layer — cross-platform quantum execution with device detection and qubit-count routing
---

# HAL Skill

## Platform Detection Logic

```python
# Priority order:
# 1. macOS ARM64 + MPS → torch_device=mps, aer_device=CPU, llm_backend=MLX
# 2. CUDA available     → torch_device=cuda, aer_device=GPU, llm_backend=ollama
# 3. CPU fallback       → torch_device=cpu, all features work (slower)
```

## macOS Apple Silicon Path
- **PyTorch**: MPS device for QNN/QSVM training (TorchConnector → mps)
- **Qiskit Aer**: CPU simulation (Aer doesn't support MPS) + Accelerate Framework + AMX coprocessor
- **LLM**: Apple MLX primary (50+ tok/s 8B model), Ollama fallback
- **Memory advantage**: 512GB unified RAM > GPU VRAM for 33-35 qubit circuits

## Windows/Linux CUDA Path
- **PyTorch**: CUDA device, TF32 on Ampere+
- **Qiskit Aer**: GPU simulation with cuStateVec (14× CPU speedup)
- **LLM**: Ollama + CUDA GPU-accelerated
- **CUDA-Q**: NVIDIA HPC simulation available

## Qubit-Count Routing

| Qubits | Method | Performance |
|--------|--------|-------------|
| ≤ 20 | `statevector` | < 0.1s all platforms |
| 21–28 | `statevector` | Mac: 0.5-5s, GPU: < 0.5s |
| 29–32 | `mps` (Matrix Product State) or GPU statevector | Platform-dependent |
| 33–35 | Large Mac wins (512GB RAM > GPU VRAM) | Memory-bound |
| 50+ | IBM Quantum cloud / D-Wave | Cloud required |
| Clifford-only | Stim | < 0.001s any size |

## Implementation Pattern

```python
# backend/app/quantum/hal.py
class HALConfig:
    os_name: str          # "Darwin" | "Linux" | "Windows"
    arch: str             # "arm64" | "x86_64"
    torch_device: str     # "mps" | "cuda" | "cpu"
    aer_device: str       # "CPU" | "GPU"
    llm_backend: str      # "mlx" | "ollama"
    gpu_available: bool
    gpu_name: str | None

    def get_aer_method(self, num_qubits: int) -> str:
        if num_qubits <= 20: return "statevector"
        if num_qubits <= 28: return "statevector"
        if num_qubits <= 32: return "matrix_product_state"
        return "automatic"
```

## IMPORTANT Rules
- **Never assume GPU on macOS** — Aer runs on CPU even with MPS available
- **Always detect at startup** — platform config is immutable per session
- **Qubit routing is critical** — wrong method = crash or 100× slowdown
- **MLX > Ollama on macOS** — prefer MLX for local LLM when available

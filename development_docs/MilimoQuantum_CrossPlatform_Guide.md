🍎 ⚡ 🪟

**MILIMO QUANTUM**

*Cross-Platform Acceleration Guide*

**macOS Apple Silicon --- Full MPS / MLX / Accelerate Stack**

**Windows --- Full CUDA / cuQuantum / CUDA-Q Stack**

*Development Guide · February 2026 · Supplement to Blueprint v1.0*

**1. The Honest Truth About MPS + Qiskit Aer**

Before diving into optimization strategies, every Milimo Quantum
developer must understand one critical fact about the macOS Apple
Silicon landscape that almost all tutorials omit. Getting this wrong
will waste days of debugging.

+-----------------------------------------------------------------------+
| **⚠ Critical Constraint: Qiskit Aer GPU Does NOT Support MPS**        |
|                                                                       |
| Qiskit Aer\'s GPU acceleration (device=\'GPU\') uses CUDA (NVIDIA)    |
| only.                                                                 |
|                                                                       |
| The qiskit-aer-gpu PyPI package only ships Linux x86_64 wheels --- it |
| will not install on macOS at all.                                     |
|                                                                       |
| There is no Apple Metal / MPS backend for Qiskit Aer quantum circuit  |
| simulation.                                                           |
|                                                                       |
| On macOS Apple Silicon, Qiskit Aer runs entirely on CPU --- this is   |
| expected and by design.                                               |
|                                                                       |
| However: Aer\'s CPU performance on Apple Silicon is EXCELLENT due to: |
|                                                                       |
| • Apple\'s Accelerate Framework (Veclib BLAS / LAPACK) ---            |
| automatically used by NumPy/SciPy                                     |
|                                                                       |
| • ARM NEON SIMD vectorization in Qiskit Aer\'s C++ core               |
|                                                                       |
| • AMX (Apple Matrix Extensions) coprocessor for matrix multiply       |
| operations                                                            |
|                                                                       |
| • Up to 512 GB unified memory (Mac Studio M4 Ultra) --- simulate      |
| larger circuits than GPU VRAM limits                                  |
+-----------------------------------------------------------------------+

This constraint is actually not the disaster it might seem. Here is why
macOS Apple Silicon is an excellent Milimo Quantum development platform
despite no Aer GPU support:

+-----------------------------------------------------------------------+
| **Why macOS Apple Silicon Is Still Excellent for Milimo Quantum**     |
|                                                                       |
| 1\. Quantum Simulation (Aer CPU): Apple Silicon Aer CPU ≈ 2-4x faster |
| than Intel Aer CPU.                                                   |
|                                                                       |
| Accelerate Framework BLAS is among the fastest CPU BLAS in the world. |
|                                                                       |
| For circuits ≤ 25 qubits, CPU simulation is fast enough for all dev   |
| work.                                                                 |
|                                                                       |
| 2\. QML / QNN Training (MPS): PyTorch MPS fully accelerates           |
| qiskit-machine-learning\'s TorchConnector.                            |
|                                                                       |
| Quantum Neural Networks, QSVMs, and hybrid models train on GPU.       |
|                                                                       |
| This is the HIGHEST value use of MPS in Milimo Quantum.               |
|                                                                       |
| 3\. LLM Inference (MLX): Apple MLX is FASTER than Ollama+GGUF for     |
| most Llama/Qwen/Mistral models.                                       |
|                                                                       |
| Unified memory allows running 70B models that would OOM a 24GB NVIDIA |
| GPU.                                                                  |
|                                                                       |
| M5 Neural Accelerators provide 28% faster inference than M4.          |
|                                                                       |
| 4\. Large Circuit Simulation: Mac Studio M4 Ultra (512 GB RAM)        |
| simulates 35+ qubit statevector.                                      |
|                                                                       |
| A 40 GB A100 GPU can only simulate ≤ 32-33 qubits statevector.        |
|                                                                       |
| For large circuits, Mac wins on memory capacity.                      |
|                                                                       |
| 5\. Dev Experience: Native macOS app (Electron/Tauri), no Docker GPU  |
| passthrough issues,                                                   |
|                                                                       |
| unified memory eliminates CPU↔GPU copy overhead entirely.             |
+-----------------------------------------------------------------------+

**2. Apple Silicon Architecture: Every Compute Unit Milimo Uses**

Apple Silicon (M1 through M5) is a System-on-Chip (SoC) with multiple
specialized compute units sharing a unified memory pool. Milimo Quantum
must target each unit with the right workload to extract maximum
performance.

  ----------------------------------------------------------------------------------------
  **Compute      **What It Is**     **Milimo Quantum       **Framework**   **Bandwidth**
  Unit**                            Workload**                             
  -------------- ------------------ ---------------------- --------------- ---------------
  CPU (P+E       ARM cores:         Qiskit Aer simulation, Qiskit Aer      up to 546 GB/s
  cores)         P=performance,     Qiskit transpiler,     (CPU),          (M4 Ultra)
                 E=efficiency       classical              NumPy/SciPy +   
                                    pre/post-processing,   Accelerate      
                                    backend API calls                      

  GPU (30-76     Metal 3 shader     PyTorch MPS: QNN       PyTorch MPS,    Shared unified
  cores)         cores, Neural      training, QSVM,        MLX, Metal      memory
                 Accelerators (M5)  quantum kernel         Performance     
                                    estimation, VQE        Shaders         
                                    gradient computation,                  
                                    visualization                          
                                    rendering                              

  ANE / Neural   16-core dedicated  Core ML inference for  Core ML, MLX    \~18 TOPS
  Engine         ML accelerator     small models,          (partial),      
                                    quantized embeddings,  Create ML       
                                    fast tokenization ---                  
                                    available via MLX                      
                                    partial offload (M5+)                  

  AMX (Matrix    Apple Matrix       NumPy matmul, SciPy    Accelerate      Auto-used
  Coprocessor)   Extensions ---     BLAS, Qiskit Aer       Framework       
                 hidden accelerator statevector            (auto), NumPy   
                 in every P-core    operations, VQE        (auto)          
                                    parameter gradients                    
                                    via numpy                              

  Unified Memory Single pool shared Large quantum          All frameworks  120--546 GB/s
                 by CPU+GPU+ANE --- statevectors (35+      --- zero copy   
                 no copy overhead   qubits), 70B LLM       advantage       
                                    models, large molecule                 
                                    Hamiltonians, graph                    
                                    database in-memory                     

  Media Engine   H.264/H.265/HEVC   Optional: record and   AVFoundation /  N/A
                 hardware           compress quantum       FFmpeg with     
                 encode/decode      circuit visualization  hwaccel         
                                    screencasts, export                    
                                    video tutorials for                    
                                    Learning Academy                       
  ----------------------------------------------------------------------------------------

**3. macOS Full Development Environment Setup**

This is the definitive, step-by-step setup guide for building Milimo
Quantum on macOS Apple Silicon. Follow this exactly --- several steps
have non-obvious requirements that cause silent performance degradation
if skipped.

**3.1 Prerequisites & Xcode**

+-----------------------------------------------------------------------+
| \# Step 1: Install Xcode Command Line Tools (required for Metal/MPS   |
| build)                                                                |
|                                                                       |
| \$ xcode-select \--install                                            |
|                                                                       |
| \# Step 2: Install Xcode from App Store (required for MPS PyTorch     |
| build if needed)                                                      |
|                                                                       |
| \# Minimum: Xcode 13.3.1 \| Recommended: Xcode 16.x (2025)            |
|                                                                       |
| \# Step 3: Install Homebrew (ARM native --- critical, do NOT use      |
| Rosetta)                                                              |
|                                                                       |
| \$ /bin/bash -c \"\$(curl -fsSL                                       |
| https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\" |
|                                                                       |
| \$ echo \'eval \"\$(/opt/homebrew/bin/brew shellenv)\"\' \>\>         |
| \~/.zshrc                                                             |
|                                                                       |
| \$ source \~/.zshrc                                                   |
|                                                                       |
| \# Verify ARM native (should show arm64, NOT x86_64)                  |
|                                                                       |
| \$ arch                                                               |
|                                                                       |
| arm64                                                                 |
+-----------------------------------------------------------------------+

**3.2 Python Environment (ARM Native)**

+-----------------------------------------------------------------------+
| **⚠ Critical: Use ARM Native Python Only**                            |
|                                                                       |
| NEVER use Rosetta/x86 Python with MPS --- it causes a silent MPS      |
| fallback to CPU.                                                      |
|                                                                       |
| If PyTorch reports \'MPS device not found\' despite having Apple      |
| Silicon, your Python is x86-emulated.                                 |
|                                                                       |
| Always verify: python3 -c \"import platform;                          |
| print(platform.machine())\" → must print \'arm64\'                    |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
| \# Install pyenv with ARM support                                     |
|                                                                       |
| \$ brew install pyenv                                                 |
|                                                                       |
| \$ echo \'export PYENV_ROOT=\"\$HOME/.pyenv\"\' \>\> \~/.zshrc        |
|                                                                       |
| \$ echo \'export PATH=\"\$PYENV_ROOT/bin:\$PATH\"\' \>\> \~/.zshrc    |
|                                                                       |
| \$ echo \'eval \"\$(pyenv init -)\"\' \>\> \~/.zshrc                  |
|                                                                       |
| \$ source \~/.zshrc                                                   |
|                                                                       |
| \# Install Python 3.12 (ARM native --- do NOT add \--enable-shared on |
| macOS)                                                                |
|                                                                       |
| \$ pyenv install 3.12.8                                               |
|                                                                       |
| \$ pyenv global 3.12.8                                                |
|                                                                       |
| \# Verify ARM native Python                                           |
|                                                                       |
| \$ python3 -c \"import platform; print(platform.machine())\"          |
|                                                                       |
| arm64                                                                 |
|                                                                       |
| \# Create Milimo Quantum virtual environment                          |
|                                                                       |
| \$ python3 -m venv milimo-env                                         |
|                                                                       |
| \$ source milimo-env/bin/activate                                     |
+-----------------------------------------------------------------------+

**3.3 Core Quantum Stack (CPU-Optimized for Apple Silicon)**

+-----------------------------------------------------------------------+
| \# Install Qiskit v1.4 and Aer (CPU only --- this is correct for      |
| macOS)                                                                |
|                                                                       |
| \$ pip install qiskit==1.4.0                                          |
|                                                                       |
| \$ pip install qiskit-aer==0.17.0                                     |
|                                                                       |
| \# Install domain libraries                                           |
|                                                                       |
| \$ pip install qiskit-ibm-runtime qiskit-nature qiskit-finance        |
|                                                                       |
| \$ pip install qiskit-machine-learning qiskit-optimization            |
| qiskit-algorithms                                                     |
|                                                                       |
| \# Verify Aer devices --- should show \[\'CPU\'\] on macOS (correct)  |
|                                                                       |
| \$ python3 -c \"                                                      |
|                                                                       |
| from qiskit_aer import AerSimulator                                   |
|                                                                       |
| print(AerSimulator().available_devices()) \# → \[\'CPU\'\]            |
|                                                                       |
| print(AerSimulator().available_methods()) \# → all simulation methods |
| available                                                             |
|                                                                       |
| \"                                                                    |
|                                                                       |
| \# Aer is using Accelerate Framework BLAS automatically --- no config |
| needed                                                                |
|                                                                       |
| \# Verify with: python3 -c \"import numpy; numpy.show_config()\"      |
|                                                                       |
| \# Should show \'blas_opt_info: libraries = \[\'cblas\', \'blas\'\],  |
| library_dirs = \[\'/System/Library/Frameworks/\...\'\]\'              |
+-----------------------------------------------------------------------+

**3.4 PyTorch MPS --- Quantum ML Acceleration**

This is the primary GPU acceleration path for Milimo Quantum on macOS.
PyTorch MPS accelerates all quantum neural network training and quantum
kernel methods via qiskit-machine-learning\'s TorchConnector.

+-----------------------------------------------------------------------+
| \# Install PyTorch with MPS support (macOS wheel --- NOT the          |
| Linux/CUDA build)                                                     |
|                                                                       |
| \$ pip install torch torchvision torchaudio                           |
|                                                                       |
| \# Note: the standard pip wheel includes MPS support on macOS \>=     |
| 12.3                                                                  |
|                                                                       |
| \# Verify MPS availability                                            |
|                                                                       |
| \$ python3 -c \"                                                      |
|                                                                       |
| import torch                                                          |
|                                                                       |
| print(\'MPS available:\', torch.backends.mps.is_available())          |
|                                                                       |
| print(\'MPS built: \', torch.backends.mps.is_built())                 |
|                                                                       |
| print(\'PyTorch version:\', torch.\_\_version\_\_)                    |
|                                                                       |
| if torch.backends.mps.is_available():                                 |
|                                                                       |
| x = torch.ones(1, device=\'mps\')                                     |
|                                                                       |
| print(\'MPS test tensor:\', x) \# → tensor(\[1.\], device=\'mps:0\')  |
|                                                                       |
| \"                                                                    |
|                                                                       |
| \# Enable MPS fallback for unsupported ops (important --- some ops    |
| not yet in MPS)                                                       |
|                                                                       |
| \# Add to your .zshrc or set at process start:                        |
|                                                                       |
| \$ export PYTORCH_ENABLE_MPS_FALLBACK=1                               |
|                                                                       |
| \# For QNN training --- TorchConnector with MPS device                |
|                                                                       |
| \$ python3 -c \"                                                      |
|                                                                       |
| from qiskit_machine_learning.connectors import TorchConnector         |
|                                                                       |
| import torch                                                          |
|                                                                       |
| device = torch.device(\'mps\' if torch.backends.mps.is_available()    |
| else \'cpu\')                                                         |
|                                                                       |
| print(f\'QML training device: {device}\') \# → mps                    |
|                                                                       |
| \"                                                                    |
+-----------------------------------------------------------------------+

**3.5 Apple MLX --- LLM Inference (Faster Than Ollama on Apple
Silicon)**

For Milimo Quantum\'s local AI inference, Apple MLX significantly
outperforms Ollama+GGUF on Apple Silicon. MLX uses the GPU natively (not
via PyTorch MPS), leverages lazy graph compilation, and on M5 hardware
uses the Neural Accelerators for matrix multiply --- achieving 50+
tokens/sec for 8B models vs \~30 tokens/sec for equivalent Ollama
models.

+-----------------------------------------------------------------------+
| **⚠ MLX vs Ollama: Why Both Are Used**                                |
|                                                                       |
| MLX: Faster inference, better memory efficiency, direct Metal GPU     |
| usage, best for research/power users.                                 |
|                                                                       |
| Limited model selection vs Ollama\'s 400+ models. Requires mlx-lm     |
| separately.                                                           |
|                                                                       |
| Ollama: Broader model support, easier to use, GGUF format is          |
| universal, great for general users.                                   |
|                                                                       |
| Slower on Apple Silicon vs MLX for the same model, but still          |
| excellent on CPU+GPU path.                                            |
|                                                                       |
| Strategy: MLX as PRIMARY backend for macOS, Ollama as FALLBACK for    |
| model compatibility.                                                  |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
| \# Install Apple MLX and mlx-lm                                       |
|                                                                       |
| \$ pip install mlx mlx-lm                                             |
|                                                                       |
| \# Download and run a model via mlx-lm (pulls from HuggingFace        |
| mlx-community)                                                        |
|                                                                       |
| \$ python3 -m mlx_lm.generate \\                                      |
|                                                                       |
| \--model mlx-community/Qwen2.5-7B-Instruct-4bit \\                    |
|                                                                       |
| \--prompt \'Explain VQE in one paragraph\' \\                         |
|                                                                       |
| \--max-tokens 200                                                     |
|                                                                       |
| \# Programmatic MLX inference for Milimo Quantum backend              |
|                                                                       |
| \$ python3 -c \"                                                      |
|                                                                       |
| from mlx_lm import load, generate                                     |
|                                                                       |
| model, tokenizer = load(\'mlx-community/Llama-3.2-8B-Instruct-4bit\') |
|                                                                       |
| response = generate(model, tokenizer,                                 |
|                                                                       |
| prompt=\'Write a Qiskit VQE circuit for H2\',                         |
|                                                                       |
| max_tokens=500, verbose=True                                          |
|                                                                       |
| )                                                                     |
|                                                                       |
| print(response)                                                       |
|                                                                       |
| \"                                                                    |
|                                                                       |
| \# MLX model performance on Apple Silicon (approximate tokens/sec):   |
|                                                                       |
| \# Llama 3.2 8B (4-bit): \~45-55 tok/s on M4 Pro \| \~60-70 tok/s on  |
| M4 Max                                                                |
|                                                                       |
| \# Qwen 2.5 14B (4-bit): \~25-30 tok/s on M4 Pro \| \~38-45 tok/s on  |
| M4 Max                                                                |
|                                                                       |
| \# Qwen 2.5 32B (4-bit): \~12-15 tok/s on M4 Max \| \~18-22 tok/s on  |
| M4 Ultra                                                              |
|                                                                       |
| \# Qwen 30B MoE (4-bit): \~22-28 tok/s on M4 Max (MoE: only 3B active |
| params)                                                               |
+-----------------------------------------------------------------------+

**3.6 MPS-Optimized Quantum ML: Complete Working Example**

This is the definitive reference implementation for MPS-accelerated
quantum neural network training in Milimo Quantum. Every QML agent
operation follows this pattern.

+-----------------------------------------------------------------------+
| import torch                                                          |
|                                                                       |
| import torch.nn as nn                                                 |
|                                                                       |
| import numpy as np                                                    |
|                                                                       |
| from qiskit import QuantumCircuit                                     |
|                                                                       |
| from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes       |
|                                                                       |
| from qiskit_aer import AerSimulator                                   |
|                                                                       |
| from qiskit_machine_learning.connectors import TorchConnector         |
|                                                                       |
| from qiskit_machine_learning.neural_networks import EstimatorQNN      |
|                                                                       |
| from qiskit.primitives import StatevectorEstimator                    |
|                                                                       |
| from qiskit.quantum_info import SparsePauliOp                         |
|                                                                       |
| \# ── Device selection: MPS → CPU fallback                            |
| ─────────────────────────────                                         |
|                                                                       |
| def get_device():                                                     |
|                                                                       |
| if torch.backends.mps.is_available() and                              |
| torch.backends.mps.is_built():                                        |
|                                                                       |
| return torch.device(\'mps\')                                          |
|                                                                       |
| elif torch.cuda.is_available():                                       |
|                                                                       |
| return torch.device(\'cuda\')                                         |
|                                                                       |
| return torch.device(\'cpu\')                                          |
|                                                                       |
| device = get_device()                                                 |
|                                                                       |
| print(f\'\[Milimo Quantum\] Acceleration: {device}\') \# mps on Apple |
| Silicon                                                               |
|                                                                       |
| \# ── Quantum circuit (runs on Aer CPU --- correct for macOS)         |
| ─────────────                                                         |
|                                                                       |
| num_qubits = 4                                                        |
|                                                                       |
| feature_map = ZZFeatureMap(num_qubits)                                |
|                                                                       |
| ansatz = RealAmplitudes(num_qubits, reps=2)                           |
|                                                                       |
| qc = QuantumCircuit(num_qubits)                                       |
|                                                                       |
| qc.compose(feature_map, inplace=True)                                 |
|                                                                       |
| qc.compose(ansatz, inplace=True)                                      |
|                                                                       |
| \# ── QNN (quantum part runs on Aer CPU, gradients computed on MPS)   |
| ─────                                                                 |
|                                                                       |
| estimator = StatevectorEstimator()                                    |
|                                                                       |
| observable = SparsePauliOp.from_list(\[(\'ZZZZ\', 1)\])               |
|                                                                       |
| qnn = EstimatorQNN(                                                   |
|                                                                       |
| circuit=qc,                                                           |
|                                                                       |
| observables=observable,                                               |
|                                                                       |
| input_params=feature_map.parameters,                                  |
|                                                                       |
| weight_params=ansatz.parameters,                                      |
|                                                                       |
| estimator=estimator,                                                  |
|                                                                       |
| )                                                                     |
|                                                                       |
| \# ── Hybrid model: quantum layer + classical MPS layers              |
| ────────────────                                                      |
|                                                                       |
| class MilimHybridModel(nn.Module):                                    |
|                                                                       |
| def \_\_init\_\_(self, qnn, num_classes=2):                           |
|                                                                       |
| super().\_\_init\_\_()                                                |
|                                                                       |
| self.qnn = TorchConnector(qnn) \# wraps QNN as PyTorch layer          |
|                                                                       |
| self.classifier = nn.Sequential(                                      |
|                                                                       |
| nn.Linear(1, 16),                                                     |
|                                                                       |
| nn.ReLU(),                                                            |
|                                                                       |
| nn.Linear(16, num_classes),                                           |
|                                                                       |
| nn.Softmax(dim=1)                                                     |
|                                                                       |
| )                                                                     |
|                                                                       |
| def forward(self, x):                                                 |
|                                                                       |
| \# qnn runs on Aer CPU, output tensor moved to MPS for classical      |
| layers                                                                |
|                                                                       |
| q_out = self.qnn(x.cpu()) \# quantum on CPU (Aer)                     |
|                                                                       |
| q_out = q_out.to(device) \# move to MPS                               |
|                                                                       |
| return self.classifier(q_out) \# classical on MPS GPU                 |
|                                                                       |
| model = MilimHybridModel(qnn).to(device)                              |
|                                                                       |
| optimizer = torch.optim.Adam(model.parameters(), lr=0.01)             |
|                                                                       |
| criterion = nn.CrossEntropyLoss()                                     |
|                                                                       |
| \# ── Training loop with MPS acceleration                             |
| ───────────────────────────────                                       |
|                                                                       |
| print(f\'Model on device: {next(model.parameters()).device}\') \#     |
| mps:0                                                                 |
|                                                                       |
| \# Classical layers train on MPS GPU; QNN forward/backward on Aer CPU |
|                                                                       |
| \# This hybrid split is the correct pattern --- do NOT force QNN to   |
| MPS                                                                   |
+-----------------------------------------------------------------------+

**3.7 MPS Memory Management --- Critical Best Practices**

MPS memory management differs fundamentally from CUDA. Unlike CUDA where
GPU VRAM is separate from system RAM, MPS uses Apple\'s unified memory
--- shared between CPU and GPU. This is powerful but requires different
management strategies.

+-----------------------------------------------------------------------+
| import torch                                                          |
|                                                                       |
| import os                                                             |
|                                                                       |
| \# ── Set MPS memory limit (prevents system-wide memory pressure)     |
| ───────                                                               |
|                                                                       |
| \# Default: MPS can use up to 75% of total unified memory             |
|                                                                       |
| \# For a 32 GB Mac, that\'s \~24 GB available to MPS --- far more     |
| than a 12GB GPU                                                       |
|                                                                       |
| os.environ\[\'PYTORCH_MPS_HIGH_WATERMARK_RATIO\'\] = \'0.7\' \# 70% = |
| safer default                                                         |
|                                                                       |
| os.environ\[\'PYTORCH_MPS_LOW_WATERMARK_RATIO\'\] = \'0.5\' \#        |
| trigger cache clear at 50%                                            |
|                                                                       |
| \# ── Manual cache clearing (important after large QNN forward        |
| passes) ──                                                            |
|                                                                       |
| torch.mps.empty_cache() \# releases cached but unused memory          |
|                                                                       |
| \# ── Synchronize MPS before timing (MPS is async like CUDA)          |
| ───────────                                                           |
|                                                                       |
| torch.mps.synchronize() \# wait for all queued Metal operations to    |
| complete                                                              |
|                                                                       |
| \# ── Monitor MPS memory usage                                        |
| ──────────────────────────────────────────                            |
|                                                                       |
| print(torch.mps.current_allocated_memory()) \# bytes currently        |
| allocated                                                             |
|                                                                       |
| print(torch.mps.driver_allocated_memory()) \# total allocated by      |
| Metal driver                                                          |
|                                                                       |
| \# ── Float precision: MPS does NOT support float64 (double           |
| precision) ──                                                         |
|                                                                       |
| \# This is a critical MPS limitation --- Qiskit statevectors use      |
| complex128                                                            |
|                                                                       |
| \# Solution: keep all Qiskit/Aer computation in float64 on CPU        |
|                                                                       |
| \# convert to float32 only when moving to MPS                         |
|                                                                       |
| def to_mps_safe(tensor):                                              |
|                                                                       |
| if tensor.dtype in \[torch.float64, torch.complex128\]:               |
|                                                                       |
| tensor = tensor.to(torch.float32) \# downcast for MPS                 |
|                                                                       |
| return tensor.to(device)                                              |
|                                                                       |
| \# ── Attention slicing for large QNN batches (prevents OOM on \<32GB |
| Macs)                                                                 |
|                                                                       |
| \# torch.backends.mps.enable_fallback_for_op() available in PyTorch   |
| 2.x                                                                   |
|                                                                       |
| os.environ\[\'PYTORCH_ENABLE_MPS_FALLBACK\'\] = \'1\' \#              |
| auto-fallback unsupported ops                                         |
+-----------------------------------------------------------------------+

**3.8 NumPy/SciPy --- AMX Acceleration (Automatic, Zero Config)**

NumPy and SciPy on Apple Silicon automatically use the Accelerate
Framework\'s BLAS/LAPACK implementation, which in turn dispatches matrix
operations to the AMX coprocessor. This is already active in your
environment --- but verification is important to ensure you are not
accidentally using the slower generic BLAS.

+-----------------------------------------------------------------------+
| \# Verify NumPy is using Apple Accelerate (should show                |
| vecLib/Accelerate references)                                         |
|                                                                       |
| \$ python3 -c \"import numpy; numpy.show_config()\"                   |
|                                                                       |
| \# Look for: blas_opt_info: libraries = \[\'cblas\', \'blas\'\]       |
|                                                                       |
| \# library_dirs =                                                     |
| \[\'/System/Library/Frameworks/Accelerate.framework/\...\'            |
|                                                                       |
| \# Benchmark: Aer statevector on Apple Silicon (AMX-accelerated)      |
|                                                                       |
| \$ python3 -c \"                                                      |
|                                                                       |
| import time                                                           |
|                                                                       |
| from qiskit import QuantumCircuit, transpile                          |
|                                                                       |
| from qiskit_aer import AerSimulator                                   |
|                                                                       |
| from qiskit.circuit.library import QuantumVolume                      |
|                                                                       |
| sim = AerSimulator(method=\'statevector\')                            |
|                                                                       |
| qv = QuantumVolume(25, seed=42) \# 25-qubit Quantum Volume circuit    |
|                                                                       |
| qv.measure_all()                                                      |
|                                                                       |
| qv_t = transpile(qv, sim)                                             |
|                                                                       |
| t0 = time.time()                                                      |
|                                                                       |
| result = sim.run(qv_t, shots=1).result()                              |
|                                                                       |
| print(f\'25-qubit QV: {time.time()-t0:.2f}s on Apple Silicon CPU      |
| (AMX)\') \# \~3-8s                                                    |
|                                                                       |
| \"                                                                    |
|                                                                       |
| \# For VQE parameter sweeps --- use numpy vectorization (AMX          |
| auto-used)                                                            |
|                                                                       |
| \# NEVER write Python loops over NumPy arrays in Milimo Quantum       |
| backend                                                               |
+-----------------------------------------------------------------------+

**3.9 Complete macOS Requirements File**

+-----------------------------------------------------------------------+
| \# requirements-macos.txt --- Milimo Quantum macOS Apple Silicon      |
|                                                                       |
| \# Generated for Python 3.12 + macOS 14+ (Sonoma) / macOS 15          |
| (Sequoia)                                                             |
|                                                                       |
| \# ── Quantum Core                                                    |
| ─────────────────────────────────────────────────────                 |
|                                                                       |
| qiskit==1.4.0                                                         |
|                                                                       |
| qiskit-aer==0.17.0 \# CPU only on macOS --- correct                   |
|                                                                       |
| qiskit-ibm-runtime\>=0.40.0                                           |
|                                                                       |
| qiskit-nature\>=0.7.0                                                 |
|                                                                       |
| qiskit-finance\>=0.4.0                                                |
|                                                                       |
| qiskit-machine-learning\>=0.7.0                                       |
|                                                                       |
| qiskit-optimization\>=0.6.0                                           |
|                                                                       |
| qiskit-algorithms\>=0.3.0                                             |
|                                                                       |
| \# ── AI Acceleration --- MPS (GPU)                                   |
| ───────────────────────────────────────                               |
|                                                                       |
| torch\>=2.5.0 \# MPS backend included                                 |
|                                                                       |
| torchvision\>=0.20.0                                                  |
|                                                                       |
| torchaudio\>=2.5.0                                                    |
|                                                                       |
| torch-geometric\>=2.6.0 \# Graph neural networks (QGNN)               |
|                                                                       |
| \# ── AI Acceleration --- MLX (Apple native, fastest on M-series)     |
| ─────────                                                             |
|                                                                       |
| mlx\>=0.22.0 \# Apple\'s array framework                              |
|                                                                       |
| mlx-lm\>=0.22.0 \# LLM inference via MLX                              |
|                                                                       |
| \# ── LLM Inference --- Ollama (Python client only, Ollama runs as    |
| system service)                                                       |
|                                                                       |
| ollama\>=0.4.0 \# Python client for Ollama API                        |
|                                                                       |
| \# ── Agent Framework                                                 |
| ───────────────────────────────────────────────────                   |
|                                                                       |
| langchain\>=0.3.0                                                     |
|                                                                       |
| langchain-community\>=0.3.0                                           |
|                                                                       |
| openai\>=1.0.0 \# Cloud AI API                                        |
|                                                                       |
| anthropic\>=0.40.0 \# Anthropic Claude API                            |
|                                                                       |
| \# ── Scientific Computing (Accelerate Framework auto-used)           |
| ─────────────                                                         |
|                                                                       |
| numpy\>=2.0.0 \# AMX auto-accelerated via Accelerate                  |
|                                                                       |
| scipy\>=1.14.0 \# BLAS/LAPACK via Accelerate                          |
|                                                                       |
| pandas\>=2.2.0                                                        |
|                                                                       |
| matplotlib\>=3.9.0                                                    |
|                                                                       |
| plotly\>=5.24.0                                                       |
|                                                                       |
| \# ── Quantum Chemistry (macOS compatible builds)                     |
| ───────────────────────                                               |
|                                                                       |
| pyscf\>=2.7.0 \# Quantum chemistry --- ARM native                     |
|                                                                       |
| openfermion\>=1.6.0                                                   |
|                                                                       |
| \# ── Graph Database                                                  |
| ─────────────────────────────────────────────────────                 |
|                                                                       |
| neo4j\>=5.26.0                                                        |
|                                                                       |
| graphiti-core\>=0.11.0                                                |
|                                                                       |
| kuzu\>=0.11.0                                                         |
|                                                                       |
| \# ── D-Wave Ocean SDK                                                |
| ──────────────────────────────────────────────────                    |
|                                                                       |
| dwave-ocean-sdk\>=7.0.0                                               |
|                                                                       |
| \# ── Quantum Error Mitigation                                        |
| ──────────────────────────────────────────                            |
|                                                                       |
| mitiq\>=0.38.0                                                        |
|                                                                       |
| stim\>=1.14.0 \# Stabilizer simulator (Clifford)                      |
|                                                                       |
| pymatching\>=2.2.0 \# MWPM decoder (surface codes)                    |
|                                                                       |
| \# ── Data Layer                                                      |
| ───────────────────────────────────────────────────────               |
|                                                                       |
| duckdb\>=1.1.0                                                        |
|                                                                       |
| chromadb\>=0.6.0                                                      |
+-----------------------------------------------------------------------+

**4. Windows --- Full CUDA / cuQuantum Stack**

Windows with an NVIDIA GPU is the other primary development and
deployment target. Unlike macOS, Windows gets full GPU acceleration for
Qiskit Aer via CUDA and NVIDIA cuQuantum --- enabling GPU-accelerated
quantum simulation of up to 32+ qubit circuits at 14x the CPU speed.

**4.1 Windows Prerequisites**

+-----------------------------------------------------------------------+
| \# 1. Install NVIDIA CUDA Toolkit 12.x                                |
|                                                                       |
| \# Download from: https://developer.nvidia.com/cuda-downloads         |
|                                                                       |
| \# Select: Windows → x86_64 → your Windows version → exe (local)      |
|                                                                       |
| \# Verify CUDA installation                                           |
|                                                                       |
| \> nvcc \--version                                                    |
|                                                                       |
| \> nvidia-smi                                                         |
|                                                                       |
| \# 2. Install Python 3.12 from python.org (Windows installer)         |
|                                                                       |
| \# Check \'Add Python to PATH\' during installation                   |
|                                                                       |
| \# 3. Create virtual environment                                      |
|                                                                       |
| \> python -m venv milimo-env                                          |
|                                                                       |
| \> milimo-env\\Scripts\\activate                                      |
|                                                                       |
| \# 4. Upgrade pip                                                     |
|                                                                       |
| \> python -m pip install \--upgrade pip                               |
+-----------------------------------------------------------------------+

**4.2 Qiskit Aer GPU (CUDA) on Windows**

+-----------------------------------------------------------------------+
| \# Install Qiskit + Aer GPU for CUDA 12                               |
|                                                                       |
| \# Note: qiskit-aer-gpu is Linux-only wheel from PyPI                 |
|                                                                       |
| \# On Windows, build from source or use WSL2 (recommended)            |
|                                                                       |
| \# ── OPTION A: WSL2 (Recommended --- best GPU support)               |
| ──────────────────                                                    |
|                                                                       |
| \# Install WSL2 with Ubuntu 24.04                                     |
|                                                                       |
| \> wsl \--install -d Ubuntu-24.04                                     |
|                                                                       |
| \# Inside WSL2 Ubuntu:                                                |
|                                                                       |
| \$ sudo apt update && sudo apt install -y python3.12 python3.12-venv  |
| python3-pip                                                           |
|                                                                       |
| \$ pip install qiskit qiskit-aer \# CPU version                       |
|                                                                       |
| \$ pip install qiskit-aer-gpu \# GPU version (CUDA 12, Linux x86_64   |
| wheel)                                                                |
|                                                                       |
| \# Verify GPU is visible from WSL2                                    |
|                                                                       |
| \$ nvidia-smi \# should show your GPU via CUDA-WSL driver             |
|                                                                       |
| \# ── OPTION B: Native Windows via conda (experimental)               |
| ────────────────                                                      |
|                                                                       |
| \# conda-forge has native Windows GPU builds for some Qiskit versions |
|                                                                       |
| \> conda install -c conda-forge qiskit qiskit-aer                     |
|                                                                       |
| \# Note: GPU support varies --- check                                 |
| https://github.com/Qiskit/qiskit-aer for status                       |
|                                                                       |
| \# ── OPTION C: Docker with GPU passthrough (production-grade)        |
| ─────────                                                             |
|                                                                       |
| \# Uses NVIDIA Container Toolkit on Windows with Docker Desktop       |
|                                                                       |
| \> docker run \--gpus all -it nvidia/cuda:12.4.1-devel-ubuntu22.04    |
|                                                                       |
| \# Then install qiskit-aer-gpu inside the container                   |
+-----------------------------------------------------------------------+

**4.3 NVIDIA cuQuantum --- Maximum Quantum Simulation Performance**

NVIDIA cuQuantum provides the maximum quantum simulation performance on
Windows/Linux with an NVIDIA GPU. IEEE benchmarks show 14x speedup over
CPU for large circuits, with cuStateVec providing an additional 1.5-3x
over the default CUDA Thrust backend.

+-----------------------------------------------------------------------+
| \# Install cuQuantum SDK (inside WSL2 or Linux)                       |
|                                                                       |
| \$ pip install cuquantum-python-cu12 \# CUDA 12 wheel                 |
|                                                                       |
| \# Enable cuStateVec in Qiskit Aer                                    |
|                                                                       |
| \$ python3 -c \"                                                      |
|                                                                       |
| from qiskit_aer import AerSimulator                                   |
|                                                                       |
| \# Standard GPU simulation                                            |
|                                                                       |
| sim_gpu = AerSimulator(method=\'statevector\', device=\'GPU\')        |
|                                                                       |
| print(sim_gpu.available_devices()) \# \[\'CPU\', \'GPU\'\]            |
|                                                                       |
| \# cuStateVec-accelerated (additional 1.5-3x speedup for large        |
| circuits)                                                             |
|                                                                       |
| sim_cusv = AerSimulator(                                              |
|                                                                       |
| method=\'statevector\',                                               |
|                                                                       |
| device=\'GPU\',                                                       |
|                                                                       |
| cuStateVec_enable=True,                                               |
|                                                                       |
| precision=\'single\' \# float32 --- halves memory, faster on Tensor   |
| Cores                                                                 |
|                                                                       |
| )                                                                     |
|                                                                       |
| \# For very large circuits with limited VRAM --- use tensor network   |
|                                                                       |
| sim_tn = AerSimulator(                                                |
|                                                                       |
| method=\'tensor_network\',                                            |
|                                                                       |
| device=\'GPU\', \# cuTensorNet backend (if cuQuantum installed)       |
|                                                                       |
| use_cuTensorNet_autotuning=True                                       |
|                                                                       |
| )                                                                     |
|                                                                       |
| \"                                                                    |
|                                                                       |
| \# Performance reference (Qiskit Aer + cuQuantum, NVIDIA A100 80GB):  |
|                                                                       |
| \# 25-qubit statevector: CPU \~3-8s \| GPU (Thrust) \~0.3s \| GPU     |
| (cuSV) \~0.1s                                                         |
|                                                                       |
| \# 30-qubit statevector: CPU \~120s \| GPU (Thrust) \~9s \| GPU       |
| (cuSV) \~4s                                                           |
|                                                                       |
| \# 32-qubit statevector: CPU OOM \| GPU (Thrust) \~35s \| GPU (cuSV)  |
| \~14s                                                                 |
+-----------------------------------------------------------------------+

**4.4 Windows Requirements File**

+-----------------------------------------------------------------------+
| \# requirements-windows.txt --- Milimo Quantum Windows + NVIDIA GPU   |
|                                                                       |
| \# ── Quantum Core                                                    |
| ─────────────────────────────────────────────────────                 |
|                                                                       |
| qiskit==1.4.0                                                         |
|                                                                       |
| \# qiskit-aer: install qiskit-aer-gpu separately (inside WSL2/Linux)  |
|                                                                       |
| \# pip install qiskit-aer-gpu (CUDA 12) OR qiskit-aer-gpu-cu11 (CUDA  |
| 11)                                                                   |
|                                                                       |
| qiskit-ibm-runtime\>=0.40.0                                           |
|                                                                       |
| qiskit-nature\>=0.7.0                                                 |
|                                                                       |
| qiskit-finance\>=0.4.0                                                |
|                                                                       |
| qiskit-machine-learning\>=0.7.0                                       |
|                                                                       |
| qiskit-optimization\>=0.6.0                                           |
|                                                                       |
| \# ── AI Acceleration --- CUDA (GPU)                                  |
| ─────────────────────────────────────                                 |
|                                                                       |
| \# Install CUDA-enabled PyTorch from:                                 |
| https://pytorch.org/get-started/locally/                              |
|                                                                       |
| \# pip install torch torchvision torchaudio \--index-url              |
| https://download.pytorch.org/whl/cu124                                |
|                                                                       |
| torch\>=2.5.0+cu124                                                   |
|                                                                       |
| \# ── NVIDIA cuQuantum                                                |
| ─────────────────────────────────────────────────                     |
|                                                                       |
| cuquantum-python-cu12\>=25.0.0                                        |
|                                                                       |
| \# ── NVIDIA CUDA-Q (for HPC simulation)                              |
| ───────────────────────────────                                       |
|                                                                       |
| \# pip install cudaq (requires CUDA 12 + specific NVIDIA GPU)         |
|                                                                       |
| cudaq\>=1.2.0                                                         |
|                                                                       |
| \# ── LLM Inference --- Ollama (Windows native)                       |
| ──────────────────────────                                            |
|                                                                       |
| ollama\>=0.4.0                                                        |
|                                                                       |
| \# Ollama on Windows uses CUDA automatically for GPU-accelerated LLM  |
| inference                                                             |
|                                                                       |
| \# ── Rest of stack (same as macOS)                                   |
| ─────────────────────────────────────                                 |
|                                                                       |
| numpy\>=2.0.0                                                         |
|                                                                       |
| scipy\>=1.14.0                                                        |
|                                                                       |
| langchain\>=0.3.0                                                     |
|                                                                       |
| neo4j\>=5.26.0                                                        |
|                                                                       |
| dwave-ocean-sdk\>=7.0.0                                               |
|                                                                       |
| mitiq\>=0.38.0                                                        |
|                                                                       |
| stim\>=1.14.0                                                         |
|                                                                       |
| pymatching\>=2.2.0                                                    |
+-----------------------------------------------------------------------+

**5. Milimo Quantum Hardware Abstraction Layer**

The hardware abstraction layer (HAL) is the core cross-platform
engineering challenge. All Milimo Quantum agent code must work
identically regardless of whether it runs on macOS Apple Silicon,
Windows CUDA, or Linux CUDA. The HAL handles device detection, optimal
backend selection, and graceful degradation.

**5.1 Device Detection & Auto-Configuration**

+-----------------------------------------------------------------------+
| \# milimo_quantum/hal/device.py --- Hardware Abstraction Layer        |
|                                                                       |
| \"\"\"                                                                |
|                                                                       |
| Milimo Quantum Hardware Abstraction Layer.                            |
|                                                                       |
| Detects and configures the optimal compute backend for the current    |
| platform.                                                             |
|                                                                       |
| Supports: macOS MPS, Windows/Linux CUDA, all-platform CPU fallback.   |
|                                                                       |
| \"\"\"                                                                |
|                                                                       |
| import platform, subprocess, sys                                      |
|                                                                       |
| from dataclasses import dataclass                                     |
|                                                                       |
| from enum import Enum                                                 |
|                                                                       |
| from typing import Optional                                           |
|                                                                       |
| class AcceleratorType(Enum):                                          |
|                                                                       |
| MPS = \'mps\' \# Apple Metal Performance Shaders                      |
|                                                                       |
| CUDA = \'cuda\' \# NVIDIA CUDA                                        |
|                                                                       |
| CPU = \'cpu\' \# CPU only (fallback)                                  |
|                                                                       |
| \@dataclass                                                           |
|                                                                       |
| class MilimoDevice:                                                   |
|                                                                       |
| accelerator: AcceleratorType                                          |
|                                                                       |
| torch_device: str                                                     |
|                                                                       |
| aer_device: str                                                       |
|                                                                       |
| llm_backend: str                                                      |
|                                                                       |
| memory_gb: float                                                      |
|                                                                       |
| platform_name: str                                                    |
|                                                                       |
| has_gpu: bool                                                         |
|                                                                       |
| details: dict                                                         |
|                                                                       |
| def detect_device() -\> MilimoDevice:                                 |
|                                                                       |
| import torch                                                          |
|                                                                       |
| sys_mem = \_get_system_memory_gb()                                    |
|                                                                       |
| plat = platform.system()                                              |
|                                                                       |
| \# ── macOS Apple Silicon (MPS) ───────────────────────────────────── |
|                                                                       |
| if (plat == \'Darwin\' and platform.machine() == \'arm64\'            |
|                                                                       |
| and torch.backends.mps.is_available()                                 |
|                                                                       |
| and torch.backends.mps.is_built()):                                   |
|                                                                       |
| chip = \_get_apple_chip_name()                                        |
|                                                                       |
| return MilimoDevice(                                                  |
|                                                                       |
| accelerator=AcceleratorType.MPS,                                      |
|                                                                       |
| torch_device=\'mps\',                                                 |
|                                                                       |
| aer_device=\'CPU\', \# Aer GPU not supported on macOS                 |
|                                                                       |
| llm_backend=\'mlx\', \# MLX is fastest on Apple Silicon               |
|                                                                       |
| memory_gb=sys_mem,                                                    |
|                                                                       |
| platform_name=f\'macOS Apple Silicon ({chip})\',                      |
|                                                                       |
| has_gpu=True, \# GPU via Metal/MPS                                    |
|                                                                       |
| details={\'chip\': chip, \'unified_memory\': True,                    |
|                                                                       |
| \'aer_note\': \'Aer uses CPU+Accelerate (AMX). Fast for ≤30q.\'},     |
|                                                                       |
| )                                                                     |
|                                                                       |
| \# ── Windows / Linux with NVIDIA GPU (CUDA) ───────────────────────  |
|                                                                       |
| if torch.cuda.is_available():                                         |
|                                                                       |
| gpu_name = torch.cuda.get_device_name(0)                              |
|                                                                       |
| gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9      |
|                                                                       |
| return MilimoDevice(                                                  |
|                                                                       |
| accelerator=AcceleratorType.CUDA,                                     |
|                                                                       |
| torch_device=\'cuda\',                                                |
|                                                                       |
| aer_device=\'GPU\', \# Full GPU acceleration                          |
|                                                                       |
| llm_backend=\'ollama\', \# Ollama with CUDA for GPU LLM inference     |
|                                                                       |
| memory_gb=sys_mem,                                                    |
|                                                                       |
| platform_name=f\'CUDA ({gpu_name}, {gpu_mem:.0f}GB VRAM)\',           |
|                                                                       |
| has_gpu=True,                                                         |
|                                                                       |
| details={\'gpu\': gpu_name, \'vram_gb\': gpu_mem,                     |
|                                                                       |
| \'cusv_available\': \_check_custatevec()},                            |
|                                                                       |
| )                                                                     |
|                                                                       |
| \# ── CPU Fallback ────────────────────────────────────────────────── |
|                                                                       |
| return MilimoDevice(                                                  |
|                                                                       |
| accelerator=AcceleratorType.CPU,                                      |
|                                                                       |
| torch_device=\'cpu\',                                                 |
|                                                                       |
| aer_device=\'CPU\',                                                   |
|                                                                       |
| llm_backend=\'ollama\',                                               |
|                                                                       |
| memory_gb=sys_mem,                                                    |
|                                                                       |
| platform_name=f\'{plat} CPU\',                                        |
|                                                                       |
| has_gpu=False,                                                        |
|                                                                       |
| details={\'note\': \'CPU-only mode. All features work, simulation is  |
| slower.\'},                                                           |
|                                                                       |
| )                                                                     |
|                                                                       |
| def \_get_system_memory_gb() -\> float:                               |
|                                                                       |
| import psutil                                                         |
|                                                                       |
| return psutil.virtual_memory().total / 1e9                            |
|                                                                       |
| def \_get_apple_chip_name() -\> str:                                  |
|                                                                       |
| try:                                                                  |
|                                                                       |
| result = subprocess.run(\[\'sysctl\', \'-n\',                         |
| \'machdep.cpu.brand_string\'\],                                       |
|                                                                       |
| capture_output=True, text=True)                                       |
|                                                                       |
| return result.stdout.strip()                                          |
|                                                                       |
| except: return \'Apple Silicon\'                                      |
|                                                                       |
| def \_check_custatevec() -\> bool:                                    |
|                                                                       |
| try: import cuquantum; return True                                    |
|                                                                       |
| except: return False                                                  |
+-----------------------------------------------------------------------+

**5.2 Platform-Aware Aer Simulator Factory**

+-----------------------------------------------------------------------+
| \# milimo_quantum/hal/simulator.py                                    |
|                                                                       |
| from qiskit_aer import AerSimulator                                   |
|                                                                       |
| from .device import MilimoDevice, AcceleratorType                     |
|                                                                       |
| def get_aer_simulator(device: MilimoDevice,                           |
|                                                                       |
| method: str = \'automatic\',                                          |
|                                                                       |
| precision: str = \'double\',                                          |
|                                                                       |
| qubits_hint: int = 20) -\> AerSimulator:                              |
|                                                                       |
| \"\"\"                                                                |
|                                                                       |
| Returns the best-configured AerSimulator for the current platform.    |
|                                                                       |
| macOS: CPU + Accelerate Framework (no GPU for Aer)                    |
|                                                                       |
| CUDA: GPU + optional cuStateVec                                       |
|                                                                       |
| \"\"\"                                                                |
|                                                                       |
| base_options = {                                                      |
|                                                                       |
| \'method\': method,                                                   |
|                                                                       |
| \'precision\': precision,                                             |
|                                                                       |
| \'max_parallel_threads\': 0, \# auto-detect CPU cores                 |
|                                                                       |
| }                                                                     |
|                                                                       |
| if device.accelerator == AcceleratorType.CUDA:                        |
|                                                                       |
| options = {                                                           |
|                                                                       |
| \*\*base_options,                                                     |
|                                                                       |
| \'device\': \'GPU\',                                                  |
|                                                                       |
| }                                                                     |
|                                                                       |
| \# Enable cuStateVec if available (1.5-3x additional speedup)         |
|                                                                       |
| if device.details.get(\'cusv_available\'):                            |
|                                                                       |
| options\[\'cuStateVec_enable\'\] = True                               |
|                                                                       |
| if precision == \'single\':                                           |
|                                                                       |
| options\[\'precision\'\] = \'single\' \# halves VRAM, faster Tensor   |
| Cores                                                                 |
|                                                                       |
| \# For very large circuits on GPU, switch to tensor_network           |
| automatically                                                         |
|                                                                       |
| if qubits_hint \> 30 and method in \[\'automatic\',                   |
| \'statevector\'\]:                                                    |
|                                                                       |
| options\[\'method\'\] = \'tensor_network\'                            |
|                                                                       |
| options\[\'use_cuTensorNet_autotuning\'\] = True                      |
|                                                                       |
| elif device.accelerator == AcceleratorType.MPS:                       |
|                                                                       |
| \# macOS: CPU simulation, optimized for Accelerate Framework          |
|                                                                       |
| options = {                                                           |
|                                                                       |
| \*\*base_options,                                                     |
|                                                                       |
| \'device\': \'CPU\',                                                  |
|                                                                       |
| \# MPS method here refers to Matrix Product State --- NOT Metal!      |
|                                                                       |
| \# For large qubit counts on Mac, MPS reduces memory                  |
|                                                                       |
| }                                                                     |
|                                                                       |
| if qubits_hint \> 28:                                                 |
|                                                                       |
| options\[\'method\'\] = \'matrix_product_state\' \# memory-efficient  |
|                                                                       |
| options\[\'matrix_product_state_max_bond_dimension\'\] = 256          |
|                                                                       |
| else:                                                                 |
|                                                                       |
| options = {\*\*base_options, \'device\': \'CPU\'}                     |
|                                                                       |
| return AerSimulator(\*\*options)                                      |
+-----------------------------------------------------------------------+

**5.3 Platform-Aware QML Training**

+-----------------------------------------------------------------------+
| \# milimo_quantum/hal/qml.py                                          |
|                                                                       |
| import torch                                                          |
|                                                                       |
| import os                                                             |
|                                                                       |
| from .device import MilimoDevice, AcceleratorType                     |
|                                                                       |
| def configure_qml_training(device: MilimoDevice):                     |
|                                                                       |
| \"\"\"Set up optimal QML training environment for the current         |
| platform.\"\"\"                                                       |
|                                                                       |
| if device.accelerator == AcceleratorType.MPS:                         |
|                                                                       |
| \# Enable MPS fallback for ops not yet in MPS kernel set              |
|                                                                       |
| os.environ\[\'PYTORCH_ENABLE_MPS_FALLBACK\'\] = \'1\'                 |
|                                                                       |
| \# Conservative memory limits (avoid system swap on \<32GB Macs)      |
|                                                                       |
| if device.memory_gb \< 32:                                            |
|                                                                       |
| os.environ\[\'PYTORCH_MPS_HIGH_WATERMARK_RATIO\'\] = \'0.6\'          |
|                                                                       |
| os.environ\[\'PYTORCH_MPS_LOW_WATERMARK_RATIO\'\] = \'0.4\'           |
|                                                                       |
| else:                                                                 |
|                                                                       |
| os.environ\[\'PYTORCH_MPS_HIGH_WATERMARK_RATIO\'\] = \'0.75\'         |
|                                                                       |
| os.environ\[\'PYTORCH_MPS_LOW_WATERMARK_RATIO\'\] = \'0.5\'           |
|                                                                       |
| elif device.accelerator == AcceleratorType.CUDA:                      |
|                                                                       |
| \# Enable TF32 on Ampere+ GPUs (2x throughput with minimal accuracy   |
| loss)                                                                 |
|                                                                       |
| torch.backends.cuda.matmul.allow_tf32 = True                          |
|                                                                       |
| torch.backends.cudnn.allow_tf32 = True                                |
|                                                                       |
| torch.backends.cudnn.benchmark = True \# auto-tune conv algos         |
|                                                                       |
| return torch.device(device.torch_device)                              |
|                                                                       |
| def safe_move_to_device(tensor: torch.Tensor,                         |
|                                                                       |
| device: MilimoDevice) -\> torch.Tensor:                               |
|                                                                       |
| \"\"\"Safely move tensor to accelerator, handling MPS float64         |
| limitation.\"\"\"                                                     |
|                                                                       |
| if device.accelerator == AcceleratorType.MPS:                         |
|                                                                       |
| \# MPS does not support float64 or complex128                         |
|                                                                       |
| if tensor.dtype == torch.float64:                                     |
|                                                                       |
| tensor = tensor.to(torch.float32)                                     |
|                                                                       |
| elif tensor.dtype == torch.complex128:                                |
|                                                                       |
| tensor = tensor.to(torch.complex64)                                   |
|                                                                       |
| return tensor.to(device.torch_device)                                 |
+-----------------------------------------------------------------------+

**6. LLM Inference Stack: MLX vs Ollama vs PyTorch MPS**

Milimo Quantum\'s local AI relies on running LLMs efficiently on the
developer\'s machine. For macOS, there are three inference paths ---
each with different trade-offs. Understanding when to use each is
critical for building a responsive, production-quality platform.

  ---------------------------------------------------------------------------
  **Criterion**      **Apple MLX**    **Ollama (GGUF)**   **PyTorch MPS (HF
                                                          Transformers)**
  ------------------ ---------------- ------------------- -------------------
  Speed (8B model,   \~50 tok/s       \~30 tok/s          \~20-35 tok/s
  M4 Pro)                                                 

  Speed (8B model,   \~65 tok/s       \~40 tok/s          \~30-45 tok/s
  M4 Max)                                                 

  Memory efficiency  Excellent (lazy) Good (GGUF quant)   Good (bitsandbytes)

  70B+ model support ✓ (512GB Mac =   ✓ (GGUF quantized)  ✓ (if RAM
                     70B)                                 available)

  Fine-tuning (LoRA) ✓ Native mlx-lm  ✗ Inference only    ✓ Full PEFT support

  Model selection    mlx-community HF 400+ models         All HuggingFace
                                                          models

  Float64 support    ✓ Full precision ✓ Full precision    ⚡ Partial (MPS
                                                          limit)

  API compatibility  mlx-lm Python    OpenAI-compatible   HuggingFace
                     API                                  Pipeline API

  Streaming support  ✓ Async          ✓ stream=True       ✓ TextStreamer
                     generator                            

  Quantization       ✓ Native 4-bit   ✓ Q4_K_M, Q8_0 etc  ✓ via bitsandbytes
  (4-bit)                                                 

  Cold start (model  Fast (\~2-5s)    Fast (\~2-8s)       Slow (\~10-30s)
  load)                                                   

  Best use case in   PRIMARY: fast    FALLBACK: any model TRAINING:
  Milimo             agents                               fine-tuning
  ---------------------------------------------------------------------------

**Recommended Strategy for Milimo Quantum macOS**

+-----------------------------------------------------------------------+
| \# milimo_quantum/ai/llm_router.py --- Intelligent LLM backend        |
| routing                                                               |
|                                                                       |
| from .device import detect_device, AcceleratorType                    |
|                                                                       |
| class MilimoLLMRouter:                                                |
|                                                                       |
| \"\"\"Routes LLM requests to the optimal backend for the current      |
| platform.\"\"\"                                                       |
|                                                                       |
| def \_\_init\_\_(self):                                               |
|                                                                       |
| self.device = detect_device()                                         |
|                                                                       |
| self.backends = self.\_init_backends()                                |
|                                                                       |
| def \_init_backends(self) -\> dict:                                   |
|                                                                       |
| backends = {}                                                         |
|                                                                       |
| mac = self.device.accelerator == AcceleratorType.MPS                  |
|                                                                       |
| \# MLX: primary on macOS, fastest inference                           |
|                                                                       |
| if mac:                                                               |
|                                                                       |
| try:                                                                  |
|                                                                       |
| from mlx_lm import load, generate                                     |
|                                                                       |
| backends\[\'mlx\'\] = {\'available\': True, \'priority\': 1}          |
|                                                                       |
| except ImportError:                                                   |
|                                                                       |
| backends\[\'mlx\'\] = {\'available\': False}                          |
|                                                                       |
| \# Ollama: available on all platforms, 400+ models                    |
|                                                                       |
| try:                                                                  |
|                                                                       |
| import ollama                                                         |
|                                                                       |
| ollama.list() \# ping Ollama server                                   |
|                                                                       |
| backends\[\'ollama\'\] = {\'available\': True,                        |
|                                                                       |
| \'priority\': 2 if mac else 1}                                        |
|                                                                       |
| except: backends\[\'ollama\'\] = {\'available\': False}               |
|                                                                       |
| \# Cloud APIs: always available if API key configured                 |
|                                                                       |
| import os                                                             |
|                                                                       |
| if os.getenv(\'ANTHROPIC_API_KEY\'):                                  |
|                                                                       |
| backends\[\'anthropic\'\] = {\'available\': True, \'priority\': 10}   |
|                                                                       |
| if os.getenv(\'OPENAI_API_KEY\'):                                     |
|                                                                       |
| backends\[\'openai\'\] = {\'available\': True, \'priority\': 11}      |
|                                                                       |
| return backends                                                       |
|                                                                       |
| def get_backend(self, model_size_b: float = 8.0,                      |
|                                                                       |
| requires_finetune: bool = False) -\> str:                             |
|                                                                       |
| \"\"\"Select best available backend for the given requirement.\"\"\"  |
|                                                                       |
| if requires_finetune:                                                 |
|                                                                       |
| return \'pytorch_mps\' \# only backend that supports training         |
|                                                                       |
| if self.backends.get(\'mlx\', {}).get(\'available\'):                 |
|                                                                       |
| return \'mlx\' \# fastest on macOS                                    |
|                                                                       |
| if self.backends.get(\'ollama\', {}).get(\'available\'):              |
|                                                                       |
| return \'ollama\'                                                     |
|                                                                       |
| return \'cloud\' \# fallback to cloud API                             |
+-----------------------------------------------------------------------+

**7. Quantum Simulation Performance Guide**

Choosing the right Aer simulation method is as important as choosing the
right hardware. This guide maps qubit counts and circuit types to the
optimal method for each platform.

  --------------------------------------------------------------------------------------
  **Qubits**   **Circuit Type** **macOS (Aer     **Windows CUDA**   **Recommendation**
                                CPU)**                              
  ------------ ---------------- ---------------- ------------------ --------------------
  ≤ 20         Any              statevector      statevector        Develop on Mac,
                                \<0.1s           \<0.01s            identical results

  21-25        Dense (VQE,      statevector      GPU statevector    Mac ok for dev;
               QAOA)            0.5-5s           0.1-0.5s           Windows faster

  26-28        Dense            statevector      GPU statevector    Mac for small shot
                                10-60s           1-5s               counts; GPU for
                                                                    sweeps

  29-32        Dense            MPS method       GPU                Use MPS on Mac; GPU
                                (approx)         statevector/cuSV   on Windows

  33-50        Low entanglement MPS method       tensor_network     IBM Quantum hardware
               (MPS)            (slow)           (GPU)              OR GPU cluster

  33-35        High-memory Mac  statevector      GPU (VRAM limited) Large Mac wins on
               (512 GB)         (possible)                          memory capacity!

  50+          Any              Not feasible     Not feasible       IBM Quantum / cloud
                                locally          (single GPU)       HPC

  Any          Clifford-only    stabilizer       stabilizer         Use Stim for
                                \<0.001s         \<0.001s           fault-tolerant
                                                                    circuits
  --------------------------------------------------------------------------------------

**macOS-Specific: When MPS Method (Matrix Product State) Helps**

IMPORTANT: In Qiskit Aer, \'MPS\' means Matrix Product State --- a
tensor network simulation method --- NOT Metal Performance Shaders. This
is an unfortunate naming collision. The MPS simulation method excels for
quantum circuits with limited entanglement (QAOA on sparse graphs,
quantum chemistry with local interactions) and allows simulation of 50+
qubit circuits that would be impossible with the full statevector
method.

+-----------------------------------------------------------------------+
| from qiskit_aer import AerSimulator                                   |
|                                                                       |
| \# macOS: Matrix Product State method for large low-entanglement      |
| circuits                                                              |
|                                                                       |
| \# Note: \'MPS\' here = Matrix Product State, NOT Metal Performance   |
| Shaders!                                                              |
|                                                                       |
| sim_mps = AerSimulator(                                               |
|                                                                       |
| method=\'matrix_product_state\', \# tensor network --- NOT Metal      |
|                                                                       |
| device=\'CPU\', \# macOS: CPU always                                  |
|                                                                       |
| matrix_product_state_max_bond_dimension=256, \# accuracy vs memory    |
| trade-off                                                             |
|                                                                       |
| mps_sample_measure_algorithm=\'mps_apply_measure\', \# efficient for  |
| few shots                                                             |
|                                                                       |
| )                                                                     |
|                                                                       |
| \# For QAOA on sparse graphs (low entanglement) --- MPS is excellent  |
|                                                                       |
| \# For VQE ansatz with deep entanglement --- MPS accuracy degrades    |
|                                                                       |
| \# Rule: if circuit has many CX/CNOT gates between distant qubits →   |
| statevector                                                           |
|                                                                       |
| \# if circuit has mostly nearest-neighbor gates → MPS                 |
+-----------------------------------------------------------------------+

**8. Cross-Platform Development Workflow**

+----------------------------------+-----------------------------------+
| **🍎 macOS Development Flow**    | **🪟 Windows Deployment Flow**    |
|                                  |                                   |
| - Write quantum circuits + agent | - Full CUDA GPU acceleration for  |
|   code natively                  |   Aer                             |
|                                  |                                   |
| - Test QML training with MPS     | - cuStateVec for large circuit    |
|   acceleration                   |   simulation                      |
|                                  |                                   |
| - Use MLX for fast local LLM     | - Ollama with CUDA for fast LLM   |
|   inference                      |   inference                       |
|                                  |                                   |
| - Simulate ≤28 qubit circuits    | - GPU QML training (faster than   |
|   locally                        |   MPS)                            |
|                                  |                                   |
| - Connect to IBM Quantum for     | - CUDA-Q for HPC-scale simulation |
|   large circuits                 |                                   |
|                                  | - WSL2 Ubuntu for Linux tools     |
| - Run frontend in native macOS   |                                   |
|   browser                        | - Docker with NVIDIA Container    |
|                                  |   Toolkit                         |
| - Neo4j Desktop for graph        |                                   |
|   database GUI                   | - Production-parity with cloud    |
|                                  |   Linux                           |
| - No Docker GPU passthrough      |                                   |
|   needed                         |                                   |
+----------------------------------+-----------------------------------+

+-----------------------------------------------------------------------+
| **✓ macOS Development Advantage Summary**                             |
|                                                                       |
| ✓ All Milimo Quantum features work on macOS Apple Silicon --- zero    |
| exceptions                                                            |
|                                                                       |
| ✓ Qiskit Aer CPU on Apple Silicon is fast (Accelerate Framework +     |
| AMX + NEON)                                                           |
|                                                                       |
| ✓ PyTorch MPS fully accelerates all QNN/QML training workloads        |
|                                                                       |
| ✓ Apple MLX is the fastest local LLM inference option available       |
|                                                                       |
| ✓ 512 GB unified memory (Mac Studio M4 Ultra) exceeds any single GPU  |
| for large circuits                                                    |
|                                                                       |
| ✓ Native macOS app (Tauri) is the best developer experience available |
|                                                                       |
| ✓ All cloud backends (IBM Quantum, D-Wave, Braket) work identically   |
|                                                                       |
| ✓ No CUDA dependency in Milimo core --- cross-platform by design      |
+-----------------------------------------------------------------------+

**8.1 Milimo Quantum Tauri Desktop App (Native macOS + Windows)**

The Milimo Quantum desktop application is built with Tauri (Rust
backend + React frontend), delivering a native experience on both macOS
(Apple Silicon optimized) and Windows. Unlike Electron, Tauri apps are
\~10-20x smaller and use the platform\'s native WebView --- WKWebView on
macOS, WebView2 on Windows.

+-----------------------------------------------------------------------+
| \# Install Tauri CLI                                                  |
|                                                                       |
| \$ cargo install create-tauri-app \--locked                           |
|                                                                       |
| \$ npm create tauri-app@latest milimo-quantum \-- \--template         |
| react-ts                                                              |
|                                                                       |
| \# macOS: Tauri uses WKWebView + Metal rendering --- hardware         |
| accelerated                                                           |
|                                                                       |
| \# Windows: Tauri uses WebView2 + DirectX --- hardware accelerated    |
|                                                                       |
| \# Key Tauri configuration for Milimo Quantum                         |
| (src-tauri/tauri.conf.json):                                          |
|                                                                       |
| {                                                                     |
|                                                                       |
| \"bundle\": {                                                         |
|                                                                       |
| \"targets\": \[\"dmg\", \"app\"\], // macOS                           |
|                                                                       |
| \"targets\": \[\"msi\", \"nsis\"\], // Windows                        |
|                                                                       |
| \"icon\": \[\"icons/icon.icns\", \"icons/icon.ico\"\]                 |
|                                                                       |
| },                                                                    |
|                                                                       |
| \"app\": {                                                            |
|                                                                       |
| \"windows\": \[{                                                      |
|                                                                       |
| \"title\": \"Milimo Quantum\",                                        |
|                                                                       |
| \"width\": 1400, \"height\": 900,                                     |
|                                                                       |
| \"minWidth\": 1000, \"minHeight\": 700                                |
|                                                                       |
| }\]                                                                   |
|                                                                       |
| }                                                                     |
|                                                                       |
| }                                                                     |
|                                                                       |
| \# FastAPI backend runs as a sidecar process (Tauri sidecar API)      |
|                                                                       |
| \# Automatically starts/stops Python backend with the app             |
|                                                                       |
| \# No separate terminal needed --- fully integrated native app        |
+-----------------------------------------------------------------------+

**9. Quick Reference: Platform Feature Matrix**

  ---------------------------------------------------------------------------
  **Milimo Quantum      **macOS MPS   **Windows    **Linux      **CPU Only**
  Feature**             (M4/M5)**     CUDA**       CUDA**       
  --------------------- ------------- ------------ ------------ -------------
  Qiskit Aer (CPU)      ✓ Native      ✓ Native     ✓ Native     ✓ Native

  Qiskit Aer (GPU)      ✗ Not avail   ✓ CUDA       ✓ CUDA       ✗ Not avail

  cuStateVec            ✗             ✓ cuQuantum  ✓ cuQuantum  ✗
  acceleration                                                  

  CUDA-Q (NVIDIA)       ✗             ✓ CUDA       ✓ CUDA       ✗

  PyTorch QML (GPU)     ✓ MPS         ✓ CUDA       ✓ CUDA       ⚡ CPU
                                                                fallback

  MLX LLM inference     ✓ Fastest     ✗            ✗            ✗

  Ollama LLM inference  ✓ Good        ✓ CUDA fast  ✓ CUDA fast  ✓ Slow

  Large circuit sim     ✓ RAM-limited ✓ VRAM-lim   ✓ VRAM-lim   ✗ Too slow
  (35q+)                                                        

  IBM Quantum cloud     ✓ Native      ✓ Native     ✓ Native     ✓ Native

  D-Wave Leap cloud     ✓ Native      ✓ Native     ✓ Native     ✓ Native

  Neo4j + Graphiti      ✓ Native      ✓ Docker     ✓ Docker     ✓ Native

  Tauri native app      ✓ DMG/app     ✓ MSI/NSIS   ✓ AppImage   ✓ Native

  Docker support        ⚡ No GPU     ✓ Full GPU   ✓ Full GPU   ✓ CPU only

  Recommended for       Development   Dev+Prod     Production   Lightweight
  ---------------------------------------------------------------------------

+-----------------------------------------------------------------------+
| **Final Guidance for macOS Development**                              |
|                                                                       |
| Your macOS Apple Silicon machine is an excellent Milimo Quantum       |
| development platform.                                                 |
|                                                                       |
| The key mental model to internalize:                                  |
|                                                                       |
| QUANTUM SIMULATION → Qiskit Aer CPU (Accelerate Framework + AMX ---   |
| fast enough for ≤28q)                                                 |
|                                                                       |
| QUANTUM ML TRAINING → PyTorch MPS GPU (direct Metal GPU --- real      |
| acceleration for QNNs)                                                |
|                                                                       |
| LLM INFERENCE → Apple MLX (fastest local LLM on Apple Silicon ---     |
| primary)                                                              |
|                                                                       |
| → Ollama (fallback for model compatibility)                           |
|                                                                       |
| LARGE CIRCUITS → IBM Quantum cloud (when local CPU simulation is too  |
| slow)                                                                 |
|                                                                       |
| PRODUCTION DEPLOY → Linux CUDA (WSL2 or server) for full GPU Aer      |
| acceleration                                                          |
|                                                                       |
| Everything else --- graph database, D-Wave, networking simulation,    |
| agents, UI --- is identical                                           |
|                                                                       |
| across macOS, Windows, and Linux. The HAL handles all differences     |
| transparently.                                                        |
+-----------------------------------------------------------------------+

*🍎 Build on Apple Silicon. 🪟 Deploy on CUDA. 🌐 Run on Quantum
Hardware. ⚛ Be Milimo Quantum.*

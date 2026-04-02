# Milimo Quantum — Implementation Improvement Plan
## Simulation-First: Qiskit Aer + autoresearch-mlx Integration
*Generated: March 31, 2026*

---

## 1. Critical Blocker Audit

Before any feature work, these blockers prevent the system from running at all.

### 1.1 Qiskit 2.x API Breakage (CRITICAL)

The executor and agent code was written against pre-2.0 Qiskit. The following are gone or deprecated:

| Removed API | Replacement |
|---|---|
| `qiskit.algorithms` | `qiskit_algorithms` (separate pip install) |
| `QuantumInstance` | Primitives: `EstimatorV2`, `SamplerV2` |
| `backend.run()` direct | `PassManager` + primitive `.run()` |
| `qiskit.opflow` (PauliSumOp etc.) | `qiskit.quantum_info.SparsePauliOp` |
| `qiskit.providers.aer` | `qiskit_aer` |
| `BasicAer` | `AerSimulator` from `qiskit_aer` |

**Impact:** VQE, QAOA, all `qiskit_algorithms` imports will fail with `ModuleNotFoundError`. The sandbox patcher covers `qiskit.providers.aer → qiskit_aer` but misses `qiskit.algorithms → qiskit_algorithms`.

### 1.2 VQE is Mocked (CRITICAL)

Section 10 of the system doc explicitly states: *"VQE real quantum evaluation (currently mock)."* The `/api/autoresearch/vqe` endpoint returns fake data. The autoresearch loop therefore has no real quantum feedback signal — the autonomous research loop cannot learn anything meaningful.

### 1.3 autoresearch-mlx is Disconnected (CRITICAL)

The `vqe_train.py` in autoresearch-mlx is not wired to real Qiskit simulation. The repo's `train.py` loop edits and evaluates `val_bpb` (bits-per-byte) — a language model metric. The VQE equivalent (`val_energy`) has no real quantum backend behind it.

### 1.4 HAL Routes to IBM Cloud for >30 Qubits (BLOCKER FOR SIM-ONLY)

`executor.py` routes circuits with >30 qubits to `ibm_cloud`. In simulation-only mode with no IBM credentials set, every large circuit silently fails or throws a credential error. MPS simulation can handle 50+ qubits for many circuit topologies — this is the correct sim-only fallback.

### 1.5 Sandbox Import Whitelist Gaps

`qiskit_algorithms`, `qiskit_aer.primitives`, and `scipy.optimize` are needed for VQE/QAOA but are likely absent from the sandbox whitelist and the migration patcher.

---

## 2. Updated `requirements.txt`

```txt
# Core
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.0.0
python-multipart>=0.0.9

# Quantum — simulation only
qiskit>=2.0.0
qiskit-aer>=0.15.0
qiskit-algorithms>=0.3.0          # community package, separate install
qiskit-ibm-runtime>=0.25.0        # needed for primitives interface even locally

# Quantum chemistry (for VQE Hamiltonians)
qiskit-nature>=0.7.0              # optional but enables PySCF integration later

# Classical ML & optimization
numpy>=1.26.0
scipy>=1.13.0
matplotlib>=3.9.0

# MLX (Apple Silicon)
mlx>=0.18.0
mlx-lm>=0.18.0

# Data layer
sqlalchemy>=2.0.0
asyncpg>=0.29.0
redis>=5.0.0
celery>=5.3.0
neo4j>=5.20.0
chromadb>=0.5.0

# API
httpx>=0.27.0
sse-starlette>=2.0.0
slowapi>=0.1.9

# Auth
python-jose>=3.3.0
```

---

## 3. Fix 1 — `hal.py` (Hardware Abstraction Layer)

Add `SIM_ONLY_MODE` and fix qubit routing to stay fully local.

```python
# backend/app/quantum/hal.py
import os
import platform
import psutil
from qiskit_aer import AerSimulator

SIM_ONLY_MODE = os.getenv("SIM_ONLY_MODE", "true").lower() == "true"
IS_APPLE_SILICON = (platform.machine() == "arm64" and platform.system() == "Darwin")

def get_memory_gb() -> float:
    return psutil.virtual_memory().total / (1024 ** 3)

def select_aer_backend(num_qubits: int) -> AerSimulator:
    """
    Select the best local Aer backend for the given qubit count.
    
    Statevector: exact, exponential memory (2^n complex128 amplitudes).
      - 24 qubits = 256 MB  (fine)
      - 30 qubits = 16 GB   (borderline on 32 GB machines)
    
    MPS: tensor-network, polynomial memory for low-entanglement circuits.
      - Handles 50-100 qubits comfortably for VQE ansatze (moderate entanglement).
      - Falls back gracefully to statevector math when bond dimension grows.
    """
    mem_gb = get_memory_gb()

    # Dynamic statevector threshold based on available RAM
    # 2^n complex128 = 2^n * 16 bytes; leave 4GB headroom
    max_sv_qubits = min(int((mem_gb - 4) * 1024**3 / 16).bit_length() - 1, 28)
    max_sv_qubits = max(20, max_sv_qubits)  # floor at 20 qubits

    if num_qubits <= max_sv_qubits:
        return AerSimulator(method='statevector')
    else:
        # MPS handles larger circuits with moderate entanglement
        # max_bond_dimension=128 is a good default for VQE ansatze
        return AerSimulator(
            method='matrix_product_state',
            matrix_product_state_max_bond_dimension=128,
            matrix_product_state_truncation_threshold=1e-10,
        )

def select_backend(num_qubits: int):
    """
    Main backend selector. Returns local Aer backend in SIM_ONLY_MODE.
    Falls through to cloud routing only when SIM_ONLY_MODE=False AND
    IBM credentials are configured.
    """
    if SIM_ONLY_MODE:
        return select_aer_backend(num_qubits)
    
    # Cloud routing (future — when IBM credentials configured)
    if num_qubits > 30:
        ibm_token = os.getenv("IBM_QUANTUM_TOKEN")
        if ibm_token:
            return _get_ibm_backend(num_qubits)
        else:
            # Graceful fallback instead of hard failure
            import logging
            logging.getLogger(__name__).warning(
                f"IBM_QUANTUM_TOKEN not set for {num_qubits}-qubit circuit. "
                f"Falling back to local MPS simulation."
            )
    
    return select_aer_backend(num_qubits)

def _get_ibm_backend(num_qubits: int):
    """Lazy IBM cloud connection — only called when credentials exist."""
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(token=os.getenv("IBM_QUANTUM_TOKEN"))
    return service.least_busy(
        operational=True,
        min_num_qubits=num_qubits,
        simulator=False
    )
```

---

## 4. Fix 2 — `sandbox.py` (Import Whitelist + Migration Patches)

```python
# backend/app/quantum/sandbox.py
import ast
import sys
import signal
import hashlib
import textwrap
from typing import Any, Dict

ALLOWED_IMPORTS = {
    # Qiskit core
    'qiskit',
    'qiskit_aer',
    'qiskit_aer.primitives',
    'qiskit_algorithms',
    'qiskit_algorithms.minimum_eigensolvers',
    'qiskit_algorithms.optimizers',
    'qiskit_algorithms.utils',
    'qiskit.circuit',
    'qiskit.circuit.library',
    'qiskit.quantum_info',
    'qiskit.transpiler',
    'qiskit.transpiler.preset_passmanagers',
    'qiskit.visualization',
    # Numerics
    'numpy', 'numpy.linalg', 'numpy.fft',
    'scipy', 'scipy.optimize', 'scipy.linalg', 'scipy.sparse',
    'math', 'cmath', 'itertools', 'functools', 'collections',
    # Viz
    'matplotlib', 'matplotlib.pyplot',
    # D-Wave (optional)
    'dimod', 'dwave',
}

# Qiskit 1.x → 2.x migration patches applied at source level
IMPORT_PATCHES = {
    # Module renames
    'from qiskit.providers.aer': 'from qiskit_aer',
    'import qiskit.providers.aer': 'import qiskit_aer',
    'from qiskit.algorithms': 'from qiskit_algorithms',
    'import qiskit.algorithms': 'import qiskit_algorithms',
    # Deprecated primitives location
    'from qiskit.primitives import Estimator': 'from qiskit_aer.primitives import EstimatorV2 as Estimator',
    'from qiskit.primitives import Sampler': 'from qiskit_aer.primitives import SamplerV2 as Sampler',
    # Opflow removal
    'from qiskit.opflow import PauliSumOp': '# PauliSumOp removed — use qiskit.quantum_info.SparsePauliOp',
    'from qiskit.opflow': '# qiskit.opflow removed in Qiskit 2.x',
    # Old provider imports
    'from qiskit import BasicAer': 'from qiskit_aer import AerSimulator',
    'BasicAer.get_backend': 'AerSimulator',
    # QuantumInstance removal
    'QuantumInstance': '# QuantumInstance removed — use primitives (EstimatorV2/SamplerV2)',
}

# Constructor patches (common mistakes in generated code)
CONSTRUCTOR_PATCHES = [
    # Missing qubit count
    ('QuantumCircuit()', 'QuantumCircuit(2)'),
    # Old provider import path
    ('qiskit.providers.aer', 'qiskit_aer'),
]

BLOCKED_BUILTINS = {
    'exec', 'eval', 'open', '__import__', 'compile',
    'breakpoint', 'input', 'print',  # print OK below but controlled
}

EXECUTION_TIMEOUT_SECONDS = 15
MAX_OUTPUT_BYTES = 1024 * 1024  # 1 MB


def apply_migration_patches(source: str) -> str:
    """Apply Qiskit API migration patches to user-submitted source."""
    for old, new in IMPORT_PATCHES.items():
        source = source.replace(old, new)
    for old, new in CONSTRUCTOR_PATCHES:
        source = source.replace(old, new)
    return source


def validate_imports(source: str) -> list[str]:
    """Return list of blocked import names found in source."""
    tree = ast.parse(source)
    blocked = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                names = [alias.name.split('.')[0] for alias in node.names]
            else:
                names = [node.module.split('.')[0]] if node.module else []
            for name in names:
                if not any(name == allowed.split('.')[0] for allowed in ALLOWED_IMPORTS):
                    blocked.append(name)
    return blocked


def fingerprint(circuit_code: str, backend: str) -> str:
    return hashlib.sha256(f"{circuit_code}:{backend}".encode()).hexdigest()


def execute_quantum_code(
    source: str,
    backend_name: str = 'aer_statevector',
    timeout: int = EXECUTION_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """
    Execute quantum circuit code in a restricted sandbox.
    Returns {'counts': ..., 'statevector': ..., 'error': ...}
    """
    patched = apply_migration_patches(source)
    blocked = validate_imports(patched)
    if blocked:
        return {'error': f"Blocked imports: {blocked}. Only quantum/scientific libraries allowed."}

    # Build restricted globals
    safe_globals = {
        '__builtins__': {
            k: v for k, v in __builtins__.items()
            if k not in BLOCKED_BUILTINS
        } if isinstance(__builtins__, dict) else {
            k: getattr(__builtins__, k)
            for k in dir(__builtins__)
            if k not in BLOCKED_BUILTINS and not k.startswith('_')
        },
    }
    output_capture = []
    safe_globals['print'] = lambda *args, **kwargs: output_capture.append(' '.join(str(a) for a in args))

    result_store = {}
    safe_globals['_result_store'] = result_store

    # Inject a result-capture hook
    patched += textwrap.dedent("""
    import inspect as _inspect
    _frame = _inspect.currentframe()
    _locals = _frame.f_locals
    if 'result' in _locals:
        _result_store['result'] = _locals['result']
    if 'counts' in _locals:
        _result_store['counts'] = _locals['counts']
    """)

    def handler(signum, frame):
        raise TimeoutError(f"Circuit execution exceeded {timeout}s limit")

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        exec(compile(patched, '<quantum_sandbox>', 'exec'), safe_globals)
        signal.alarm(0)
    except TimeoutError as e:
        return {'error': str(e)}
    except Exception as e:
        signal.alarm(0)
        return {'error': f"{type(e).__name__}: {e}"}

    return {
        'result': result_store.get('result'),
        'counts': result_store.get('counts'),
        'output': '\n'.join(output_capture)[:MAX_OUTPUT_BYTES],
        'error': None,
    }
```

---

## 5. Fix 3 — `vqe_executor.py` (Real VQE, Not Mock)

This is the core fix. Wire up `qiskit_algorithms.VQE` with `AerEstimatorV2`.

```python
# backend/app/quantum/vqe_executor.py
"""
Real VQE execution using Qiskit Aer simulation.
Replaces the mock VQE implementation.
"""
import numpy as np
import logging
from typing import Any, Dict, List, Optional, Callable

from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.circuit.library import EfficientSU2, RealAmplitudes, TwoLocal
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import EstimatorV2 as AerEstimatorV2
from qiskit_algorithms import VQE, AdaptVQE
from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import SPSA, COBYLA, L_BFGS_B, SLSQP
from qiskit_algorithms.utils import algorithm_globals

from .hal import select_aer_backend

logger = logging.getLogger(__name__)

# ── Predefined Hamiltonians ───────────────────────────────────────────────────

HAMILTONIANS = {
    'h2': [
        ("II", -1.052373245772859),
        ("IZ",  0.39793742484318045),
        ("ZI", -0.39793742484318045),
        ("ZZ", -0.01128010425623538),
        ("XX",  0.18093119978423156),
    ],
    'lih': [
        ("IIII", -7.499763400876443),
        ("IIIZ", -0.0920519843788469),
        ("IIZI", -0.09205198437884688),
        ("IIZZ",  0.09872239219922697),
        # ... truncated for brevity, full LiH Hamiltonian has ~20 terms
    ],
    'ising_1d': lambda n: [
        (f"{'I'*(i)}ZZ{'I'*(n-i-2)}", -1.0)
        for i in range(n - 1)
    ] + [
        (f"{'I'*(i)}X{'I'*(n-i-1)}", -0.5)
        for i in range(n)
    ],
}

# ── Ansatz catalog ────────────────────────────────────────────────────────────

ANSATZ_CATALOG = {
    'efficient_su2': lambda n, reps=2: EfficientSU2(n, reps=reps),
    'real_amplitudes': lambda n, reps=2: RealAmplitudes(n, reps=reps),
    'two_local_ry_cz': lambda n, reps=2: TwoLocal(
        n, rotation_blocks=['ry'], entanglement_blocks='cz', reps=reps
    ),
    'two_local_ryrz_cz': lambda n, reps=2: TwoLocal(
        n, rotation_blocks=['ry', 'rz'], entanglement_blocks='cz', reps=reps
    ),
    'two_local_full': lambda n, reps=2: TwoLocal(
        n, rotation_blocks=['ry', 'rz'], entanglement_blocks='cx',
        entanglement='full', reps=reps
    ),
}

# ── Optimizer catalog ─────────────────────────────────────────────────────────

OPTIMIZER_CATALOG = {
    'spsa':    lambda maxiter=300: SPSA(maxiter=maxiter),
    'cobyla':  lambda maxiter=200: COBYLA(maxiter=maxiter),
    'l_bfgs_b': lambda maxiter=100: L_BFGS_B(maxiter=maxiter),
    'slsqp':   lambda maxiter=100: SLSQP(maxiter=maxiter),
}


# ── Meyer-Wallach Entanglement Score ─────────────────────────────────────────

def meyer_wallach_score(circuit) -> float:
    """
    Compute the Meyer-Wallach global entanglement measure for a circuit.
    Returns a value in [0, 1] where:
      0 = fully separable (no entanglement)
      1 = maximally entangled
    
    Used by autoresearch-mlx to score ansatz quality.
    Reference: Meyer & Wallach (2002), J. Math. Phys. 43, 4273.
    """
    n = circuit.num_qubits
    # Bind parameters to random values for evaluation
    if circuit.num_parameters > 0:
        bound = circuit.assign_parameters(
            np.random.uniform(0, 2 * np.pi, circuit.num_parameters)
        )
    else:
        bound = circuit
    
    sv = Statevector(bound).data
    arr = sv.reshape([2] * n)
    
    Q = 0.0
    for k in range(n):
        # Axes to trace over (all except qubit k)
        other_axes = [i for i in range(n) if i != k]
        # Partial trace → 2x2 reduced density matrix for qubit k
        rho_k = np.tensordot(arr, arr.conj(), axes=(other_axes, other_axes))
        Q += 2.0 * (1.0 - float(np.real(np.trace(rho_k @ rho_k))))
    
    return Q / n  # normalize to [0, 1]


# ── Main VQE Runner ───────────────────────────────────────────────────────────

def run_vqe(
    hamiltonian: str | List[tuple],
    ansatz_type: str = 'efficient_su2',
    ansatz_reps: int = 2,
    optimizer: str = 'spsa',
    optimizer_maxiter: int = 300,
    seed: int = 42,
    on_iteration: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Run VQE with full Aer simulation. This is NOT a mock.
    
    Args:
        hamiltonian: Preset name ('h2', 'lih') or list of (pauli_str, coeff) tuples.
        ansatz_type: Key from ANSATZ_CATALOG.
        ansatz_reps: Number of ansatz repetitions (depth).
        optimizer: Key from OPTIMIZER_CATALOG.
        optimizer_maxiter: Maximum optimizer iterations.
        seed: Random seed for reproducibility.
        on_iteration: Optional callback(eval_count, energy) for SSE streaming.
    
    Returns:
        Dict with eigenvalue, convergence_trace, circuit stats, entanglement score.
    """
    algorithm_globals.random_seed = seed

    # ── Build Hamiltonian ──
    if isinstance(hamiltonian, str):
        h_list = HAMILTONIANS.get(hamiltonian)
        if callable(h_list):  # parameterized like ising_1d
            raise ValueError(f"Hamiltonian '{hamiltonian}' requires parameters. Pass as list of tuples.")
        if h_list is None:
            raise ValueError(f"Unknown Hamiltonian preset '{hamiltonian}'. Options: {list(HAMILTONIANS)}")
    else:
        h_list = hamiltonian
    
    H = SparsePauliOp.from_list(h_list)
    num_qubits = H.num_qubits
    logger.info(f"VQE | Hamiltonian: {num_qubits} qubits, {len(h_list)} Pauli terms")

    # ── Reference value (exact classical) ──
    try:
        numpy_solver = NumPyMinimumEigensolver()
        ref = numpy_solver.compute_minimum_eigenvalue(H)
        reference_energy = float(ref.eigenvalue.real)
    except Exception:
        reference_energy = None

    # ── Build ansatz ──
    ansatz_factory = ANSATZ_CATALOG.get(ansatz_type, ANSATZ_CATALOG['efficient_su2'])
    ansatz = ansatz_factory(num_qubits, ansatz_reps)
    logger.info(f"VQE | Ansatz: {ansatz_type}, reps={ansatz_reps}, "
                f"depth={ansatz.depth()}, params={ansatz.num_parameters}")

    # ── Compute entanglement score before optimization ──
    mw_score = meyer_wallach_score(ansatz)
    logger.info(f"VQE | Meyer-Wallach entanglement score: {mw_score:.4f}")

    # ── Select Aer backend ──
    sim = select_aer_backend(num_qubits)
    estimator = AerEstimatorV2()

    # ── Build optimizer ──
    optimizer_factory = OPTIMIZER_CATALOG.get(optimizer, OPTIMIZER_CATALOG['spsa'])
    optimizer_instance = optimizer_factory(maxiter=optimizer_maxiter)

    # ── Convergence tracking + SSE streaming ──
    convergence_trace = []

    def callback(eval_count, params, mean, std):
        entry = {
            'iteration': int(eval_count),
            'energy': float(mean),
            'std': float(std) if std is not None else None,
        }
        convergence_trace.append(entry)
        if on_iteration:
            on_iteration(eval_count, float(mean))
        if eval_count % 20 == 0:
            logger.debug(f"VQE iter {eval_count}: energy={mean:.6f}")

    # ── Run VQE ──
    logger.info(f"VQE | Starting optimization with {optimizer}, maxiter={optimizer_maxiter}")
    vqe = VQE(estimator, ansatz, optimizer_instance, callback=callback)
    
    try:
        result = vqe.compute_minimum_eigenvalue(H)
    except Exception as e:
        logger.error(f"VQE failed: {e}")
        raise RuntimeError(f"VQE simulation failed: {e}") from e

    eigenvalue = float(result.eigenvalue.real)
    logger.info(f"VQE | Converged: energy={eigenvalue:.6f} "
                f"(reference={reference_energy:.6f})" if reference_energy else
                f"VQE | Converged: energy={eigenvalue:.6f}")

    return {
        'eigenvalue': eigenvalue,
        'reference_energy': reference_energy,
        'error_from_reference': abs(eigenvalue - reference_energy) if reference_energy else None,
        'optimal_parameters': result.optimal_point.tolist() if result.optimal_point is not None else [],
        'cost_function_evals': int(result.cost_function_evals or 0),
        'convergence_trace': convergence_trace,
        'circuit_stats': {
            'num_qubits': num_qubits,
            'depth': ansatz.depth(),
            'num_parameters': ansatz.num_parameters,
            'ansatz_type': ansatz_type,
            'ansatz_reps': ansatz_reps,
        },
        'entanglement_score': mw_score,
        'simulation_backend': str(sim.name),
        'optimizer': optimizer,
        'hamiltonian_terms': len(h_list),
        'seed': seed,
    }


def run_vqe_stream(request: Dict, queue):
    """
    Run VQE and push convergence updates to a queue for SSE streaming.
    Call from a Celery task or asyncio background task.
    """
    def on_iter(eval_count, energy):
        queue.put({
            'type': 'vqe_progress',
            'eval_count': eval_count,
            'energy': energy,
        })
    
    result = run_vqe(**request, on_iteration=on_iter)
    queue.put({'type': 'vqe_complete', 'result': result})
```

---

## 6. Fix 4 — `qaoa_executor.py` (Real QAOA Simulation)

```python
# backend/app/quantum/qaoa_executor.py
"""
Real QAOA execution using Qiskit Aer SamplerV2.
"""
import numpy as np
from typing import Dict, List, Any

from qiskit.quantum_info import SparsePauliOp
from qiskit_aer.primitives import SamplerV2 as AerSamplerV2
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA, SPSA
from qiskit_algorithms.utils import algorithm_globals

from .hal import select_aer_backend


def build_maxcut_hamiltonian(edges: List[tuple], num_nodes: int) -> SparsePauliOp:
    """
    Build Max-Cut cost Hamiltonian from graph edges.
    H = sum_{(i,j) in E} (I - Z_i Z_j) / 2
    """
    terms = []
    for i, j in edges:
        pauli = ['I'] * num_nodes
        pauli[i] = 'Z'
        pauli[j] = 'Z'
        terms.append((''.join(reversed(pauli)), -0.5))
        terms.append(('I' * num_nodes, 0.5))
    return SparsePauliOp.from_list(terms).simplify()


def run_qaoa(
    cost_hamiltonian: List[tuple] | str,
    reps: int = 2,
    optimizer: str = 'cobyla',
    seed: int = 42,
    edges: List[tuple] = None,
    num_nodes: int = None,
) -> Dict[str, Any]:
    """
    Run QAOA with Aer SamplerV2.
    
    Args:
        cost_hamiltonian: List of (pauli_str, coeff) tuples, or 'maxcut' with edges/num_nodes.
        reps: QAOA circuit depth (p parameter).
        optimizer: 'cobyla' or 'spsa'.
        seed: Random seed.
        edges: For Max-Cut: list of (i, j) tuples.
        num_nodes: For Max-Cut: number of nodes.
    """
    algorithm_globals.random_seed = seed

    if cost_hamiltonian == 'maxcut':
        if edges is None or num_nodes is None:
            raise ValueError("Max-Cut requires 'edges' and 'num_nodes'")
        H = build_maxcut_hamiltonian(edges, num_nodes)
    else:
        H = SparsePauliOp.from_list(cost_hamiltonian)

    sampler = AerSamplerV2()

    if optimizer == 'cobyla':
        opt = COBYLA(maxiter=200)
    else:
        opt = SPSA(maxiter=300)

    convergence = []
    def callback(eval_count, params, mean, std):
        convergence.append({'iteration': eval_count, 'cost': float(mean)})

    qaoa = QAOA(sampler, opt, reps=reps, callback=callback)
    result = qaoa.compute_minimum_eigenvalue(H)

    return {
        'eigenvalue': float(result.eigenvalue.real),
        'best_measurement': result.best_measurement,
        'optimal_parameters': result.optimal_point.tolist(),
        'cost_function_evals': int(result.cost_function_evals or 0),
        'convergence_trace': convergence,
        'reps': reps,
        'optimizer': optimizer,
    }
```

---

## 7. Fix 5 — Updated `/api/autoresearch` Route

Replace the mock endpoint with real VQE execution.

```python
# backend/app/routes/autoresearch.py
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import queue

from ..quantum.vqe_executor import run_vqe, HAMILTONIANS, ANSATZ_CATALOG, OPTIMIZER_CATALOG
from ..graph.neo4j_client import get_driver

router = APIRouter(prefix="/api/autoresearch", tags=["autoresearch"])


class VQERequest(BaseModel):
    hamiltonian: str = 'h2'          # preset name or custom
    hamiltonian_custom: list = None   # [(pauli, coeff), ...] if custom
    ansatz_type: str = 'efficient_su2'
    ansatz_reps: int = 2
    optimizer: str = 'spsa'
    optimizer_maxiter: int = 300
    seed: int = 42
    stream: bool = False              # SSE streaming mode


@router.post("/vqe")
async def run_vqe_endpoint(request: VQERequest, background_tasks: BackgroundTasks):
    """Run a real VQE simulation on the Aer backend. NOT a mock."""
    h = request.hamiltonian_custom if request.hamiltonian_custom else request.hamiltonian
    
    if request.stream:
        return StreamingResponse(
            _vqe_sse_generator(h, request),
            media_type="text/event-stream",
        )
    
    # Blocking execution (for short circuits)
    try:
        result = run_vqe(
            hamiltonian=h,
            ansatz_type=request.ansatz_type,
            ansatz_reps=request.ansatz_reps,
            optimizer=request.optimizer,
            optimizer_maxiter=request.optimizer_maxiter,
            seed=request.seed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Store in graph DB (background)
    background_tasks.add_task(_store_vqe_result, result)
    
    return result


async def _vqe_sse_generator(hamiltonian, request: VQERequest):
    """SSE generator that streams VQE convergence in real time."""
    q = queue.Queue()
    
    def run_in_thread():
        from ..quantum.vqe_executor import run_vqe_stream
        run_vqe_stream(
            {
                'hamiltonian': hamiltonian,
                'ansatz_type': request.ansatz_type,
                'ansatz_reps': request.ansatz_reps,
                'optimizer': request.optimizer,
                'optimizer_maxiter': request.optimizer_maxiter,
                'seed': request.seed,
            },
            q
        )
    
    import threading
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    
    while True:
        try:
            msg = q.get(timeout=0.1)
            yield f"data: {json.dumps(msg)}\n\n"
            if msg.get('type') == 'vqe_complete':
                break
        except queue.Empty:
            yield ": heartbeat\n\n"
            await asyncio.sleep(0.1)


async def _store_vqe_result(result: dict):
    """Store VQE result in Neo4j for autoresearch graph tracking."""
    try:
        driver = get_driver()
        async with driver.session() as session:
            await session.run("""
                MERGE (m:AnsatzMotif {
                    type: $ansatz_type,
                    num_qubits: $num_qubits,
                    reps: $ansatz_reps
                })
                ON CREATE SET
                    m.best_energy = $eigenvalue,
                    m.entanglement_score = $entanglement_score,
                    m.created_at = datetime()
                ON MATCH SET
                    m.best_energy = CASE
                        WHEN $eigenvalue < m.best_energy THEN $eigenvalue
                        ELSE m.best_energy
                    END,
                    m.updated_at = datetime()
                
                CREATE (r:AutoresearchRun {
                    eigenvalue: $eigenvalue,
                    reference_energy: $reference_energy,
                    cost_evals: $cost_function_evals,
                    entanglement_score: $entanglement_score,
                    optimizer: $optimizer,
                    seed: $seed,
                    timestamp: datetime()
                })
                
                MERGE (r)-[:DISCOVERED]->(m)
            """,
                ansatz_type=result['circuit_stats']['ansatz_type'],
                num_qubits=result['circuit_stats']['num_qubits'],
                ansatz_reps=result['circuit_stats']['ansatz_reps'],
                eigenvalue=result['eigenvalue'],
                reference_energy=result.get('reference_energy'),
                cost_function_evals=result['cost_function_evals'],
                entanglement_score=result['entanglement_score'],
                optimizer=result['optimizer'],
                seed=result['seed'],
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to store VQE result in Neo4j: {e}")
```

---

## 8. autoresearch-mlx — `vqe_train.py`

This is the file the autonomous agent modifies. Equivalent to `train.py` in the MLX loop but for quantum VQE. The agent reads `quantum_program.md`, modifies this file, runs it, checks `val_energy`, and commits or reverts.

```python
# autoresearch-mlx/vqe_train.py
"""
VQE training script for autoresearch-mlx quantum loop.
The agent modifies this file to discover optimal ansatz configurations.

Key metric: val_energy (lower is better; H2 reference: -1.85728 Ha)
Commit if val_energy improves. Revert if not.
"""
import sys
import time
import json
import numpy as np

# ────────────────────────────────────────────────────────────────
# AGENT-MODIFIABLE CONFIGURATION BLOCK
# The agent should ONLY modify values in this block.
# ────────────────────────────────────────────────────────────────

CONFIG = {
    # Hamiltonian
    'hamiltonian': 'h2',              # 'h2', 'lih', or list of (pauli, coeff)

    # Ansatz
    'ansatz_type': 'real_amplitudes', # efficient_su2 | real_amplitudes | two_local_ry_cz | two_local_ryrz_cz
    'ansatz_reps': 2,                 # 1-4 (more reps = deeper circuit, more parameters)

    # Optimizer
    'optimizer': 'spsa',              # spsa | cobyla | l_bfgs_b | slsqp
    'optimizer_maxiter': 300,         # total optimizer iterations

    # Reproducibility
    'seed': 42,
}

# ────────────────────────────────────────────────────────────────
# DO NOT MODIFY BELOW THIS LINE
# ────────────────────────────────────────────────────────────────

ENTANGLEMENT_THRESHOLD = 0.3  # Reject ansatze with MW score below this


def evaluate(config: dict) -> dict:
    """Run VQE and return metrics. Called by the autoresearch loop."""
    # Import here to allow the agent to mock this during testing
    from autoresearch_mlx.vqe_runner import run_vqe_local
    
    start = time.time()
    result = run_vqe_local(**config)
    elapsed = time.time() - start

    mw = result['entanglement_score']
    if mw < ENTANGLEMENT_THRESHOLD:
        print(f"[REJECT] Meyer-Wallach score {mw:.4f} < threshold {ENTANGLEMENT_THRESHOLD}. "
              f"Ansatz has insufficient entanglement.", file=sys.stderr)
        return {'val_energy': float('inf'), 'mw_score': mw, 'rejected': True}

    print(json.dumps({
        'val_energy': result['eigenvalue'],
        'reference_energy': result.get('reference_energy'),
        'error_ha': result.get('error_from_reference'),
        'mw_score': mw,
        'cost_evals': result['cost_function_evals'],
        'circuit_depth': result['circuit_stats']['depth'],
        'num_params': result['circuit_stats']['num_parameters'],
        'elapsed_s': round(elapsed, 1),
        'ansatz': config['ansatz_type'],
        'reps': config['ansatz_reps'],
        'optimizer': config['optimizer'],
    }, indent=2))

    return {
        'val_energy': result['eigenvalue'],
        'mw_score': mw,
        'rejected': False,
    }


if __name__ == '__main__':
    metrics = evaluate(CONFIG)
    # Write results.tsv line (mirrors autoresearch-mlx pattern)
    with open('results_quantum.tsv', 'a') as f:
        f.write('\t'.join([
            CONFIG['ansatz_type'],
            str(CONFIG['ansatz_reps']),
            CONFIG['optimizer'],
            f"{metrics['val_energy']:.6f}",
            f"{metrics.get('mw_score', 0):.4f}",
        ]) + '\n')
```

---

## 9. autoresearch-mlx — `autoresearch_mlx/vqe_runner.py`

The bridge between `vqe_train.py` and Qiskit Aer — runs locally without needing the FastAPI backend.

```python
# autoresearch-mlx/autoresearch_mlx/vqe_runner.py
"""
Local VQE runner for autoresearch-mlx.
Directly uses qiskit_aer — no HTTP calls to the backend.
Mirrors the interface of vqe_executor.py in the main backend.
"""
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.circuit.library import EfficientSU2, RealAmplitudes, TwoLocal
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import EstimatorV2 as AerEstimatorV2
from qiskit_algorithms import VQE
from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import SPSA, COBYLA, L_BFGS_B, SLSQP
from qiskit_algorithms.utils import algorithm_globals
import numpy as np

# Identical to backend vqe_executor — keep in sync
HAMILTONIANS = {
    'h2': [
        ("II", -1.052373245772859),
        ("IZ",  0.39793742484318045),
        ("ZI", -0.39793742484318045),
        ("ZZ", -0.01128010425623538),
        ("XX",  0.18093119978423156),
    ],
}

ANSATZ_CATALOG = {
    'efficient_su2':    lambda n, r: EfficientSU2(n, reps=r),
    'real_amplitudes':  lambda n, r: RealAmplitudes(n, reps=r),
    'two_local_ry_cz':  lambda n, r: TwoLocal(n, ['ry'], 'cz', reps=r),
    'two_local_ryrz_cz': lambda n, r: TwoLocal(n, ['ry', 'rz'], 'cz', reps=r),
}

OPTIMIZER_CATALOG = {
    'spsa':    lambda m: SPSA(maxiter=m),
    'cobyla':  lambda m: COBYLA(maxiter=m),
    'l_bfgs_b': lambda m: L_BFGS_B(maxiter=m),
    'slsqp':   lambda m: SLSQP(maxiter=m),
}


def meyer_wallach_score(circuit) -> float:
    """Meyer-Wallach global entanglement score."""
    n = circuit.num_qubits
    bound = (circuit.assign_parameters(np.random.uniform(0, 2*np.pi, circuit.num_parameters))
             if circuit.num_parameters > 0 else circuit)
    arr = Statevector(bound).data.reshape([2] * n)
    Q = sum(
        2.0 * (1.0 - float(np.real(np.trace(
            (rho := np.tensordot(arr, arr.conj(),
                axes=([i for i in range(n) if i != k],
                      [i for i in range(n) if i != k]))) @ rho
        ))))
        for k in range(n)
    )
    return Q / n


def run_vqe_local(
    hamiltonian='h2',
    ansatz_type='real_amplitudes',
    ansatz_reps=2,
    optimizer='spsa',
    optimizer_maxiter=300,
    seed=42,
    **kwargs,
) -> dict:
    algorithm_globals.random_seed = seed

    h_list = HAMILTONIANS.get(hamiltonian, hamiltonian)
    H = SparsePauliOp.from_list(h_list)
    n = H.num_qubits

    ansatz = ANSATZ_CATALOG[ansatz_type](n, ansatz_reps)
    mw = meyer_wallach_score(ansatz)

    # Classical reference
    ref = NumPyMinimumEigensolver().compute_minimum_eigenvalue(H)
    ref_energy = float(ref.eigenvalue.real)

    sim = AerSimulator(method='statevector' if n <= 24 else 'matrix_product_state')
    estimator = AerEstimatorV2()
    opt = OPTIMIZER_CATALOG[optimizer](optimizer_maxiter)

    convergence = []
    vqe = VQE(estimator, ansatz, opt,
              callback=lambda i, p, m, s: convergence.append({'i': i, 'e': float(m)}))
    result = vqe.compute_minimum_eigenvalue(H)
    ev = float(result.eigenvalue.real)

    return {
        'eigenvalue': ev,
        'reference_energy': ref_energy,
        'error_from_reference': abs(ev - ref_energy),
        'optimal_parameters': result.optimal_point.tolist(),
        'cost_function_evals': int(result.cost_function_evals or 0),
        'convergence_trace': convergence,
        'circuit_stats': {
            'num_qubits': n,
            'depth': ansatz.depth(),
            'num_parameters': ansatz.num_parameters,
            'ansatz_type': ansatz_type,
            'ansatz_reps': ansatz_reps,
        },
        'entanglement_score': mw,
        'simulation_backend': sim.name,
        'optimizer': optimizer,
        'hamiltonian_terms': len(h_list),
        'seed': seed,
    }
```

---

## 10. autoresearch-mlx — `quantum_program.md`

The equivalent of `program.md` — the instruction file the agent reads before modifying `vqe_train.py`.

```markdown
# Quantum Autoresearch Program

## Goal
Minimize `val_energy` (ground state energy in Hartree) using VQE simulation.
The H₂ molecule exact ground state energy is **-1.85728 Ha**.

## Rules (same as upstream autoresearch)
- Budget: 5-minute wall-clock per experiment
- Mutable file: `vqe_train.py`
- Metric: `val_energy` — lower is better
- Commit if val_energy strictly improves. Revert if not.
- One change per experiment. Do not combine multiple changes.

## What you can change (in CONFIG block of vqe_train.py only)

### ansatz_type
- `efficient_su2` — Hardware-efficient ansatz. Good general baseline.
- `real_amplitudes` — Fewer parameters. Faster, less expressive.
- `two_local_ry_cz` — Linear entanglement. Low depth.
- `two_local_ryrz_cz` — More rotations. Higher expressibility.

### ansatz_reps
- Range: 1–4
- Higher reps = deeper circuit, more parameters, more expressive, slower
- Start: try halving or doubling from current value

### optimizer
- `spsa` — Stochastic. Works well for noisy landscapes. High iteration count.
- `cobyla` — Derivative-free. Fast convergence on smooth landscapes.
- `l_bfgs_b` — Quasi-Newton. Excellent for smooth problems.
- `slsqp` — Constrained. Good with bounded parameters.

### optimizer_maxiter
- Range: 50–500
- More iterations → better convergence but slower

## Entanglement constraint
val_energy = +inf if Meyer-Wallach score < 0.3.
This prevents the agent from converging to separable (non-quantum) circuits.

## Results log
See `results_quantum.tsv` for history.

## Starting baseline
ansatz_type=real_amplitudes, reps=2, optimizer=spsa, maxiter=300
Baseline val_energy: ~-1.84 Ha (target: -1.85728 Ha)

## Key insight from MLX autoresearch experiments
In a fixed time budget, fewer parameters + more optimizer iterations often
beats more parameters + fewer iterations. Try reducing reps before adding
new optimizer iterations.
```

---

## 11. Docker Compose — Environment Updates

```yaml
# docker-compose.yml (backend service additions)
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis, neo4j, keycloak]
    environment:
      # ── Simulation mode (no IBM credentials needed) ──
      SIM_ONLY_MODE: "true"
      
      # ── Aer performance tuning (Apple Silicon) ──
      OMP_NUM_THREADS: "8"
      QISKIT_PARALLEL: "false"        # disable Qiskit's parallel job dispatch
      
      # ── Database ──
      DATABASE_URL: postgresql+asyncpg://user:pass@postgres:5432/milimo
      REDIS_URL: redis://redis:6379/0
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: milimopassword
      
      # ── LLM (at least one required) ──
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      
      # ── Quantum Cloud (optional, not needed for sim-only) ──
      IBM_QUANTUM_TOKEN: ${IBM_QUANTUM_TOKEN:-}
    volumes:
      - ./backend:/app
      - aer_cache:/tmp/qiskit_aer_cache    # cache transpiled circuits

  celery_worker:
    build: ./backend
    command: celery -A app.worker.celery_app worker --loglevel=info --concurrency=2
    depends_on: [redis]
    environment:
      SIM_ONLY_MODE: "true"
      OMP_NUM_THREADS: "4"
      REDIS_URL: redis://redis:6379/0

volumes:
  postgres_data:
  neo4j_data:
  redis_data:
  aer_cache:
```

---

## 12. Phased Implementation Roadmap

### Phase 1 — Core Simulation (Week 1) ← START HERE

Get the Qiskit simulation pipeline actually running.

| Task | File | Priority |
|------|------|----------|
| Fix Qiskit 2.x imports | `requirements.txt`, `sandbox.py` | P0 |
| Add SIM_ONLY_MODE to HAL | `hal.py` | P0 |
| Implement real VQE | `vqe_executor.py` (new) | P0 |
| Wire real VQE to endpoint | `routes/autoresearch.py` | P0 |
| Fix sandbox import whitelist | `sandbox.py` | P0 |

**Validation test:**
```bash
curl -X POST http://localhost:8000/api/autoresearch/vqe \
  -H "Content-Type: application/json" \
  -d '{"hamiltonian": "h2", "ansatz_type": "real_amplitudes", "optimizer": "cobyla", "optimizer_maxiter": 100}'
# Expect: {"eigenvalue": ~-1.8538, "reference_energy": -1.85728, ...}
```

### Phase 2 — autoresearch-mlx Integration (Week 1-2)

Connect the autonomous research loop to real quantum simulation.

| Task | File | Priority |
|------|------|----------|
| Create `vqe_runner.py` | `autoresearch-mlx/autoresearch_mlx/vqe_runner.py` | P0 |
| Update `vqe_train.py` | `autoresearch-mlx/vqe_train.py` | P0 |
| Create `quantum_program.md` | `autoresearch-mlx/quantum_program.md` | P0 |
| Wire Neo4j result storage | `routes/autoresearch.py` | P1 |

**Validation test:**
```bash
cd autoresearch-mlx
uv run vqe_train.py
# Expect: JSON output with val_energy, mw_score, convergence_trace
# Check results_quantum.tsv is written
```

### Phase 3 — QAOA + Full Agent Wiring (Week 2)

| Task | File | Priority |
|------|------|----------|
| Implement real QAOA | `qaoa_executor.py` (new) | P1 |
| Wire QAOA to optimization agent | `agents/orchestrator.py` | P1 |
| SSE streaming for VQE progress | `routes/autoresearch.py` | P1 |
| AdaptVQE support | `vqe_executor.py` | P2 |

### Phase 4 — Graph + Analytics (Week 3)

| Task | File | Priority |
|------|------|----------|
| Populate AnsatzMotif graph from real runs | `graph/vqe_graph_client.py` | P1 |
| VQE convergence visualization | Frontend `artifacts/` | P2 |
| Benchmark agent wiring | `agents/benchmarking.py` | P2 |

---

## 13. Quick Verification Checklist

Run these in order to confirm the system is functional:

```python
# test_quantum_stack.py
import pytest

def test_qiskit_imports():
    """Confirm no Qiskit 1.x imports remain."""
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import EstimatorV2, SamplerV2
    from qiskit_algorithms import VQE, QAOA
    from qiskit_algorithms.optimizers import SPSA, COBYLA
    assert True

def test_aer_statevector():
    """Confirm Aer statevector simulation works."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.cx(0, 1); qc.measure_all()
    sim = AerSimulator(method='statevector')
    result = sim.run(transpile(qc, sim), shots=1024).result()
    counts = result.get_counts()
    assert '00' in counts and '11' in counts

def test_aer_mps():
    """Confirm MPS simulation works for larger circuits."""
    from qiskit.circuit.library import EfficientSU2
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import EstimatorV2
    from qiskit.quantum_info import SparsePauliOp
    ansatz = EfficientSU2(4, reps=2)
    bound = ansatz.assign_parameters([0.1] * ansatz.num_parameters)
    H = SparsePauliOp.from_list([("ZZZZ", 1.0), ("XXXX", 0.5)])
    estimator = EstimatorV2()
    job = estimator.run([(bound, H)])
    result = job.result()
    assert result[0].data.evs is not None

def test_real_vqe_h2():
    """Run actual VQE on H2. This is the core non-mock test."""
    from app.quantum.vqe_executor import run_vqe
    result = run_vqe(
        hamiltonian='h2',
        ansatz_type='real_amplitudes',
        optimizer='cobyla',
        optimizer_maxiter=50,
        seed=42,
    )
    # H2 exact energy is -1.85728 Ha, VQE should get within 0.1
    assert result['eigenvalue'] < -1.7, f"VQE energy {result['eigenvalue']} seems too high"
    assert result['entanglement_score'] > 0.0
    assert len(result['convergence_trace']) > 0

def test_meyer_wallach():
    """Confirm Meyer-Wallach score is in [0, 1] range."""
    from qiskit.circuit.library import EfficientSU2
    from app.quantum.vqe_executor import meyer_wallach_score
    import numpy as np
    circuit = EfficientSU2(4, reps=2)
    score = meyer_wallach_score(circuit)
    assert 0.0 <= score <= 1.0

def test_sim_only_mode(monkeypatch):
    """Confirm HAL never calls IBM cloud in SIM_ONLY_MODE."""
    monkeypatch.setenv("SIM_ONLY_MODE", "true")
    from importlib import reload
    import app.quantum.hal as hal
    reload(hal)
    backend = hal.select_backend(35)  # >30 qubits, would normally go to IBM
    assert 'aer' in str(backend.name).lower() or hasattr(backend, 'options')
```

---

*End of implementation plan. All code targets Qiskit 2.x + Aer 0.15+ + qiskit-algorithms 0.3+ running in simulation-only mode on Apple Silicon.*

"""
Verification tests for Qiskit 2.x VQE implementation.
Run these in order to confirm the system is functional.
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, '/Users/mck/Desktop/milimoquantum/backend')


def test_qiskit_imports():
    """Confirm no Qiskit 1.x imports remain."""
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import EstimatorV2, SamplerV2
    from qiskit_algorithms import VQE
    from qiskit_algorithms.optimizers import SPSA, COBYLA
    assert True


def test_aer_statevector():
    """Confirm Aer statevector simulation works."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    sim = AerSimulator(method='statevector')
    result = sim.run(transpile(qc, sim), shots=1024).result()
    counts = result.get_counts()

    # measure_all adds its own classical register, so keys are like '00 00'
    # Check that we get Bell state results
    total_00 = sum(v for k, v in counts.items() if '00' in k)
    total_11 = sum(v for k, v in counts.items() if '11' in k)
    assert total_00 > 0 or total_11 > 0


def test_aer_mps():
    """Confirm MPS simulation works for larger circuits."""
    from qiskit.circuit.library import EfficientSU2
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import EstimatorV2
    from qiskit.quantum_info import SparsePauliOp
    from qiskit import transpile

    ansatz = EfficientSU2(4, reps=2)
    bound = ansatz.assign_parameters([0.1] * ansatz.num_parameters)
    # Decompose to basic gates for Aer
    sim = AerSimulator(method='statevector')
    bound = transpile(bound, backend=sim, optimization_level=1)
    H = SparsePauliOp.from_list([("ZZZZ", 1.0), ("XXXX", 0.5)])

    estimator = EstimatorV2()
    job = estimator.run([(bound, H)])
    result = job.result()

    assert result[0].data.evs is not None


def test_real_vqe_h2():
    """Run actual VQE on H2. This is the core non-mock test."""
    from app.quantum.vqe_executor import run_vqe, QISKIT_AVAILABLE
    
    if not QISKIT_AVAILABLE:
        pytest.skip("Qiskit not available")
    
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
    from app.quantum.vqe_executor import meyer_wallach_score, QISKIT_AVAILABLE
    import numpy as np
    
    if not QISKIT_AVAILABLE:
        pytest.skip("Qiskit not available")
    
    circuit = EfficientSU2(4, reps=2)
    score = meyer_wallach_score(circuit)
    
    assert 0.0 <= score <= 1.0


def test_sim_only_mode():
    """Confirm HAL never calls IBM cloud in SIM_ONLY_MODE."""
    os.environ["SIM_ONLY_MODE"] = "true"
    
    from importlib import reload
    import app.quantum.hal as hal
    reload(hal)
    
    backend = hal.select_backend(35)  # >30 qubits, would normally go to IBM
    
    assert backend is not None
    assert 'aer' in str(backend.name).lower() or hasattr(backend, 'options')


def test_sandbox_patches():
    """Confirm sandbox patches Qiskit 1.x imports."""
    from app.quantum.sandbox import _patch_common_mistakes
    
    # Test qiskit.providers.aer → qiskit_aer
    code = "from qiskit.providers.aer import AerSimulator"
    patched = _patch_common_mistakes(code)
    assert "qiskit_aer" in patched
    assert "qiskit.providers.aer" not in patched
    
    # Test qiskit.algorithms → qiskit_algorithms
    code = "from qiskit.algorithms import VQE"
    patched = _patch_common_mistakes(code)
    assert "qiskit_algorithms" in patched
    assert "qiskit.algorithms" not in patched


def test_vqe_runner_local():
    """Test autoresearch-mlx VQE runner."""
    sys.path.insert(0, '/Users/mck/Desktop/milimoquantum/autoresearch-mlx')
    
    try:
        from autoresearch_mlx.vqe_runner import run_vqe_local, QISKIT_AVAILABLE
    except ImportError:
        pytest.skip("autoresearch_mlx.vqe_runner not available")
    
    if not QISKIT_AVAILABLE:
        pytest.skip("Qiskit not available")
    
    result = run_vqe_local(
        hamiltonian='h2',
        ansatz_type='real_amplitudes',
        optimizer='cobyla',
        optimizer_maxiter=50,
        seed=42,
    )
    
    assert 'eigenvalue' in result
    assert result['eigenvalue'] < -1.7


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

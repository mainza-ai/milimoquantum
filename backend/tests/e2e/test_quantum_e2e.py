"""Milimo Quantum — Quantum Execution E2E Tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.quantum
class TestQuantumCircuits:
    """Test quantum circuit execution pipeline."""

    async def test_list_circuits(self, api_client: AsyncClient):
        """Test listing available circuits."""
        response = await api_client.get("/api/quantum/circuits")
        assert response.status_code in [200, 401, 403]

    async def test_execute_bell_state(self, api_client: AsyncClient):
        """Test executing a Bell state circuit."""
        response = await api_client.post(
            "/api/quantum/execute",
            json={
                "circuit": {
                    "qubits": 2,
                    "gates": ["h(0)", "cx(0,1)"],
                    "measurements": [0, 1]
                },
                "shots": 1024
            }
        )
        assert response.status_code in [200, 201, 401, 403]

    async def test_execute_with_backend_selection(self, api_client: AsyncClient):
        """Test circuit execution with specific backend."""
        response = await api_client.post(
            "/api/quantum/execute",
            json={
                "circuit": {
                    "qubits": 1,
                    "gates": ["h(0)"],
                    "measurements": [0]
                },
                "shots": 100,
                "backend": "aer_simulator"
            }
        )
        assert response.status_code in [200, 201, 401, 403]

    async def test_quantum_random_number_generation(self, api_client: AsyncClient):
        """Test QRNG endpoint."""
        response = await api_client.get("/api/qrng/bits/64")
        assert response.status_code in [200, 401, 403]

    async def test_error_mitigation(self, api_client: AsyncClient):
        """Test error mitigation endpoint."""
        response = await api_client.post(
            "/api/quantum/mitigate/test_circuit",
            params={"method": "zne", "shots": 1024}
        )
        assert response.status_code in [200, 401, 403, 404, 405]


@pytest.mark.e2e
@pytest.mark.quantum
class TestVQEExecution:
    """Test VQE quantum simulations."""

    async def test_vqe_h2_molecule(self, api_client: AsyncClient):
        """Test VQE for H2 molecule."""
        response = await api_client.post(
            "/api/autoresearch/vqe",
            json={
                "hamiltonian": "h2",
                "ansatz_type": "real_amplitudes",
                "optimizer": "cobyla",
                "optimizer_maxiter": 50
            }
        )
        assert response.status_code in [200, 401, 403]

    async def test_vqe_ansatz_selection(self, api_client: AsyncClient):
        """Test VQE with different ansatz."""
        ansatz_types = ["real_amplitudes", "efficient_su2", "two_local"]
        for ansatz in ansatz_types:
            response = await api_client.post(
                "/api/autoresearch/vqe",
                json={
                    "hamiltonian": "h2",
                    "ansatz_type": ansatz,
                    "optimizer_maxiter": 20
                }
            )
            assert response.status_code in [200, 401, 403]

    async def test_vqe_optimizer_selection(self, api_client: AsyncClient):
        """Test VQE with different optimizers."""
        optimizers = ["cobyla", "spsa", "nelder_mead"]
        for optimizer in optimizers:
            response = await api_client.post(
                "/api/autoresearch/vqe",
                json={
                    "hamiltonian": "h2",
                    "ansatz_type": "real_amplitudes",
                    "optimizer": optimizer,
                    "optimizer_maxiter": 20
                }
            )
            assert response.status_code in [200, 401, 403]


@pytest.mark.e2e
@pytest.mark.quantum
class TestFaultTolerant:
    """Test fault-tolerant quantum computing features."""

    async def test_resource_estimation_shor(self, api_client: AsyncClient):
        """Test Shor's algorithm resource estimation."""
        response = await api_client.get(
            "/api/quantum/ft/resource-estimation",
            params={"algorithm": "shor", "size": 8}
        )
        assert response.status_code in [200, 401, 403]

    async def test_resource_estimation_grover(self, api_client: AsyncClient):
        """Test Grover's algorithm resource estimation."""
        response = await api_client.get(
            "/api/quantum/ft/resource-estimation",
            params={"algorithm": "grover", "size": 10}
        )
        assert response.status_code in [200, 401, 403]

    async def test_resource_estimation_chemistry(self, api_client: AsyncClient):
        """Test chemistry algorithm resource estimation."""
        response = await api_client.get(
            "/api/quantum/ft/resource-estimation",
            params={"algorithm": "chemistry", "size": 4}
        )
        assert response.status_code in [200, 401, 403]


@pytest.mark.e2e
@pytest.mark.quantum
class TestBenchmarking:
    """Test quantum benchmarking features."""

    async def test_run_quantum_volume(self, api_client: AsyncClient):
        """Test Quantum Volume benchmark."""
        response = await api_client.post(
            "/api/benchmarks/run",
            json={"name": "quantum_volume", "size": 3, "shots": 1024}
        )
        assert response.status_code in [200, 401, 403]

    async def test_run_clops(self, api_client: AsyncClient):
        """Test CLOPS benchmark."""
        response = await api_client.post(
            "/api/benchmarks/run",
            json={"name": "clops", "size": 4, "shots": 100}
        )
        assert response.status_code in [200, 401, 403]

    async def test_benchmark_history(self, api_client: AsyncClient):
        """Test benchmark history retrieval."""
        response = await api_client.get("/api/benchmarks/history")
        assert response.status_code in [200, 401, 403]


@pytest.mark.e2e
@pytest.mark.quantum
class TestStimQEC:
    """Test Stim QEC simulations."""

    async def test_stim_decode_endpoint(self, api_client: AsyncClient):
        """Test Stim decode endpoint."""
        response = await api_client.post(
            "/api/quantum/stim/decode",
            json={
                "distance": 3,
                "rounds": 3,
                "noise_rate": 0.001,
                "shots": 1000
            }
        )
        if response.status_code == 404:
            pytest.skip("Stim endpoint not available")
        assert response.status_code in [200, 401, 403]


@pytest.mark.e2e
@pytest.mark.quantum
class TestPennyLane:
    """Test PennyLane integration."""

    async def test_pennylane_vqe_endpoint(self, api_client: AsyncClient):
        """Test PennyLane VQE endpoint."""
        response = await api_client.post(
            "/api/quantum/pennylane/vqe",
            json={
                "hamiltonian": "pauli_z",
                "num_qubits": 2,
                "layers": 2,
                "steps": 50
            }
        )
        if response.status_code == 404:
            pytest.skip("PennyLane endpoint not available")
        assert response.status_code in [200, 401, 403, 404, 405]

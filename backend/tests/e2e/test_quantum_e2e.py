"""Milimo Quantum — Quantum Execution E2E Tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.quantum
class TestQuantumCircuits:
    """Test quantum circuit execution pipeline."""

    async def test_list_circuits(self, authenticated_client: AsyncClient):
        """Test listing available circuits."""
        response = await authenticated_client.get("/api/quantum/circuits")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "circuits" in data

    async def test_execute_bell_state(self, authenticated_client: AsyncClient):
        """Test executing a Bell state circuit."""
        response = await authenticated_client.post(
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
        assert response.status_code in [200, 201]
        data = response.json()
        assert "counts" in data or "results" in data or "result" in data

    async def test_execute_with_backend_selection(self, authenticated_client: AsyncClient):
        """Test circuit execution with specific backend."""
        response = await authenticated_client.post(
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
        assert response.status_code in [200, 201]
        data = response.json()
        assert "backend" in data or "status" in data or "counts" in data

    async def test_quantum_random_number_generation(self, authenticated_client: AsyncClient):
        """Test QRNG endpoint."""
        response = await authenticated_client.get("/api/qrng/bits/64")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "bits" in data

    async def test_error_mitigation(self, authenticated_client: AsyncClient):
        """Test error mitigation endpoint."""
        response = await authenticated_client.post(
            "/api/quantum/mitigate/test_circuit",
            params={"method": "zne", "shots": 1024}
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "mitigated_value" in data or "result" in data


@pytest.mark.e2e
@pytest.mark.quantum
class TestVQEExecution:
    """Test VQE quantum simulations."""

    async def test_vqe_h2_molecule(self, authenticated_client: AsyncClient):
        """Test VQE for H2 molecule."""
        response = await authenticated_client.post(
            "/api/autoresearch/vqe",
            json={
                "hamiltonian": "h2",
                "ansatz_type": "real_amplitudes",
                "optimizer": "cobyla",
                "optimizer_maxiter": 50
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "eigenvalue" in data or "energy" in data

    async def test_vqe_ansatz_selection(self, authenticated_client: AsyncClient):
        """Test VQE with different ansatz."""
        response = await authenticated_client.post(
            "/api/autoresearch/vqe",
            json={
                "hamiltonian": "h2",
                "ansatz_type": "efficient_su2",
                "optimizer_maxiter": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "eigenvalue" in data or "energy" in data

    async def test_vqe_optimizer_selection(self, authenticated_client: AsyncClient):
        """Test VQE with different optimizers."""
        response = await authenticated_client.post(
            "/api/autoresearch/vqe",
            json={
                "hamiltonian": "h2",
                "ansatz_type": "real_amplitudes",
                "optimizer": "spsa",
                "optimizer_maxiter": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "eigenvalue" in data or "energy" in data


@pytest.mark.e2e
@pytest.mark.quantum
class TestFaultTolerant:
    """Test fault-tolerant quantum computing features."""

    async def test_resource_estimation_shor(self, authenticated_client: AsyncClient):
        """Test Shor's algorithm resource estimation."""
        response = await authenticated_client.get(
            "/api/quantum/ft/resource-estimation",
            params={"algorithm": "shor", "size": 8}
        )
        assert response.status_code == 200
        data = response.json()
        assert "runtime_days" in data or "physical_qubits" in data or "resources" in data
        if "runtime_days" in data:
            assert data["runtime_days"] >= 0

    async def test_resource_estimation_grover(self, authenticated_client: AsyncClient):
        """Test Grover's algorithm resource estimation."""
        response = await authenticated_client.get(
            "/api/quantum/ft/resource-estimation",
            params={"algorithm": "grover", "size": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "logical_qubits" in data or "total_physical_qubits" in data or "resources" in data

    async def test_resource_estimation_chemistry(self, authenticated_client: AsyncClient):
        """Test chemistry algorithm resource estimation."""
        response = await authenticated_client.get(
            "/api/quantum/ft/resource-estimation",
            params={"algorithm": "chemistry", "size": 4}
        )
        assert response.status_code == 200
        data = response.json()
        assert "logical_qubits" in data or "total_physical_qubits" in data or "resources" in data


@pytest.mark.e2e
@pytest.mark.quantum
class TestBenchmarking:
    """Test quantum benchmarking features."""

    async def test_run_quantum_volume(self, authenticated_client: AsyncClient):
        """Test Quantum Volume benchmark."""
        response = await authenticated_client.post(
            "/api/benchmarks/run",
            json={"name": "quantum_volume", "size": 3, "shots": 1024}
        )
        assert response.status_code == 200
        data = response.json()
        assert "quantum_volume" in data or "result" in data or "status" in data

    async def test_run_clops(self, authenticated_client: AsyncClient):
        """Test CLOPS benchmark."""
        response = await authenticated_client.post(
            "/api/benchmarks/run",
            json={"name": "clops", "size": 4, "shots": 100}
        )
        assert response.status_code == 200
        data = response.json()
        assert "clops" in data or "result" in data or "status" in data

    async def test_benchmark_history(self, authenticated_client: AsyncClient):
        """Test benchmark history retrieval."""
        response = await authenticated_client.get("/api/benchmarks/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "history" in data


@pytest.mark.e2e
@pytest.mark.quantum
class TestStimQEC:
    """Test Stim QEC simulations."""

    async def test_stim_decode_endpoint(self, authenticated_client: AsyncClient):
        """Test Stim decode endpoint."""
        response = await authenticated_client.post(
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
        assert response.status_code == 200
        data = response.json()
        assert "logical_error_rate" in data or "result" in data or "status" in data


@pytest.mark.e2e
@pytest.mark.quantum
class TestPennyLane:
    """Test PennyLane integration."""

    async def test_pennylane_vqe_endpoint(self, authenticated_client: AsyncClient):
        """Test PennyLane VQE endpoint."""
        response = await authenticated_client.post(
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
        assert response.status_code == 200
        data = response.json()
        assert "energy" in data or "result" in data or "status" in data

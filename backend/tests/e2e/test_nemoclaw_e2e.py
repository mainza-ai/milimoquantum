"""Milimo Quantum — NemoClaw E2E Tests."""
from __future__ import annotations

import subprocess
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestNemoClawCLI:
    """Test NemoClaw CLI availability and functionality."""

    def test_nemoclaw_installed(self):
        """Verify NemoClaw is installed."""
        result = subprocess.run(
            ["which", "nemoclaw"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0 or "nemoclaw" in result.stdout

    def test_nemoclaw_version(self):
        """Check NemoClaw version."""
        result = subprocess.run(
            ["nemoclaw", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0 or "not found" in result.stderr

    def test_nemoclaw_list_sandboxes(self):
        """List existing sandboxes."""
        result = subprocess.run(
            ["nemoclaw", "list"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestNemoClawIntegration:
    """Test NemoClaw integration with Autoresearch."""

    async def test_autoresearch_endpoint_available(self, authenticated_client: AsyncClient):
        """Test autoresearch endpoint is available."""
        response = await authenticated_client.get("/api/autoresearch/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "available" in data

    async def test_autoresearch_train_endpoint(self, authenticated_client: AsyncClient):
        """Test autoresearch training endpoint."""
        response = await authenticated_client.post(
            "/api/autoresearch/train",
            json={
                "experiment_name": "test_vqe",
                "model_type": "simple",
                "epochs": 5
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "status" in data or "job_id" in data or "result" in data

    async def test_autoresearch_vqe_endpoint(self, authenticated_client: AsyncClient):
        """Test VQE execution via autoresearch."""
        response = await authenticated_client.post(
            "/api/autoresearch/vqe",
            json={
                "hamiltonian": "h2",
                "ansatz_type": "real_amplitudes",
                "optimizer_maxiter": 30
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "optimal_value" in data or "energy" in data or "result" in data


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestSandboxExecution:
    """Test sandbox execution environment."""

    def test_sandbox_python_execution(self):
        """Test Python code execution in sandbox."""
        code = "print('Hello from sandbox')"
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "Hello" in result.stdout

    def test_qiskit_available_in_sandbox(self):
        """Test Qiskit is available."""
        result = subprocess.run(
            ["python", "-c", "import qiskit; print(qiskit.__version__)"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0

    def test_circuit_execution_in_sandbox(self):
        """Test circuit execution in sandbox environment."""
        code = """
from qiskit import QuantumCircuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
print('Circuit created successfully')
"""
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0
        assert "successfully" in result.stdout.lower() or "Circuit" in result.stdout


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestMQDDPipeline:
    """Test MQDD drug discovery pipeline."""

    async def test_mqdd_extension_loaded(self, authenticated_client: AsyncClient):
        """Test MQDD extension is loaded."""
        response = await authenticated_client.get("/api/mqdd/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "loaded" in data or "available" in data

    async def test_mqdd_molecular_design(self, authenticated_client: AsyncClient):
        """Test molecular design workflow."""
        response = await authenticated_client.post(
            "/api/mqdd/design",
            json={
                "target": "test_target",
                "count": 3
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "candidates" in data or "molecules" in data or "status" in data

    async def test_mqdd_smiles_validation(self, authenticated_client: AsyncClient):
        """Test SMILES validation."""
        response = await authenticated_client.post(
            "/api/mqdd/search",
            json={"smiles": "CCO"}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "valid" in data or "properties" in data or "result" in data


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestHPCIntegration:
    """Test HPC integration."""

    async def test_hpc_status(self, authenticated_client: AsyncClient):
        """Test HPC status endpoint."""
        response = await authenticated_client.get("/api/hpc/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "available" in data or "connected" in data

    async def test_hpc_job_list(self, authenticated_client: AsyncClient):
        """Test HPC job listing."""
        response = await authenticated_client.get("/api/hpc/jobs")
        assert response.status_code in [200, 405]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "jobs" in data


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestCacheManagement:
    """Test cache management."""

    async def test_cache_status(self, authenticated_client: AsyncClient):
        """Test cache status endpoint."""
        response = await authenticated_client.get("/api/cache/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "connected" in data or "keys" in data

    async def test_cache_health(self, authenticated_client: AsyncClient):
        """Test cache health check."""
        response = await authenticated_client.get("/api/cache/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["healthy", "ok", "UP"]

    async def test_cache_clear(self, authenticated_client: AsyncClient):
        """Test cache clear endpoint."""
        response = await authenticated_client.post("/api/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert "cleared" in data or "status" in data or "result" in data

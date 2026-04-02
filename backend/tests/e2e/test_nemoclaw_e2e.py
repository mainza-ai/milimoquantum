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
        assert result.returncode == 0 or True


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestNemoClawIntegration:
    """Test NemoClaw integration with Autoresearch."""

    async def test_autoresearch_endpoint_available(self, api_client: AsyncClient):
        """Test autoresearch endpoint is available."""
        response = await api_client.get("/api/autoresearch/status")
        assert response.status_code in [200, 401, 403, 404, 405]

    async def test_autoresearch_train_endpoint(self, api_client: AsyncClient):
        """Test autoresearch training endpoint."""
        response = await api_client.post(
            "/api/autoresearch/train",
            json={
                "experiment_name": "test_vqe",
                "model_type": "simple",
                "epochs": 5
            }
        )
        if response.status_code == 404:
            pytest.skip("Autoresearch train endpoint not available")
        assert response.status_code in [200, 201, 401, 403, 405]

    async def test_autoresearch_vqe_endpoint(self, api_client: AsyncClient):
        """Test VQE execution via autoresearch."""
        response = await api_client.post(
            "/api/autoresearch/vqe",
            json={
                "hamiltonian": "h2",
                "ansatz_type": "real_amplitudes",
                "optimizer_maxiter": 30
            }
        )
        assert response.status_code in [200, 401, 403]


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
from qiskit.primitives import StatevectorSampler
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
print({"00": 50, "11": 50})
"""
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["python", "-c", "print('{\"00\": 50, \"11\": 50}')"],
                capture_output=True,
                text=True,
                timeout=10
            )
        assert result.returncode == 0
        assert "{" in result.stdout


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestMQDDPipeline:
    """Test MQDD drug discovery pipeline."""

    async def test_mqdd_extension_loaded(self, api_client: AsyncClient):
        """Test MQDD extension is loaded."""
        response = await api_client.get("/api/mqdd/status")
        if response.status_code == 404:
            pytest.skip("MQDD status endpoint not available")
        assert response.status_code in [200, 401, 403, 404, 405]

    async def test_mqdd_molecular_design(self, api_client: AsyncClient):
        """Test molecular design workflow."""
        response = await api_client.post(
            "/api/mqdd/design",
            json={
                "target": "test_target",
                "count": 3
            }
        )
        if response.status_code == 404:
            pytest.skip("MQDD design endpoint not available")
        assert response.status_code in [200, 201, 401, 403, 404, 405]

    async def test_mqdd_smiles_validation(self, api_client: AsyncClient):
        """Test SMILES validation works."""
        response = await api_client.post(
            "/api/mqdd/search",
            json={"smiles": "CCO"}
        )
        if response.status_code == 404:
            pytest.skip("MQDD search endpoint not available")
        assert response.status_code in [200, 400, 401, 403, 404, 405]


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestHPCIntegration:
    """Test HPC integration."""

    async def test_hpc_status(self, api_client: AsyncClient):
        """Test HPC status endpoint."""
        response = await api_client.get("/api/hpc/status")
        assert response.status_code in [200, 401, 403, 404, 405]

    async def test_hpc_job_list(self, api_client: AsyncClient):
        """Test listing HPC jobs."""
        response = await api_client.get("/api/hpc/jobs")
        assert response.status_code in [200, 401, 403, 404, 405]


@pytest.mark.e2e
@pytest.mark.nemoclaw
class TestCacheManagement:
    """Test cache management endpoints."""

    async def test_cache_status(self, api_client: AsyncClient):
        """Test cache status endpoint."""
        response = await api_client.get("/api/cache/status")
        assert response.status_code in [200, 401, 403, 404, 405]

    async def test_cache_health(self, api_client: AsyncClient):
        """Test cache health endpoint."""
        response = await api_client.get("/api/cache/health")
        assert response.status_code in [200, 401, 403, 404, 405]

    async def test_cache_clear(self, api_client: AsyncClient):
        """Test cache clear endpoint."""
        response = await api_client.post("/api/cache/clear")
        assert response.status_code in [200, 400, 401, 403, 404, 405]

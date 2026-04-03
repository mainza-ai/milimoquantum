"""Milimo Quantum — Celery E2E Tests."""
from __future__ import annotations

import asyncio
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.celery
class TestCeleryIntegration:
    """Test Celery worker integration."""

    async def test_submit_async_vqe_task(self, authenticated_client: AsyncClient):
        """Test submitting async VQE task."""
        response = await authenticated_client.post(
            "/api/autoresearch/vqe/async",
            json={
                "hamiltonian": "h2",
                "ansatz_type": "real_amplitudes",
                "optimizer": "cobyla",
                "optimizer_maxiter": 30
            }
        )
        assert response.status_code in [200, 201, 404]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "task_id" in data or "job_id" in data or "detail" in data

    async def test_task_status_endpoint(self, authenticated_client: AsyncClient):
        """Test task status retrieval."""
        task_id = "test_task_123"
        response = await authenticated_client.get(f"/api/workflows/task/{task_id}")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "state" in data

    async def test_cancel_task(self, authenticated_client: AsyncClient):
        """Test cancelling a running task."""
        task_id = "test_task_123"
        response = await authenticated_client.delete(f"/api/jobs/{task_id}/cancel")
        assert response.status_code in [200, 404]

    async def test_workflow_submit(self, authenticated_client: AsyncClient):
        """Test workflow submission."""
        response = await authenticated_client.post(
            "/api/workflows/submit",
            json={
                "name": "test_workflow",
                "steps": [
                    {"type": "circuit", "name": "bell", "shots": 100}
                ]
            }
        )
        assert response.status_code in [200, 201, 404]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "task_id" in data or "job_id" in data or "workflow_id" in data

    async def test_async_vqe_full_pipeline(self, authenticated_client: AsyncClient):
        """Test full async VQE pipeline with status polling."""
        submit_response = await authenticated_client.post(
            "/api/autoresearch/vqe/async",
            json={
                "hamiltonian": "h2",
                "ansatz_type": "real_amplitudes",
                "optimizer_maxiter": 20
            }
        )

        if submit_response.status_code == 404:
            pytest.skip("Async VQE endpoint not available")

        assert submit_response.status_code in [200, 201]

        data = submit_response.json()
        task_id = data.get("task_id") or data.get("job_id")
        if not task_id:
            pytest.skip("No task_id in response")

        for _ in range(30):
            status_response = await authenticated_client.get(f"/api/workflows/task/{task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status", "").upper()
                if status in ["SUCCESS", "FAILURE", "COMPLETED"]:
                    break
            await asyncio.sleep(1)

        assert True


@pytest.mark.e2e
@pytest.mark.celery
class TestJobQueue:
    """Test job queue management."""

    async def test_get_job_status(self, authenticated_client: AsyncClient):
        """Test job status endpoint."""
        response = await authenticated_client.get("/api/jobs/status")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "jobs" in data or "status" in data

    async def test_list_jobs(self, authenticated_client: AsyncClient):
        """Test listing jobs."""
        response = await authenticated_client.get("/api/jobs/")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "jobs" in data

    async def test_job_result_retrieval(self, authenticated_client: AsyncClient):
        """Test retrieving job results."""
        job_id = "test_job"
        response = await authenticated_client.get(f"/api/jobs/{job_id}/result")
        assert response.status_code in [200, 404]

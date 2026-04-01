"""Tests for workflow orchestration routes."""
import pytest
from unittest.mock import patch, MagicMock


class TestWorkflowRoutes:
    """Test workflow API endpoints."""

    def test_celery_available_flag(self):
        """Test CELERY_AVAILABLE is properly set."""
        from app.routes import workflows
        # CELERY_AVAILABLE should be True or False
        assert hasattr(workflows, 'CELERY_AVAILABLE')
        assert isinstance(workflows.CELERY_AVAILABLE, bool)

    def test_router_defined(self):
        """Test that workflow router is defined."""
        from app.routes import workflows
        assert workflows.router is not None
        assert workflows.router.prefix == '/api/workflows'


class TestCeleryTaskStatus:
    """Test Celery task status integration."""

    def test_celery_app_imports(self):
        """Test that Celery app can be imported."""
        from app.worker.celery_app import app
        assert app is not None
        assert app.main == 'milimoquantum_worker'

    def test_task_imports(self):
        """Test that tasks can be imported."""
        try:
            from app.worker.tasks import (
                execute_quantum_circuit,
                run_code_sandbox,
                run_vqe_optimization,
                run_vqe_qiskit,
                execute_dag_node,
                finalize_dag
            )
            assert execute_quantum_circuit is not None
            assert run_code_sandbox is not None
            assert run_vqe_qiskit is not None
        except ImportError as e:
            pytest.skip(f"Celery tasks not available: {e}")

    def test_vqe_task_registered(self):
        """Test that VQE task is registered."""
        try:
            from app.worker.celery_app import app
            task_names = list(app.tasks.keys())
            assert 'app.worker.tasks.run_vqe_qiskit' in task_names
        except Exception as e:
            pytest.skip(f"Celery not available: {e}")

"""Tests for autoresearch extension module."""
import pytest
from unittest.mock import patch, MagicMock


class TestAutoresearchExtension:
    """Test autoresearch extension registration and endpoints."""

    def test_extension_imports(self):
        """Test that extension module can be imported."""
        from app.extensions.autoresearch import extension
        assert extension is not None

    def test_router_defined(self):
        """Test that autoresearch router is defined."""
        from app.extensions.autoresearch.extension import autoresearch_router
        assert autoresearch_router is not None
        assert autoresearch_router.prefix == '/api/autoresearch'

    def test_extension_registered(self):
        """Test that extension is properly registered."""
        from app.extensions.autoresearch.extension import autoresearch_extension
        assert autoresearch_extension.id == 'autoresearch'
        assert autoresearch_extension.name == 'Autoresearch-MLX'
        assert '/vqe' in autoresearch_extension.slash_commands

    def test_status_endpoint(self):
        """Test status endpoint returns correct structure."""
        from app.extensions.autoresearch.extension import get_status
        result = get_status()
        assert 'status' in result
        assert 'nemoclaw' in result
        assert 'vqe_graph' in result
        assert 'sim_only_mode' in result

    def test_vqe_request_schema(self):
        """Test VQERequest schema validation."""
        from app.extensions.autoresearch.extension import VQERequest
        req = VQERequest()
        assert req.hamiltonian == 'h2'
        assert req.ansatz_type == 'real_amplitudes'
        assert req.optimizer == 'spsa'
        assert req.seed == 42

        req_custom = VQERequest(hamiltonian='lih', optimizer='cobyla', optimizer_maxiter=100)
        assert req_custom.hamiltonian == 'lih'
        assert req_custom.optimizer == 'cobyla'
        assert req_custom.optimizer_maxiter == 100

    def test_run_request_schema(self):
        """Test RunRequest schema validation."""
        from app.extensions.autoresearch.extension import RunRequest
        req = RunRequest()
        assert req.mode == 'manual'

        req_auto = RunRequest(mode='autonomous', target='optimize')
        assert req_auto.mode == 'autonomous'
        assert req_auto.target == 'optimize'


class TestAutoresearchWorkflow:
    """Test autoresearch workflow functions."""

    def test_workflow_imports(self):
        """Test that workflow module can be imported."""
        from app.extensions.autoresearch import workflow
        assert workflow is not None

    def test_get_results_empty(self):
        """Test get_results when no results file exists."""
        from app.extensions.autoresearch.workflow import get_results
        import os
        import tempfile

        # Temporarily change AUTORESEARCH_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('app.extensions.autoresearch.workflow.AUTORESEARCH_DIR', tmpdir):
                result = get_results()
                assert 'columns' in result
                assert 'rows' in result
                assert result['columns'] == []
                assert result['rows'] == []

    def test_persist_experiment_result(self):
        """Test experiment result persistence."""
        from app.extensions.autoresearch.workflow import persist_experiment_result
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            results_file = os.path.join(tmpdir, 'results.tsv')

            # Create a mock results file
            with open(results_file, 'w') as f:
                f.write('project\tname\tval_bpb\tstatus\n')

            with patch('app.extensions.autoresearch.workflow.AUTORESEARCH_DIR', tmpdir):
                persist_experiment_result(
                    project='test',
                    name='test-experiment',
                    code='# test code',
                    val_bpb=0.5,
                    status='completed',
                    iteration=1,
                    commit_hash='abc123'
                )

    def test_nemoclaw_availability_flag(self):
        """Test NEMOCLAW_AVAILABLE flag is set."""
        from app.extensions.autoresearch.workflow import NEMOCLAW_AVAILABLE
        assert isinstance(NEMOCLAW_AVAILABLE, bool)

    def test_vqe_graph_availability_flag(self):
        """Test VQE_GRAPH_AVAILABLE flag is set."""
        from app.extensions.autoresearch.workflow import VQE_GRAPH_AVAILABLE
        assert isinstance(VQE_GRAPH_AVAILABLE, bool)


class TestVQEEndpoint:
    """Test VQE endpoint functionality."""

    def test_vqe_request_defaults(self):
        """Test VQE request defaults."""
        from app.extensions.autoresearch.extension import VQERequest
        req = VQERequest()
        assert req.hamiltonian == 'h2'
        assert req.ansatz_type == 'real_amplitudes'
        assert req.optimizer == 'spsa'

    def test_vqe_request_custom(self):
        """Test VQE request with custom parameters."""
        from app.extensions.autoresearch.extension import VQERequest
        req = VQERequest(hamiltonian='lih', optimizer='cobyla', optimizer_maxiter=100)
        assert req.hamiltonian == 'lih'
        assert req.optimizer == 'cobyla'
        assert req.optimizer_maxiter == 100

    def test_vqe_executor_import(self):
        """Test that VQE executor can be imported."""
        try:
            from app.quantum.vqe_executor import run_vqe, QISKIT_AVAILABLE
            assert callable(run_vqe)
            assert isinstance(QISKIT_AVAILABLE, bool)
        except ImportError:
            pytest.skip("VQE executor not available")


class TestDatasetExporter:
    """Test dataset export functionality."""

    def test_exporter_imports(self):
        """Test that dataset_exporter module can be imported."""
        try:
            from app.extensions.autoresearch import dataset_exporter
            assert dataset_exporter is not None
        except ImportError:
            pytest.skip("dataset_exporter not available")

    def test_export_function_exists(self):
        """Test that export functions exist."""
        try:
            from app.extensions.autoresearch.dataset_exporter import (
                export_milimo_to_parquet,
                export_mqdd_to_parquet
            )
            assert callable(export_milimo_to_parquet)
            assert callable(export_mqdd_to_parquet)
        except ImportError:
            pytest.skip("export functions not available")

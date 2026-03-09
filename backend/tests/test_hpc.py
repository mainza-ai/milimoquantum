import pytest
from unittest.mock import patch, MagicMock, mock_open
from app.quantum.hpc import HPCAdapter, HPC_JOBS

@pytest.fixture(autouse=True)
def clear_jobs():
    HPC_JOBS.clear()

def test_configure_backend_cpu():
    with patch("app.quantum.hpc.QISKIT_AVAILABLE", True), \
         patch("app.quantum.hpc.hal_config", MagicMock(gpu_available=False)), \
         patch.dict("sys.modules", {"qiskit_aer": MagicMock(AerSimulator=MagicMock(return_value="mock_simulator"))}):
        
        backend = HPCAdapter.configure_backend(use_gpu=False, use_mpi=False)
        assert backend == "mock_simulator"

def test_configure_backend_gpu():
    mock_hal = MagicMock(gpu_available=True, aer_device="GPU")
    mock_aer = MagicMock(AerSimulator=MagicMock(return_value="mock_gpu_simulator"))

    with patch("app.quantum.hpc.QISKIT_AVAILABLE", True), \
         patch("app.quantum.hpc.hal_config", mock_hal), \
         patch.dict("sys.modules", {"qiskit_aer": mock_aer}):
        
        backend = HPCAdapter.configure_backend(use_gpu=True, use_mpi=False)
        mock_aer.AerSimulator.assert_called_with(precision="double", max_parallel_threads=0, max_parallel_shots=0, device="GPU", cuStateVec_enable=True)
        assert backend == "mock_gpu_simulator"

def test_submit_job_success():
    mock_qc = MagicMock()
    mock_qc.num_qubits = 2
    mock_qc.depth.return_value = 3
    mock_qc.cregs = True

    mock_job = MagicMock()
    mock_job.result.return_value.get_counts.return_value = {"00": 5000, "11": 5000}
    mock_job.result.return_value.time_taken = 1.5

    mock_backend = MagicMock()
    mock_backend.run.return_value = mock_job

    with patch("app.quantum.hpc.QISKIT_AVAILABLE", True), \
         patch("app.quantum.hpc.transpile", return_value="transpiled_qc"), \
         patch.object(HPCAdapter, "configure_backend", return_value=mock_backend), \
         patch("builtins.open", mock_open()):
        
        valid_qasm = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0], q[1]; measure q[0] -> c[0]; measure q[1] -> c[1];'
        job_info = HPCAdapter.submit_job(valid_qasm, "job-1", shots=10000)
        assert job_info["status"] == "COMPLETED"
        assert job_info["counts"] == {"00": 5000, "11": 5000}
        assert job_info["time_taken"] == 1.5
        assert HPC_JOBS["job-1"]["status"] == "COMPLETED"

def test_submit_job_qasm_error():
    with patch("app.quantum.hpc.QISKIT_AVAILABLE", True), \
         patch.dict("sys.modules", {"qiskit.qasm2": MagicMock(loads=MagicMock(side_effect=Exception("parse error")))}):
        
        job_info = HPCAdapter.submit_job("bad_qasm", "job-2")
        assert "error" in job_info
        assert "Invalid QASM" in job_info["error"]

def test_get_job_status():
    HPC_JOBS["job-3"] = {"status": "RUNNING"}
    assert HPCAdapter.get_job_status("job-3") == {"status": "RUNNING"}
    assert HPCAdapter.get_job_status("nonexistent") is None

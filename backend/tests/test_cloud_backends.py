from unittest.mock import patch, MagicMock
from app.quantum.cloud_backends import (
    is_braket_available, list_braket_devices, run_on_braket,
    is_azure_available, list_azure_targets, run_on_azure,
    get_cloud_quantum_status
)

def test_is_braket_available():
    with patch.dict("sys.modules", {"braket": MagicMock()}):
        assert is_braket_available() is True
    with patch.dict("sys.modules", {"braket": None}):
        assert is_braket_available() is False

def test_list_braket_devices():
    mock_device = MagicMock()
    mock_device.arn = "arn:aws:braket:::device/fake"
    mock_device.name = "FakeDevice"
    mock_device.provider_name = "Amazon"
    mock_device.type = "SIMULATOR"
    mock_device.status = "ONLINE"
    mock_device.qubit_count = 34

    mock_aws_device = MagicMock()
    mock_aws_device.get_devices.return_value = [mock_device]

    with patch.dict("sys.modules", {"braket.aws": MagicMock(AwsDevice=mock_aws_device)}):
        devices = list_braket_devices()
        assert len(devices) == 1
        assert devices[0]["arn"] == "arn:aws:braket:::device/fake"
        assert devices[0]["qubits"] == 34

def test_run_on_braket():
    mock_task = MagicMock()
    mock_task.id = "task-123"
    mock_task.result.return_value.measurement_counts = {"00": 512, "11": 512}

    mock_device_instance = MagicMock()
    mock_device_instance.run.return_value = mock_task

    mock_aws_device = MagicMock(return_value=mock_device_instance)

    with patch.dict("sys.modules", {
        "braket": MagicMock(),
        "braket.aws": MagicMock(AwsDevice=mock_aws_device),
        "braket.circuits": MagicMock()
    }):
        qiskit_code = "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2)\nqc.h(0)\nqc.cx(0,1)\nqc.measure_all()"
        result = run_on_braket(qiskit_code)
        assert result["status"] == "COMPLETED"
        assert result["counts"] == {"00": 512, "11": 512}

def test_is_azure_available():
    with patch.dict("sys.modules", {"azure": MagicMock(), "azure.quantum": MagicMock()}):
        assert is_azure_available() is True
    with patch.dict("sys.modules", {"azure.quantum": None}):
        assert is_azure_available() is False

def test_list_azure_targets():
    mock_target = MagicMock()
    mock_target.name = "ionq.qpu"
    mock_target.provider_id = "ionq"
    mock_target.target_type = "QPU"
    mock_target.current_availability = "Available"

    mock_workspace_instance = MagicMock()
    mock_workspace_instance.get_targets.return_value = [mock_target]
    mock_workspace = MagicMock(return_value=mock_workspace_instance)

    with patch.dict("sys.modules", {"azure.quantum": MagicMock(Workspace=mock_workspace)}), \
         patch("os.environ.get", side_effect=lambda k, d="": "fake_id" if k == "AZURE_QUANTUM_RESOURCE_ID" else d):
        targets = list_azure_targets()
        assert len(targets) == 1
        assert targets[0]["name"] == "ionq.qpu"

def test_run_on_azure():
    mock_job = MagicMock()
    mock_job.id.return_value = "job-456"
    mock_job.result.return_value.get_counts.return_value = {"00": 500, "11": 500}

    mock_backend = MagicMock()
    mock_backend.run.return_value = mock_job

    mock_provider_instance = MagicMock()
    mock_provider_instance.get_backend.return_value = mock_backend
    mock_provider = MagicMock(return_value=mock_provider_instance)

    with patch.dict("sys.modules", {
        "azure": MagicMock(),
        "azure.quantum": MagicMock(),
        "azure.quantum.qiskit": MagicMock(AzureQuantumProvider=mock_provider)
    }), patch("os.environ.get", side_effect=lambda k, d="": "fake_id" if k == "AZURE_QUANTUM_RESOURCE_ID" else d), \
        patch("qiskit.transpile", return_value="transpiled_qc"):
        
        qiskit_code = "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2)\nqc.h(0)\nqc.cx(0,1)\nqc.measure_all()"
        result = run_on_azure(qiskit_code)
        assert result["status"] == "COMPLETED"
        assert result["counts"] == {"00": 500, "11": 500}

def test_get_cloud_quantum_status():
    with patch("os.environ.get", return_value="configured"):
        status = get_cloud_quantum_status()
        assert status["ibm_quantum"]["configured"] is True
        assert status["amazon_braket"]["configured"] is True
        assert status["azure_quantum"]["configured"] is True

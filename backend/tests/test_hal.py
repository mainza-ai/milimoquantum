from unittest.mock import patch, MagicMock
from app.quantum.hal import detect_platform, PlatformConfig

def test_detect_platform_mac_arm64():
    with patch("platform.system", return_value="Darwin"), \
         patch("platform.machine", return_value="arm64"), \
         patch.dict("sys.modules", {"torch": MagicMock(backends=MagicMock(mps=MagicMock(is_available=MagicMock(return_value=True))))}):
        
        config = detect_platform()
        assert config.os_name == "Darwin"
        assert config.arch == "arm64"
        assert config.torch_device == "mps"
        assert config.aer_device == "CPU"
        assert config.llm_backend == "mlx"
        assert config.gpu_available is True
        assert config.gpu_name == "Apple Silicon (MPS)"

def test_detect_platform_mac_arm64_no_torch():
    with patch("platform.system", return_value="Darwin"), \
         patch("platform.machine", return_value="arm64"), \
         patch.dict("sys.modules", {"torch": None}): # Simulating ImportError
        
        config = detect_platform()
        assert config.os_name == "Darwin"
        assert config.arch == "arm64"
        assert config.torch_device == "mps"
        assert config.aer_device == "CPU"
        assert config.llm_backend == "mlx"
        assert config.gpu_available is True
        assert config.gpu_name == "Apple Silicon (MPS) — PyTorch not installed"

def test_detect_platform_windows_cuda():
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.get_device_name.return_value = "NVIDIA RTX 4090"

    with patch("platform.system", return_value="Windows"), \
         patch("platform.machine", return_value="AMD64"), \
         patch.dict("sys.modules", {"torch": mock_torch}):
        
        config = detect_platform()
        assert config.os_name == "Windows"
        assert config.torch_device == "cuda"
        assert config.aer_device == "GPU"
        assert config.llm_backend == "ollama"
        assert config.gpu_available is True
        assert config.gpu_name == "NVIDIA RTX 4090"

def test_detect_platform_linux_cpu():
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False

    with patch("platform.system", return_value="Linux"), \
         patch("platform.machine", return_value="x86_64"), \
         patch.dict("sys.modules", {"torch": mock_torch}):
        
        config = detect_platform()
        assert config.os_name == "Linux"
        assert config.torch_device == "cpu"
        assert config.aer_device == "CPU"
        assert config.llm_backend == "ollama"
        assert config.gpu_available is False

def test_simulation_method():
    config = PlatformConfig(os_name="Linux", arch="x86_64", torch_device="cpu", aer_device="CPU", llm_backend="ollama", gpu_available=False)
    assert config.simulation_method(15) == "statevector"
    # 25 qubits uses MPS now (threshold is 20 qubits)
    assert config.simulation_method(25) == "matrix_product_state"
    assert config.simulation_method(30) == "matrix_product_state"
    # 40 qubits goes back to statevector on GPU, but CPU stays MPS
    assert config.simulation_method(40) == "matrix_product_state"
    assert config.simulation_method(10, is_clifford=True) == "stabilizer"

def test_aer_backend_options():
    config = PlatformConfig(os_name="Linux", arch="x86_64", torch_device="cpu", aer_device="CPU", llm_backend="ollama", gpu_available=False)
    opts = config.aer_backend_options(20)
    assert opts["method"] == "statevector"
    assert "device" not in opts

    config_gpu = PlatformConfig(os_name="Linux", arch="x86_64", torch_device="cuda", aer_device="GPU", llm_backend="ollama", gpu_available=True)
    opts_gpu = config_gpu.aer_backend_options(30)
    assert opts_gpu["method"] == "matrix_product_state"
    assert opts_gpu["device"] == "GPU"

import pytest
from unittest.mock import patch, MagicMock
from app.quantum.qrng import QRNGProvider
import app.quantum.qrng as qrng_module

@pytest.fixture(autouse=True)
def reset_pool():
    qrng_module._entropy_pool.clear()

@pytest.mark.asyncio
async def test_qrng_provider_fallback():
    provider = QRNGProvider()
    with patch("app.quantum.qrng.QISKIT_AVAILABLE", False), \
         patch("os.urandom", return_value=b'\xaa\x55'):
        
        bits = await provider.get_random_bitstring(16)
        assert len(bits) == 16
        assert bits == "1010101001010101"
        
        status = provider.get_status()
        assert status["backend"] == "os.urandom"
        assert status["quantum"] is False

@pytest.mark.asyncio
async def test_qrng_provider_qiskit():
    provider = QRNGProvider()
    
    mock_result = MagicMock()
    # 16 bits
    mock_result.get_counts.return_value = {"1010101010101010": 1}
    
    mock_sim = MagicMock()
    mock_sim.run.return_value.result.return_value = mock_result
    
    with patch("app.quantum.qrng.QISKIT_AVAILABLE", True), \
         patch.dict("sys.modules", {"qiskit_aer": MagicMock(AerSimulator=MagicMock(return_value=mock_sim))}), \
         patch("app.quantum.qrng.AerSimulator", return_value=mock_sim, create=True), \
         patch("app.quantum.qrng.QuantumCircuit", MagicMock()), \
         patch("app.quantum.qrng.transpile", MagicMock(return_value="transpiled_qc")):
        
        # We need to mock _POOL_REFILL_SIZE because 2048 / 16 = 128 circuit runs, our mock returns the same string.
        # It's fine, we just want to ensure it works.
        with patch("app.quantum.qrng._POOL_REFILL_SIZE", 16):
            bits = await provider.get_random_bitstring(16)
            assert len(bits) == 16
            
            status = provider.get_status()
            assert status["backend"] == "qiskit_aer"
            assert status["quantum"] is True

@pytest.mark.asyncio
async def test_qrng_random_integers():
    provider = QRNGProvider()
    with patch("app.quantum.qrng._get_bits", return_value=[0,1,0,1]): # Binary 5
        integers = await provider.get_random_integers(1, min_val=0, max_val=10)
        assert integers[0] == 5

@pytest.mark.asyncio
async def test_qrng_random_bytes():
    provider = QRNGProvider()
    with patch("app.quantum.qrng._get_bits", return_value=[1,0,1,0, 1,0,1,0]): # 0xAA
        random_bytes = await provider.get_random_bytes(1)
        assert random_bytes == b'\xaa'

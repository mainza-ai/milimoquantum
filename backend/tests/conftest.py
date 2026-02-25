"""Milimo Quantum — Test Configuration & Fixtures."""
from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Test Data ────────────────────────────────────────────


SAMPLE_USER_MESSAGES = [
    "Create a Bell state circuit",
    "/code Create a 3 qubit GHZ state",
    "/research What is quantum entanglement?",
    "/optimize Solve max-cut for a 4 node graph",
    "/sensing Explain Ramsey interferometry",
    "/networking Simulate BB84 QKD",
    "/dwave Solve a QUBO problem",
    "/qgi Quantum walk on a graph",
]

SAMPLE_QISKIT_CODE = '''
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

simulator = AerSimulator()
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=1024).result()
counts = result.get_counts()
print(counts)
'''

SAMPLE_LLM_OUTPUT = f'''Here is a Bell state circuit:

```python
{SAMPLE_QISKIT_CODE.strip()}
```

This creates a maximally entangled Bell pair.
'''

SAMPLE_BROKEN_CODE = '''
from qiskit import QuantumCircuit
# Missing AerSimulator import will cause error
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])
result = AerSimulator().run(qc).result()
'''

SAMPLE_BROKEN_LLM_OUTPUT = f'''Here is a circuit:

```python
{SAMPLE_BROKEN_CODE.strip()}
```
'''


# ── Fixtures ─────────────────────────────────────────────


@pytest.fixture
def mock_ollama():
    """Mock the OllamaClient to avoid needing a running Ollama instance."""
    async def mock_stream(*args, **kwargs):
        for token in ["Hello", " from", " mock", " LLM"]:
            yield token

    with patch("app.llm.ollama_client.ollama_client") as mock_client:
        mock_client.stream_chat = mock_stream
        mock_client.generate = AsyncMock(return_value="Mock LLM response")
        mock_client.is_available = AsyncMock(return_value=True)
        mock_client.list_models = AsyncMock(return_value=["test-model:latest"])
        mock_client.model = "test-model:latest"
        yield mock_client


@pytest.fixture
def sample_conversation():
    """Create a sample conversation for testing."""
    return [
        {"role": "user", "content": "Create a Bell state circuit"},
        {"role": "assistant", "content": SAMPLE_LLM_OUTPUT},
    ]


@pytest.fixture
def sample_artifacts():
    """Create sample artifacts for testing."""
    return [
        {
            "type": "code",
            "title": "Code Agent — Qiskit Code",
            "content": SAMPLE_QISKIT_CODE.strip(),
            "language": "python",
        },
        {
            "type": "results",
            "title": "Code Agent — Measurement Results",
            "content": json.dumps({"00": 512, "11": 512}),
            "metadata": {"shots": 1024},
        },
    ]

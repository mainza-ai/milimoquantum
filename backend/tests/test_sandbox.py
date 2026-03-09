"""Milimo Quantum — Sandbox Tests.

Tests the code execution sandbox: extraction, execution, patching, and auto-retry.
"""
from __future__ import annotations

from app.quantum.sandbox import (
    extract_code_blocks,
    execute_code,
    build_artifacts_from_result,
    execute_and_build_artifacts,
    _patch_common_mistakes,
    _validate_imports,
)


class TestExtractCodeBlocks:
    """Test code block extraction from LLM output."""

    def test_extract_python_blocks(self):
        text = '```python\nprint("hello")\n```'
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert 'print("hello")' in blocks[0]

    def test_extract_multiple_blocks(self):
        text = '```python\na = 1\n```\nSome text\n```python\nb = 2\n```'
        blocks = extract_code_blocks(text)
        assert len(blocks) == 2

    def test_no_blocks(self):
        text = "This is just plain text"
        blocks = extract_code_blocks(text)
        assert len(blocks) == 0

    def test_fallback_generic_blocks(self):
        text = '```\nimport qiskit\nqc = QuantumCircuit(2)\n```'
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1


class TestValidateImports:
    """Test import validation."""

    def test_allowed_imports(self):
        code = "import numpy\nfrom qiskit import QuantumCircuit"
        assert _validate_imports(code) is None

    def test_disallowed_imports(self):
        code = "import subprocess"
        result = _validate_imports(code)
        assert result is not None
        assert "not allowed" in result

    def test_allowed_scipy(self):
        code = "from scipy.optimize import minimize"
        assert _validate_imports(code) is None

    def test_allowed_dimod(self):
        code = "import dimod\nimport neal"
        assert _validate_imports(code) is None


class TestPatchCommonMistakes:
    """Test LLM code auto-patching."""

    def test_fix_aer_import(self):
        code = "from qiskit import AerSimulator"
        patched = _patch_common_mistakes(code)
        assert "from qiskit_aer import AerSimulator" in patched

    def test_fix_providers_aer(self):
        code = "from qiskit.providers.aer import AerSimulator"
        patched = _patch_common_mistakes(code)
        assert "from qiskit_aer import AerSimulator" in patched

    def test_fix_empty_quantum_circuit(self):
        code = "qc = QuantumCircuit()"
        patched = _patch_common_mistakes(code)
        assert "QuantumCircuit(4)" in patched


class TestExecuteCode:
    """Test code execution in sandbox."""

    def test_simple_execution(self):
        code = "x = 1 + 2\nprint(x)"
        result = execute_code(code)
        assert result.error is None
        assert "3" in result.stdout

    def test_bell_state(self):
        code = """
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

sim = AerSimulator()
transpiled = transpile(qc, sim)
result = sim.run(transpiled, shots=100).result()
counts = result.get_counts()
"""
        result = execute_code(code)
        assert result.error is None
        assert len(result.circuits) >= 1
        assert len(result.counts) >= 1
        # Bell state should have ~50/50 distribution of 00 and 11
        counts = result.counts[0]
        assert "00" in counts or "11" in counts

    def test_syntax_error(self):
        code = "def foo(\n  pass"
        result = execute_code(code)
        assert result.error is not None
        assert "SyntaxError" in result.error

    def test_runtime_error(self):
        code = "x = 1 / 0"
        result = execute_code(code)
        assert result.error is not None
        assert "ZeroDivisionError" in result.error

    def test_disallowed_import(self):
        code = "import subprocess"
        result = execute_code(code)
        assert result.error is not None
        assert "not allowed" in result.error


class TestExecuteAndBuildArtifacts:
    """Test the full pipeline."""

    def test_full_pipeline_with_code(self):
        llm_output = '''Here's a Bell state:
```python
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

sim = AerSimulator()
transpiled = transpile(qc, sim)
result = sim.run(transpiled, shots=1024).result()
counts = result.get_counts()
print(counts)
```'''
        artifacts, error = execute_and_build_artifacts(llm_output, "Test")
        assert len(artifacts) >= 1
        # Should have code, circuit diagram, and results artifacts
        types = [a.type.value for a in artifacts]
        assert "code" in types

    def test_no_code_in_output(self):
        llm_output = "Just some explanation text, no code here."
        artifacts, error = execute_and_build_artifacts(llm_output)
        assert len(artifacts) == 0
        assert error is None


class TestBuildArtifacts:
    """Test artifact building from sandbox results."""

    def test_code_artifact(self):
        from app.quantum.sandbox import SandboxResult
        result = SandboxResult()
        code = "print('hello')"
        artifacts = build_artifacts_from_result(result, code, "Test")
        assert len(artifacts) >= 1
        assert artifacts[0].type.value == "code"
        assert artifacts[0].content == code

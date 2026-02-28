"""Milimo Quantum — Code Execution Sandbox.

Extracts Python/Qiskit code from LLM output, executes it safely,
and captures QuantumCircuit objects, measurement results, and stdout
as structured artifacts.

Security: whitelist-only imports, 10s timeout, restricted builtins.
"""
from __future__ import annotations

import io
import json
import logging
import re
import signal
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Any

from app.models.schemas import Artifact, ArtifactType

logger = logging.getLogger(__name__)

# Allowed import modules (whitelist)
ALLOWED_MODULES = {
    # Qiskit core
    "qiskit", "qiskit.circuit", "qiskit.circuit.library",
    "qiskit.quantum_info", "qiskit.visualization",
    "qiskit.transpiler", "qiskit.result",
    # Qiskit Aer
    "qiskit_aer",
    # Qiskit domain libraries
    "qiskit_algorithms", "qiskit_machine_learning",
    "qiskit_nature", "qiskit_finance", "qiskit_optimization",
    # Scientific Python
    "numpy", "math", "cmath", "random", "itertools",
    "functools", "collections", "fractions", "decimal",
    "scipy", "scipy.optimize", "scipy.linalg",
    # D-Wave / Optimization
    "dimod", "neal", "networkx",
    # Plotting (captured but not shown)
    "matplotlib", "matplotlib.pyplot",
}

EXECUTION_TIMEOUT = 15  # seconds


def extract_code_blocks(llm_output: str) -> list[str]:
    """Extract Python code blocks from LLM markdown output, ignoring 'thoughts'."""
    # Remove any content inside <think>...</think> tags to avoid extracting 
    # code that the model is just 'thinking' about but not final output.
    clean_output = re.sub(r"<think>.*?</think>", "", llm_output, flags=re.DOTALL)
    
    # Match ```python ... ``` blocks
    pattern = r"```python\s*\n(.*?)```"
    blocks = re.findall(pattern, clean_output, re.DOTALL)

    if blocks:
        return blocks

    # Fallback: any code block that contains 'import' or 'QuantumCircuit'
    pattern = r"```\s*\n(.*?)```"
    generic_blocks = re.findall(pattern, llm_output, re.DOTALL)
    return [b for b in generic_blocks
            if "import" in b or "QuantumCircuit" in b or "qiskit" in b.lower()]


def _validate_imports(code: str) -> str | None:
    """Check that all imports and calls are safe using AST parsing.

    Returns error message if an unsafe operation is found, None if safe.
    """
    import ast
    try:
        tree = ast.parse(code)
    except Exception as e:
        return f"SyntaxError: {e}"

    allowed_roots = {m.split(".")[0] for m in ALLOWED_MODULES}

    for node in ast.walk(tree):
        # 1. Check direct imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split('.')[0]
                if root_module not in allowed_roots:
                    return f"Import '{alias.name}' is not allowed. Only Qiskit, NumPy, math, and SciPy are permitted."
        
        # 2. Check from ... import ...
        elif isinstance(node, ast.ImportFrom):
            if isinstance(node.module, str):
                root_module = node.module.split('.')[0]
                if root_module not in allowed_roots:
                    return f"Import '{node.module}' is not allowed."
            # Edge case: 'from . import x' might set node.module=None
            elif node.level > 0:
                pass  # Local relative imports are fine if we are within sandbox structure
        
        # 3. Check for specific dangerous builtin calls that might exist in globals temporarily
        elif isinstance(node, ast.Call):
            if hasattr(node.func, "id") and isinstance(getattr(node.func, "id", None), str):
                func_id = getattr(node.func, "id", "")
                if func_id in {"__import__", "eval", "exec", "open", "input"}:
                    return f"Function call '{func_id}' is forbidden for security reasons."
            # Also catch things like getattr(builtins, '__import__')
            elif hasattr(node.func, "attr") and isinstance(getattr(node.func, "attr", None), str):
                func_attr = getattr(node.func, "attr", "")
                if func_attr in {"__import__", "eval", "exec", "open"}:
                    return f"Attribute call '{func_attr}' is forbidden."

    return None


def _make_safe_builtins() -> dict:
    """Create a restricted builtins dict (no exec, eval, open, etc.)."""
    import builtins
    safe = {}
    # Allow most builtins except dangerous ones
    dangerous = {
        "exec", "eval", "compile", "__import__",
        "exit", "quit", "breakpoint",
    }
    for name in dir(builtins):
        if name not in dangerous and not name.startswith("_"):
            safe[name] = getattr(builtins, name)
    # We need __import__ for import statements to work, but we'll
    # control it through the whitelist validation above
    safe["__import__"] = builtins.__import__
    safe["__name__"] = "__main__"
    safe["__build_class__"] = builtins.__build_class__
    return safe


class SandboxResult:
    """Result from sandbox execution."""

    def __init__(self):
        self.circuits: list[Any] = []       # QuantumCircuit objects
        self.counts: list[dict] = []        # Measurement count dicts
        self.stdout: str = ""
        self.stderr: str = ""
        self.error: str | None = None
        self.variables: dict[str, Any] = {} # Named results
        self.execution_time_ms: float = 0
        self.backend: str = ""


def _patch_common_mistakes(code: str) -> str:
    """Fix common LLM code generation mistakes before execution."""

    # Fix: QuantumCircuit() with no args — inject default qubit count
    # Matches: qc = QuantumCircuit() or QuantumCircuit ()
    code = re.sub(
        r'QuantumCircuit\s*\(\s*\)',
        'QuantumCircuit(4)',  # Sensible default
        code,
    )

    # Fix: deprecated execute() API → transpile + run
    # Matches: result = execute(qc, backend) or .execute(...)
    if '.execute(' in code or 'execute(qc' in code or 'execute(circuit' in code:
        # Add AerSimulator import if missing
        if 'AerSimulator' not in code and 'qiskit_aer' not in code:
            code = "from qiskit_aer import AerSimulator\n" + code
        # Replace execute() calls
        code = re.sub(
            r'(\w+)\s*=\s*execute\s*\(\s*(\w+)\s*,\s*(\w+)(?:\s*,\s*shots\s*=\s*(\d+))?\s*\)',
            lambda m: (
                f'_sim = AerSimulator()\n'
                f'from qiskit import transpile\n'
                f'_transpiled = transpile({m.group(2)}, _sim)\n'
                f'{m.group(1)} = _sim.run(_transpiled, shots={m.group(4) or "1024"}).result()'
            ),
            code,
        )

    # Fix: Aer.get_backend('qasm_simulator') → AerSimulator()
    code = re.sub(
        r"Aer\.get_backend\s*\(\s*['\"]qasm_simulator['\"]\s*\)",
        'AerSimulator()',
        code,
    )
    if 'AerSimulator()' in code and 'from qiskit_aer import AerSimulator' not in code:
        code = "from qiskit_aer import AerSimulator\n" + code

    # Fix: from qiskit import AerSimulator → from qiskit_aer import AerSimulator
    # (LLMs frequently put AerSimulator in the wrong package)
    code = re.sub(
        r"from\s+qiskit\s+import\s+(.*)AerSimulator(.*)",
        lambda m: (
            # Keep other imports from qiskit if any, move AerSimulator to qiskit_aer
            (f"from qiskit import {m.group(1).rstrip(', ')}{m.group(2).lstrip(', ')}\n"
             if m.group(1).strip().rstrip(',') or m.group(2).strip().lstrip(',')
             else "")
            + "from qiskit_aer import AerSimulator"
        ),
        code,
    )

    # Fix: from qiskit.providers.aer import AerSimulator → from qiskit_aer import AerSimulator
    code = re.sub(
        r"from\s+qiskit\.providers\.aer\s+import\s+AerSimulator",
        "from qiskit_aer import AerSimulator",
        code,
    )

    return code


def execute_code(code: str) -> SandboxResult:
    """Execute Python/Qiskit code in a sandboxed namespace.

    Captures:
    - Any QuantumCircuit objects created
    - Any measurement counts (dicts with bitstring keys)
    - stdout output
    - Errors with tracebacks
    """
    import time
    result = SandboxResult()

    # Validate imports
    import_error = _validate_imports(code)
    if import_error:
        result.error = import_error
        return result

    # Auto-fix common LLM mistakes
    code = _patch_common_mistakes(code)

    # Prepare isolated namespace with essential Qiskit imports pre-loaded
    # This prevents NameError for common symbols the LLM forgets to import
    namespace: dict[str, Any] = {"__builtins__": _make_safe_builtins()}
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator
        import numpy as np
        import math
        import random
        namespace["QuantumCircuit"] = QuantumCircuit
        namespace["transpile"] = transpile
        namespace["AerSimulator"] = AerSimulator
        namespace["np"] = np
        namespace["numpy"] = np
        namespace["math"] = math
        namespace["random"] = random
        
        # Configure matplotlib to be non-interactive so it doesn't hang headless
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        namespace["matplotlib"] = matplotlib
        namespace["plt"] = plt
    except ImportError:
        pass

    try:
        import dimod
        import neal
        namespace["dimod"] = dimod
        namespace["neal"] = neal
    except ImportError:
        pass

    # Capture stdout/stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Set timeout handler (Unix only)
    def _timeout_handler(signum, frame):
        raise TimeoutError("Code execution timed out (15s limit)")

    old_handler = None
    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(EXECUTION_TIMEOUT)

    start = time.time()
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(compile(code, "<quantum_sandbox>", "exec"), namespace)
    except TimeoutError as e:
        result.error = str(e)
    except Exception as e:
        tb = traceback.format_exc()
        # Clean up the traceback to be user-friendly
        result.error = f"{type(e).__name__}: {e}\n\n```\n{tb}\n```"
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
            if old_handler is not None:
                signal.signal(signal.SIGALRM, old_handler)

    result.execution_time_ms = round((time.time() - start) * 1000, 2)
    result.stderr = stderr_capture.getvalue()
    stdout_text = stdout_capture.getvalue()

    # Scan namespace for quantum objects
    try:
        from qiskit import QuantumCircuit
        QISKIT_AVAILABLE = True
    except ImportError:
        QISKIT_AVAILABLE = False

    # Names we pre-injected — skip these to avoid capturing the class itself
    _SKIP_NAMES = {
        "QuantumCircuit", "transpile", "AerSimulator",
        "np", "numpy", "math", "random", "dimod", "neal"
    }

    if QISKIT_AVAILABLE:
        from qiskit import QuantumCircuit

        # Deduplicate by content fingerprint, not object identity
        circuit_fingerprints: set[str] = set()
        counts_fingerprints: set[str] = set()

        for name, obj in namespace.items():
            if name.startswith("_") or name in _SKIP_NAMES:
                continue
            
            try:
                # Capture QuantumCircuit objects (dedupe by qubit shape)
                if type(obj).__name__ == "QuantumCircuit" or (QISKIT_AVAILABLE and isinstance(obj, QuantumCircuit)):
                    fp = f"{getattr(obj, 'num_qubits', 0)}:{getattr(obj, 'num_clbits', 0)}"
                    if fp not in circuit_fingerprints:
                        result.circuits.append(obj)
                        circuit_fingerprints.add(fp)

                # Capture measurement count dicts (dedupe by content)
                if isinstance(obj, dict) and obj:
                    sample_key = next(iter(obj))
                    if (isinstance(sample_key, str)
                            and len(sample_key) > 0
                            and all(c in "01 " for c in sample_key)
                            and isinstance(next(iter(obj.values())), (int, float))):
                        fp = str(sorted(obj.items()))
                        if fp not in counts_fingerprints:
                            result.counts.append(obj)
                            counts_fingerprints.add(fp)

                # Capture Qiskit Result objects (only if no counts found yet)
                if not result.counts and hasattr(obj, "get_counts"):
                    try:
                        counts = obj.get_counts()
                        if counts and isinstance(counts, dict):
                            fp = str(sorted(counts.items()))
                            if fp not in counts_fingerprints:
                                result.counts.append(counts)
                                counts_fingerprints.add(fp)
                    except Exception:
                        pass

            except (TypeError, Exception):
                continue
                
        # Capture D-Wave SampleSets
        try:
            import dimod
            for name, obj in namespace.items():
                if name.startswith("_") or name in _SKIP_NAMES:
                    continue
                if isinstance(obj, dimod.SampleSet):
                    # Convert sampleset to dict so the UI can render it as a histogram/ResultsView
                    # e.g., {'[0, 1]': 5.0, '[1, 0]': 5.0}  (states -> occurrences/energy)
                    df = obj.to_pandas_dataframe()
                    counts_dict = {}
                    for _, row in df.iterrows():
                        # Use the sample as a string key and num_occurrences as value
                        # Fallback to energy if num_occurrences is missing
                        sample_str = str(dict(row.drop(['energy', 'num_occurrences', 'chain_break_fraction'], errors='ignore')))
                        val = row.get('num_occurrences', row.get('energy', 1))
                        # The UI expects integer counts, but we'll cast to float to be safe if it's energy
                        counts_dict[sample_str] = float(val) if 'energy' in row and 'num_occurrences' not in row else int(val)
                        
                    if counts_dict:
                        fp = str(sorted(counts_dict.items()))
                        if fp not in counts_fingerprints:
                            result.counts.append(counts_dict)
                            counts_fingerprints.add(fp)
        except ImportError:
            pass

        # Fallback: try to parse counts from stdout (printed dicts)
        if not result.counts and result.stdout:
            try:
                # Look for dict-like patterns in stdout: {'000': 512, '111': 512}
                dict_pattern = r"\{['\"]?[01]+['\"]?\s*:\s*\d+.*?\}"
                for match in re.finditer(dict_pattern, result.stdout):
                    try:
                        parsed = eval(match.group())  # Safe: only bitstring→int dicts
                        if isinstance(parsed, dict) and parsed:
                            sample_key = next(iter(parsed))
                            if (isinstance(sample_key, str)
                                    and all(c in "01" for c in sample_key)):
                                result.counts.append(parsed)
                                break  # Take the first one
                    except Exception:
                        continue
            except Exception:
                pass

    result.stdout = stdout_text
    return result


def build_artifacts_from_result(
    result: SandboxResult,
    code: str,
    agent_label: str = "Code",
) -> list[Artifact]:
    """Convert a SandboxResult into structured Artifact objects."""
    artifacts: list[Artifact] = []

    # Always add the code as an artifact
    if code.strip():
        artifacts.append(Artifact(
            type=ArtifactType.CODE,
            title=f"{agent_label} — Qiskit Code",
            content=code.strip(),
            language="python",
        ))

    import sys
    import io
    from contextlib import redirect_stdout
    
    # Add circuit diagrams
    for i, circuit in enumerate(result.circuits):
        try:
            # Qiskit circuit.draw checks sys.stdout.encoding, which Celery's LoggingProxy lacks
            class DummyStdout(io.StringIO):
                @property
                def encoding(self):
                    return "utf-8"
            
            dummy_stdout = DummyStdout()
            
            with redirect_stdout(dummy_stdout):
                diagram = str(circuit.draw(output="text"))
                
            suffix = f" ({i+1})" if len(result.circuits) > 1 else ""
            artifacts.append(Artifact(
                type=ArtifactType.CIRCUIT,
                title=f"{agent_label} — Circuit Diagram{suffix}",
                content=code.strip(),
                metadata={
                    "ascii_diagram": diagram,
                    "num_qubits": circuit.num_qubits,
                    "depth": circuit.depth(),
                },
            ))
        except Exception as e:
            logger.error(f"Failed to draw circuit diagram: {e}", exc_info=True)

    # Add measurement results
    for i, counts in enumerate(result.counts):
        suffix = f" ({i+1})" if len(result.counts) > 1 else ""
        # Compute basic stats
        total_shots = sum(counts.values())
        artifacts.append(Artifact(
            type=ArtifactType.RESULTS,
            title=f"{agent_label} — Measurement Results{suffix}",
            content=json.dumps(counts),
            metadata={
                "shots": total_shots,
                "execution_time_ms": result.execution_time_ms,
                "num_states": len(counts),
            },
        ))

    # ── Error Mitigation: apply ZNE + measurement mitigation ────
    # When we have both circuits and counts, run mitigation and add
    # mitigated results as companion artifacts.
    if result.circuits and result.counts:
        try:
            from app.quantum.mitigation import apply_zne, apply_measurement_mitigation
            for i, circuit in enumerate(result.circuits):
                # Only mitigate circuits with measurements
                if circuit.num_clbits == 0:
                    continue
                try:
                    # ZNE mitigation
                    zne_result = apply_zne(circuit, shots=1024)
                    if "extrapolated" in zne_result and zne_result["extrapolated"]:
                        suffix = f" ({i+1})" if len(result.circuits) > 1 else ""
                        artifacts.append(Artifact(
                            type=ArtifactType.RESULTS,
                            title=f"{agent_label} — ZNE Mitigated{suffix}",
                            content=json.dumps(zne_result["extrapolated"]),
                            metadata={
                                "shots": 1024,
                                "method": "ZNE (Richardson extrapolation)",
                                "noise_factors": zne_result.get("noise_factors", [1, 2, 3]),
                                "execution_time_ms": result.execution_time_ms,
                                "num_states": len(zne_result["extrapolated"]),
                            },
                        ))

                    # Measurement mitigation
                    meas_result = apply_measurement_mitigation(circuit, shots=1024)
                    if "mitigated_counts" in meas_result and meas_result["mitigated_counts"]:
                        suffix = f" ({i+1})" if len(result.circuits) > 1 else ""
                        artifacts.append(Artifact(
                            type=ArtifactType.RESULTS,
                            title=f"{agent_label} — Calibrated{suffix}",
                            content=json.dumps(meas_result["mitigated_counts"]),
                            metadata={
                                "shots": 1024,
                                "method": "Measurement calibration",
                                "execution_time_ms": result.execution_time_ms,
                                "num_states": len(meas_result["mitigated_counts"]),
                            },
                        ))
                except Exception as e:
                    logger.debug(f"Error mitigation skipped for circuit {i}: {e}")
        except ImportError:
            logger.debug("Mitigation module not available, skipping")

    return artifacts


def execute_and_build_artifacts(
    llm_output: str,
    agent_label: str = "Code",
) -> tuple[list[Artifact], str | None]:
    """Full pipeline: extract code from LLM output → execute → build artifacts.

    Returns (artifacts, error_message_or_None).
    """
    code_blocks = extract_code_blocks(llm_output)
    if not code_blocks:
        return [], None

    all_artifacts: list[Artifact] = []
    error_msg = None

    for code in code_blocks:
        # Skip very short code blocks (likely just examples, not runnable)
        if len(code.strip()) < 30:
            continue

        # Skip code that's clearly just an example snippet (no imports)
        if "import" not in code and "QuantumCircuit" not in code:
            continue

        result = execute_code(code)

        if result.error:
            error_msg = result.error
            logger.warning(f"Sandbox execution error: {result.error[:200]}")
            # Still try to build artifacts from partial results
            if result.circuits or result.counts:
                artifacts = build_artifacts_from_result(result, code, agent_label)
                all_artifacts.extend(artifacts)
            continue

        artifacts = build_artifacts_from_result(result, code, agent_label)
        all_artifacts.extend(artifacts)

    return all_artifacts, error_msg

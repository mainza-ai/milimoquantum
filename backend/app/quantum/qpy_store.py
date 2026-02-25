"""Milimo Quantum — QPY Serialization Utilities.

Save and load Qiskit QuantumCircuit objects in QPY binary format.
QPY preserves the full circuit including metadata, parameters, and calibrations.
"""
from __future__ import annotations

import io
import logging
import base64
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CIRCUITS_DIR = Path.home() / ".milimoquantum" / "circuits"


def _ensure_dir() -> None:
    CIRCUITS_DIR.mkdir(parents=True, exist_ok=True)


def save_circuit_qpy(circuit: Any, name: str) -> dict:
    """Save a QuantumCircuit to QPY format on disk.

    Returns metadata about the saved circuit.
    """
    try:
        from qiskit import qpy

        _ensure_dir()
        filepath = CIRCUITS_DIR / f"{name}.qpy"

        with open(filepath, "wb") as f:
            qpy.dump(circuit, f)

        logger.info(f"Saved circuit '{name}' to QPY: {filepath}")
        return {
            "name": name,
            "path": str(filepath),
            "num_qubits": circuit.num_qubits,
            "depth": circuit.depth(),
            "size_bytes": filepath.stat().st_size,
            "format": "qpy",
        }
    except ImportError:
        return {"error": "Qiskit QPY module not available"}
    except Exception as e:
        logger.error(f"Failed to save QPY: {e}")
        return {"error": str(e)}


def load_circuit_qpy(name: str) -> dict:
    """Load a QuantumCircuit from QPY format.

    Returns the circuit as QASM string + metadata.
    """
    try:
        from qiskit import qpy
        import qiskit.qasm2

        _ensure_dir()
        filepath = CIRCUITS_DIR / f"{name}.qpy"

        if not filepath.exists():
            return {"error": f"Circuit '{name}' not found"}

        with open(filepath, "rb") as f:
            circuits = qpy.load(f)

        circuit = circuits[0] if circuits else None
        if circuit is None:
            return {"error": "No circuit found in file"}

        return {
            "name": name,
            "num_qubits": circuit.num_qubits,
            "depth": circuit.depth(),
            "gate_count": circuit.size(),
            "qasm": qiskit.qasm2.dumps(circuit),
            "format": "qpy",
        }
    except ImportError:
        return {"error": "Qiskit QPY module not available"}
    except Exception as e:
        logger.error(f"Failed to load QPY: {e}")
        return {"error": str(e)}


def list_saved_circuits() -> list[dict]:
    """List all saved QPY circuits."""
    _ensure_dir()
    circuits = []
    for filepath in sorted(CIRCUITS_DIR.glob("*.qpy")):
        circuits.append({
            "name": filepath.stem,
            "size_bytes": filepath.stat().st_size,
            "modified": filepath.stat().st_mtime,
        })
    return circuits


def circuit_to_base64_qpy(circuit: Any) -> str | None:
    """Serialize a circuit to base64-encoded QPY for API transport."""
    try:
        from qiskit import qpy

        buf = io.BytesIO()
        qpy.dump(circuit, buf)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        logger.error(f"QPY base64 encoding failed: {e}")
        return None


def base64_qpy_to_circuit(data: str) -> Any | None:
    """Deserialize a base64-encoded QPY string back to a circuit."""
    try:
        from qiskit import qpy

        buf = io.BytesIO(base64.b64decode(data))
        circuits = qpy.load(buf)
        return circuits[0] if circuits else None
    except Exception as e:
        logger.error(f"QPY base64 decoding failed: {e}")
        return None

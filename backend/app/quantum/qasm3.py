"""Milimo Quantum — OpenQASM 3 Utilities.

Parse, validate, and export OpenQASM 3 circuit strings.
Integrates with Qiskit's QASM3 exporter/importer.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def parse_qasm3(qasm_string: str) -> dict:
    """Parse an OpenQASM 3 string into a structured representation.

    Returns dict with: version, qubits, cbits, gates[], metadata.
    """
    result: dict[str, Any] = {
        "version": "3.0",
        "qubits": 0,
        "cbits": 0,
        "gates": [],
        "raw": qasm_string,
        "valid": True,
        "errors": [],
    }

    lines = qasm_string.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("//"):
            continue

        # OPENQASM version
        if line.startswith("OPENQASM"):
            match = re.match(r"OPENQASM\s+(\d+\.?\d*)", line)
            if match:
                result["version"] = match.group(1)
            continue

        # Include
        if line.startswith("include"):
            continue

        # Qubit declaration: qubit[n] q;  or  qreg q[n];
        qreg_match = re.match(r"(?:qubit\[(\d+)\]|qreg\s+\w+\[(\d+)\])", line)
        if qreg_match:
            n = int(qreg_match.group(1) or qreg_match.group(2))
            result["qubits"] = max(result["qubits"], n)
            continue

        # Classical bit declaration: bit[n] c;  or  creg c[n];
        creg_match = re.match(r"(?:bit\[(\d+)\]|creg\s+\w+\[(\d+)\])", line)
        if creg_match:
            n = int(creg_match.group(1) or creg_match.group(2))
            result["cbits"] = max(result["cbits"], n)
            continue

        # Gate application: gate_name qubit_list;
        gate_match = re.match(
            r"(\w+)(?:\(([\d.,\s\w/*\-+π]*)\))?\s+([\w\[\],\s]+);", line
        )
        if gate_match:
            gate_name = gate_match.group(1).lower()
            params = gate_match.group(2) or ""
            operands = gate_match.group(3)

            # Parse qubit references
            qubits = []
            for op in re.findall(r"\w+\[(\d+)\]", operands):
                qubits.append(int(op))

            result["gates"].append({
                "name": gate_name,
                "params": params.strip() if params else None,
                "qubits": qubits,
            })
            continue

        # Measure
        if line.startswith("measure") or "measure" in line:
            result["gates"].append({
                "name": "measure",
                "params": None,
                "qubits": list(range(result["qubits"])) if result["qubits"] else [0],
            })

    return result


def circuit_to_qasm3(code: str) -> str:
    """Convert a Qiskit circuit code string to OpenQASM 3 output.

    Uses Qiskit's qasm3 exporter if available, otherwise
    builds a basic QASM3 string from parsed gate info.
    """
    try:
        # Attempt Qiskit-native export
        from qiskit import QuantumCircuit
        from qiskit.qasm3 import dumps as qasm3_dumps

        # Try to execute the code to get a circuit object
        local_ns: dict[str, Any] = {}
        exec(code, {"QuantumCircuit": QuantumCircuit}, local_ns)

        # Find any QuantumCircuit in the namespace
        for val in local_ns.values():
            if isinstance(val, QuantumCircuit):
                return qasm3_dumps(val)

    except ImportError:
        logger.debug("qiskit.qasm3 not available, using fallback")
    except Exception as e:
        logger.debug(f"Qiskit QASM3 export failed: {e}")

    # Fallback: build basic QASM3 from pattern matching
    return _build_qasm3_fallback(code)


def _build_qasm3_fallback(code: str) -> str:
    """Build a basic QASM3 string from Python circuit code."""
    lines = ["OPENQASM 3.0;", 'include "stdgates.inc";', ""]

    # Detect qubit count
    qc_match = re.search(r"QuantumCircuit\s*\(\s*(\d+)", code)
    num_qubits = int(qc_match.group(1)) if qc_match else 2

    lines.append(f"qubit[{num_qubits}] q;")
    lines.append(f"bit[{num_qubits}] c;")
    lines.append("")

    # Map Python gate calls to QASM3
    gate_map = {
        "h": "h",
        "x": "x",
        "y": "y",
        "z": "z",
        "s": "s",
        "t": "t",
        "cx": "cx",
        "cz": "cz",
        "swap": "swap",
        "ccx": "ccx",
        "rx": "rx",
        "ry": "ry",
        "rz": "rz",
    }

    for match in re.finditer(
        r"(?:qc|circuit|q)\.(\w+)\s*\(([\d,.\s\w]*)\)", code
    ):
        gate = match.group(1).lower()
        args_str = match.group(2).strip()
        args = [a.strip() for a in args_str.split(",") if a.strip()]

        if gate == "measure_all":
            lines.append("c = measure q;")
        elif gate == "measure":
            qubit_args = [a for a in args if a.isdigit()]
            if len(qubit_args) >= 2:
                lines.append(f"c[{qubit_args[1]}] = measure q[{qubit_args[0]}];")
        elif gate in gate_map:
            qasm_gate = gate_map[gate]
            qubit_args = [a for a in args if a.isdigit()]

            # Rotation gates with parameter
            if gate in ("rx", "ry", "rz") and len(args) >= 2:
                param = args[0]
                qubit = args[1] if len(args) > 1 else "0"
                lines.append(f"{qasm_gate}({param}) q[{qubit}];")
            elif len(qubit_args) == 1:
                lines.append(f"{qasm_gate} q[{qubit_args[0]}];")
            elif len(qubit_args) == 2:
                lines.append(f"{qasm_gate} q[{qubit_args[0]}], q[{qubit_args[1]}];")
            elif len(qubit_args) == 3:
                lines.append(
                    f"{qasm_gate} q[{qubit_args[0]}], q[{qubit_args[1]}], q[{qubit_args[2]}];"
                )

    return "\n".join(lines) + "\n"


def validate_qasm3(qasm_string: str) -> dict:
    """Validate an OpenQASM 3 string.

    Returns: {valid: bool, errors: list[str], gate_count: int, qubit_count: int}
    """
    parsed = parse_qasm3(qasm_string)
    errors: list[str] = []

    if "OPENQASM" not in qasm_string:
        errors.append("Missing OPENQASM version declaration")

    if parsed["qubits"] == 0:
        errors.append("No qubit declarations found")

    if not parsed["gates"]:
        errors.append("No gate operations found")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "gate_count": len(parsed["gates"]),
        "qubit_count": parsed["qubits"],
        "version": parsed["version"],
    }

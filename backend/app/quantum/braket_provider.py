"""Milimo Quantum — Amazon Braket Provider.

Provides access to Amazon Braket quantum devices (IonQ, Rigetti, AWS simulators).
Gated behind optional amazon-braket-sdk installation.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

BRAKET_AVAILABLE = False
try:
    from braket.aws import AwsDevice
    from braket.circuits import Circuit as BraketCircuit
    from braket.devices import LocalSimulator
    BRAKET_AVAILABLE = True
except ImportError:
    logger.info("amazon-braket-sdk not installed — Braket hardware disabled")


# ── Known Braket Devices ────────────────────────────────
BRAKET_DEVICES = {
    "ionq_aria": {
        "name": "IonQ Aria",
        "arn": "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1",
        "type": "QPU",
        "provider": "IonQ",
        "qubits": 25,
    },
    "rigetti_ankaa": {
        "name": "Rigetti Ankaa-2",
        "arn": "arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-2",
        "type": "QPU",
        "provider": "Rigetti",
        "qubits": 84,
    },
    "sv1": {
        "name": "AWS SV1 Simulator",
        "arn": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        "type": "Simulator",
        "provider": "AWS",
        "qubits": 34,
    },
    "dm1": {
        "name": "AWS DM1 Density Matrix",
        "arn": "arn:aws:braket:::device/quantum-simulator/amazon/dm1",
        "type": "Simulator",
        "provider": "AWS",
        "qubits": 17,
    },
    "local": {
        "name": "Braket Local Simulator",
        "arn": "local",
        "type": "Local",
        "provider": "Local",
        "qubits": 26,
    },
}


def is_configured() -> bool:
    """Check if AWS credentials are available for Braket."""
    return bool(
        os.environ.get("AWS_ACCESS_KEY_ID")
        and os.environ.get("AWS_SECRET_ACCESS_KEY")
    )


def get_status() -> dict:
    """Get Braket provider status."""
    return {
        "sdk_installed": BRAKET_AVAILABLE,
        "configured": is_configured(),
        "provider": "Amazon Braket",
        "devices": list(BRAKET_DEVICES.keys()),
    }


def list_devices() -> list[dict]:
    """List available Braket devices."""
    devices = []
    for device_id, info in BRAKET_DEVICES.items():
        available = BRAKET_AVAILABLE and (
            info["type"] == "Local" or is_configured()
        )
        devices.append({
            "id": device_id,
            "name": info["name"],
            "provider": info["provider"],
            "type": info["type"],
            "qubits": info["qubits"],
            "available": available,
        })
    return devices


def run_circuit(
    qasm_str: str,
    device_id: str = "local",
    shots: int = 1024,
) -> dict:
    """Run a circuit on a Braket device.

    Args:
        qasm_str: OpenQASM 3.0 circuit string.
        device_id: Device key from BRAKET_DEVICES.
        shots: Number of measurement shots.

    Returns:
        dict with counts, job_id, device info.
    """
    if not BRAKET_AVAILABLE:
        return {"error": "amazon-braket-sdk not installed. Install: pip install amazon-braket-sdk"}

    if device_id not in BRAKET_DEVICES:
        return {"error": f"Unknown device: {device_id}. Available: {list(BRAKET_DEVICES.keys())}"}

    device_info = BRAKET_DEVICES[device_id]

    try:
        if device_id == "local":
            device = LocalSimulator()
        else:
            if not is_configured():
                return {"error": "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."}
            device = AwsDevice(device_info["arn"])

        # Create Braket circuit from QASM
        circuit = BraketCircuit.from_ir(qasm_str)

        # Run
        task = device.run(circuit, shots=shots)
        result = task.result()
        counts = dict(result.measurement_counts)

        return {
            "counts": counts,
            "shots": shots,
            "device": device_info["name"],
            "device_id": device_id,
            "provider": "Amazon Braket",
            "task_id": str(task.id) if hasattr(task, "id") else "local",
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Braket execution failed: {e}")
        return {"error": str(e)}

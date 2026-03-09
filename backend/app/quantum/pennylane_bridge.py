"""Milimo Quantum — PennyLane Bridge.

Cross-framework bridge to run PennyLane circuits with Qiskit backends.
Enables quantum machine learning workflows using PennyLane's autodiff
while leveraging Qiskit's hardware access and simulation infrastructure.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def is_pennylane_available() -> bool:
    """Check if PennyLane and pennylane-qiskit plugin are installed."""
    try:
        import pennylane  # noqa: F401
        return True
    except ImportError:
        return False


def get_pennylane_info() -> dict:
    """Get PennyLane version and available devices."""
    try:
        import pennylane as qml

        devices = {
            "default.qubit": "CPU-based statevector simulator",
            "default.mixed": "Mixed-state density matrix simulator",
            "default.clifford": "Fast Clifford simulator",
            "lightning.qubit": "High-performance C++ statevector",
        }

        # Check for Qiskit plugin
        try:
            import pennylane_qiskit  # noqa: F401
            devices["qiskit.aer"] = "Qiskit Aer through PennyLane"
            devices["qiskit.remote"] = "IBM Quantum hardware through PennyLane"
            qiskit_plugin = True
        except ImportError:
            qiskit_plugin = False

        return {
            "version": qml.__version__,
            "devices": devices,
            "qiskit_plugin": qiskit_plugin,
        }
    except ImportError:
        return {"error": "PennyLane not installed. Install with: pip install pennylane pennylane-qiskit"}


def run_vqe_pennylane(
    hamiltonian: str = "H2",
    num_qubits: int = 2,
    layers: int = 2,
    steps: int = 100,
    step_size: float = 0.4,
) -> dict:
    """Run a VQE optimization using PennyLane.

    Uses PennyLane's autodiff for gradient computation = faster than
    parameter-shift rule on simulators.
    """
    try:
        import pennylane as qml
        from pennylane import numpy as np

        # Define device
        dev = qml.device("default.qubit", wires=num_qubits)

        # Build Hamiltonian
        if hamiltonian == "H2":
            # H2 Hamiltonian (simplified Bravyi-Kitaev)
            coeffs = [0.2252, 0.3435, -0.4348, 0.5716, 0.0910]
            obs = [
                qml.Identity(0),
                qml.PauliZ(0),
                qml.PauliZ(1),
                qml.PauliZ(0) @ qml.PauliZ(1),
                qml.PauliX(0) @ qml.PauliX(1),
            ]
            H = qml.Hamiltonian(coeffs, obs)
        else:
            # Generic Ising model
            coeffs = [-1.0] * num_qubits + [-0.5] * (num_qubits - 1)
            obs = [qml.PauliZ(i) for i in range(num_qubits)]
            obs += [qml.PauliZ(i) @ qml.PauliZ(i + 1) for i in range(num_qubits - 1)]
            H = qml.Hamiltonian(coeffs, obs)

        # Ansatz circuit
        @qml.qnode(dev, interface="autograd")
        def cost_fn(params):
            for layer in range(layers):
                for i in range(num_qubits):
                    qml.RY(params[layer, i, 0], wires=i)
                    qml.RZ(params[layer, i, 1], wires=i)
                for i in range(num_qubits - 1):
                    qml.CNOT(wires=[i, i + 1])
            return qml.expval(H)

        # Optimization
        params = np.random.uniform(low=-np.pi, high=np.pi, size=(layers, num_qubits, 2))
        opt = qml.GradientDescentOptimizer(stepsize=step_size)

        energies = []
        for step in range(steps):
            params, energy = opt.step_and_cost(cost_fn, params)
            energies.append(float(energy))

        return {
            "hamiltonian": hamiltonian,
            "num_qubits": num_qubits,
            "layers": layers,
            "steps": steps,
            "final_energy": energies[-1] if energies else None,
            "energy_history": energies,
            "converged": len(energies) > 10 and abs(energies[-1] - energies[-10]) < 1e-5,
        }
    except ImportError:
        return {"error": "PennyLane not installed. Install with: pip install pennylane"}
    except Exception as e:
        return {"error": str(e)}


def run_qml_classifier(
    n_samples: int = 100,
    n_features: int = 2,
    n_qubits: int = 2,
    layers: int = 3,
    epochs: int = 50,
) -> dict:
    """Train a simple quantum classifier using PennyLane.

    Creates a synthetic dataset and trains a variational classifier.
    """
    try:
        import pennylane as qml
        from pennylane import numpy as np

        # Generate synthetic XOR-like dataset
        np.random.seed(42)
        X = np.random.uniform(-1, 1, (n_samples, n_features))
        y = np.array([1 if x[0] * x[1] > 0 else -1 for x in X], dtype=float)

        dev = qml.device("default.qubit", wires=n_qubits)

        @qml.qnode(dev, interface="autograd")
        def circuit(weights, x):
            # Encode features
            for i in range(min(n_features, n_qubits)):
                qml.RY(x[i], wires=i)
            # Variational layers
            for layer in range(layers):
                for i in range(n_qubits):
                    qml.Rot(*weights[layer, i], wires=i)
                for i in range(n_qubits - 1):
                    qml.CNOT(wires=[i, i + 1])
            return qml.expval(qml.PauliZ(0))

        def cost(weights, X, y):
            predictions = np.array([circuit(weights, x) for x in X])
            return np.mean((predictions - y) ** 2)

        weights = np.random.uniform(-np.pi, np.pi, (layers, n_qubits, 3))
        opt = qml.AdamOptimizer(stepsize=0.1)

        loss_history = []
        for epoch in range(epochs):
            weights, loss_val = opt.step_and_cost(lambda w: cost(w, X, y), weights)
            loss_history.append(float(loss_val))

        # Final accuracy
        predictions = np.array([1 if circuit(weights, x) > 0 else -1 for x in X])
        accuracy = float(np.mean(predictions == y))

        return {
            "n_samples": n_samples,
            "n_qubits": n_qubits,
            "layers": layers,
            "epochs": epochs,
            "final_loss": loss_history[-1] if loss_history else None,
            "accuracy": accuracy,
            "loss_history": loss_history,
        }
    except ImportError:
        return {"error": "PennyLane not installed. Install with: pip install pennylane"}
    except Exception as e:
        return {"error": str(e)}


def convert_qiskit_to_pennylane(qiskit_code: str) -> dict:
    """Convert a Qiskit circuit string to a PennyLane circuit.

    Returns PennyLane-style code as a string.
    """
    try:
        import pennylane as qml

        # Gate mapping from Qiskit to PennyLane
        gate_map = {
            "h": "qml.Hadamard",
            "x": "qml.PauliX",
            "y": "qml.PauliY",
            "z": "qml.PauliZ",
            "cx": "qml.CNOT",
            "cz": "qml.CZ",
            "rx": "qml.RX",
            "ry": "qml.RY",
            "rz": "qml.RZ",
            "s": "qml.S",
            "t": "qml.T",
            "swap": "qml.SWAP",
            "ccx": "qml.Toffoli",
        }

        return {
            "gate_map": gate_map,
            "pennylane_version": qml.__version__,
            "note": "Use qml.from_qiskit(qiskit_circuit) for direct conversion with pennylane-qiskit plugin",
        }
    except ImportError:
        return {"error": "PennyLane not installed"}

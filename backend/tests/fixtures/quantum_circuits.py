"""Milimo Quantum — Quantum Circuit Test Fixtures."""

BELL_STATE_CIRCUIT = {
    "name": "bell_state",
    "qubits": 2,
    "gates": ["h(0)", "cx(0,1)"],
    "expected_distribution": {"00": 0.5, "11": 0.5},
}

GHZ_STATE_CIRCUIT = {
    "name": "ghz_state",
    "qubits": 3,
    "gates": ["h(0)", "cx(0,1)", "cx(1,2)"],
    "expected_distribution": {"000": 0.5, "111": 0.5},
}

W_STATE_CIRCUIT = {
    "name": "w_state",
    "qubits": 3,
    "gates": [
        "h(2)",
        "cx(2,1)",
        "cx(1,0)",
        "h(1)",
        "t(0)",
        "cx(0,1)",
        "h(1)",
        "t(0)",
    ],
    "expected_distribution": {"001": 0.33, "010": 0.33, "100": 0.33},
}

QFT_CIRCUIT = {
    "name": "qft",
    "qubits": 3,
    "gates": ["h(0)", "cp(1,0,pi/2)", "h(1)", "cp(2,0,pi/4)", "cp(2,1,pi/2)", "h(2)", "swap(0,2)"],
    "description": "Quantum Fourier Transform on 3 qubits",
}

RANDOM_CIRCUIT = {
    "name": "random_4q",
    "qubits": 4,
    "gates": [
        "h(0)", "h(1)", "h(2)", "h(3)",
        "cx(0,1)", "cx(2,3)",
        "rz(0.5,0)", "rz(0.5,1)", "rz(0.5,2)", "rz(0.5,3)",
        "cx(1,2)",
    ],
    "description": "Random 4-qubit circuit for testing",
}

VQE_ANSATZ_CIRCUITS = {
    "real_amplitudes": {
        "name": "real_amplitudes",
        "reps": 3,
        "entanglement": "linear",
    },
    "efficient_su2": {
        "name": "efficient_su2",
        "reps": 2,
        "entanglement": "circular",
    },
    "two_local": {
        "name": "two_local",
        "rotation_blocks": ["ry", "rz"],
        "entanglement_blocks": "cx",
        "reps": 4,
    },
}

HAMILTONIANS = {
    "h2": {
        "name": "H2",
        "description": "Hydrogen molecule",
        "num_orbitals": 2,
        "expected_ground_state": -1.137,
    },
    "lih": {
        "name": "LiH",
        "description": "Lithium hydride",
        "num_orbitals": 4,
        "expected_ground_state": -7.88,
    },
    "beh2": {
        "name": "BeH2",
        "description": "Beryllium hydride",
        "num_orbitals": 6,
        "expected_ground_state": -15.6,
    },
}

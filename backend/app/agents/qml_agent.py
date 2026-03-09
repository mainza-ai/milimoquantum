"""Milimo Quantum — Quantum Machine Learning Agent.

Handles QNN, QSVM, quantum kernels, variational classifiers,
and quantum feature maps.
Phase 3: Template-based with executable circuits.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType


# ── Quick-reference knowledge base ──────────────────────
QUICK_TOPICS: dict[str, str] = {
    "qnn": """## Quantum Neural Networks (QNN)

A QNN uses parameterized quantum circuits as trainable models.

### Architecture

```
Input x → Encoding U(x) → Variational V(θ) → Measurement → ŷ
                                    ↑
                     Classical optimizer updates θ
```

### Types of QNNs

| Type | Qiskit Class | Use Case |
|------|-------------|----------|
| **SamplerQNN** | `SamplerQNN` | Classification via sampling |
| **EstimatorQNN** | `EstimatorQNN` | Regression via expectation values |
| **TorchConnector** | `TorchConnector` | Hybrid PyTorch integration |

### Training Loop

```python
from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
from qiskit_machine_learning.neural_networks import EstimatorQNN
from qiskit_machine_learning.algorithms import NeuralNetworkClassifier

feature_map = ZZFeatureMap(feature_dimension=2, reps=2)
ansatz = RealAmplitudes(num_qubits=2, reps=1)
qnn = EstimatorQNN(circuit=feature_map.compose(ansatz))
classifier = NeuralNetworkClassifier(qnn, optimizer=COBYLA())
classifier.fit(X_train, y_train)
```

💡 *Try it*: `/qml Build a 2-qubit variational classifier`
""",

    "qsvm": """## Quantum Support Vector Machine (QSVM)

QSVM uses quantum feature maps to compute kernels in exponentially large Hilbert spaces.

### Quantum Kernel Trick

K(x, x') = |⟨0|U†(x')U(x)|0⟩|²

### Comparison

| Aspect | Classical SVM | Quantum SVM |
|--------|:---:|:---:|
| Feature space | Polynomial | **Exponential (2ⁿ)** |
| Advantage regime | Low-dim | High-dim, structured data |

### Implementation

```python
from qiskit.circuit.library import ZZFeatureMap
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from sklearn.svm import SVC

feature_map = ZZFeatureMap(feature_dimension=4, reps=2)
kernel = FidelityQuantumKernel(feature_map=feature_map)
svc = SVC(kernel=kernel.evaluate)
svc.fit(X_train, y_train)
```
""",

    "feature_map": """## Quantum Feature Maps (Data Encoding)

Feature maps encode classical data into quantum states.

### Encoding Strategies

| Strategy | Circuit | Capacity |
|----------|---------|:---:|
| **Basis encoding** | X gates | N → N qubits |
| **Angle encoding** | R_y(x) | N → N qubits |
| **Amplitude encoding** | State prep | 2ⁿ → N qubits |
| **IQP encoding** | Z + entanglement | N → N qubits |

### Design Principles

1. **Match data structure** — use ZZ entanglement for correlated features
2. **Avoid over-encoding** — too many reps causes barren plateaus
3. **Data re-uploading** — repeat encoding layers for richer representations
""",

    "barren": """## Barren Plateaus in Quantum ML

As circuit depth increases, gradients **vanish exponentially**:

$$\\text{Var}[\\partial C/\\partial \\theta_i] \\leq F(n) \\cdot e^{-cn}$$

### Mitigations

| Cause | Mitigation |
|-------|-----------|
| Deep random circuits | Shallow circuits (reps ≤ 3) |
| Global cost functions | Local cost functions |
| Hardware noise | Error mitigation |
| Too much entanglement | Structured entanglement |

### Rule of Thumb

> **If n_qubits × depth > 20**, expect barren plateaus.
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "qnn": ["qnn", "quantum neural network", "neural network", "variational classifier", "torchconnector"],
    "qsvm": ["qsvm", "quantum svm", "support vector", "quantum kernel", "kernel method"],
    "feature_map": ["feature map", "encoding", "data encoding", "zzfeaturemap", "paulifeaturemap"],
    "barren": ["barren plateau", "gradient vanishing", "trainability"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick QML topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None


# ── Quick circuit templates ─────────────────────────────
def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to generate a QML-related circuit."""
    lower = message.lower()

    if any(kw in lower for kw in ["classifier", "classify", "classification", "variational"]):
        return _build_variational_classifier()

    if any(kw in lower for kw in ["feature map", "encoding", "zzfeature", "encode data"]):
        return _build_feature_map_demo()

    return [], None


def _build_variational_classifier() -> tuple[list[Artifact], str | None]:
    """Build and execute a 2-qubit variational classifier."""
    code = '''from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
from qiskit_aer import AerSimulator
import numpy as np

feature_map = ZZFeatureMap(feature_dimension=2, reps=2)
ansatz = RealAmplitudes(num_qubits=2, reps=2)
classifier_circuit = feature_map.compose(ansatz)

data_params = {feature_map.parameters[i]: [0.5, 1.2][i] for i in range(2)}
n_params = ansatz.num_parameters
theta = np.random.uniform(-np.pi, np.pi, n_params)
ansatz_params = {ansatz.parameters[i]: theta[i] for i in range(n_params)}

bound = classifier_circuit.assign_parameters({**data_params, **ansatz_params})
qc = QuantumCircuit(2, 2)
qc.compose(bound, inplace=True)
qc.measure([0, 1], [0, 1])

sim = AerSimulator()
result = sim.run(transpile(qc, sim), shots=4096).result()
counts = result.get_counts()
print("Variational Classifier Output:", counts)
print(f"Trainable parameters: {n_params}")
'''

    from app.quantum.executor import QISKIT_AVAILABLE
    if not QISKIT_AVAILABLE:
        return [], None

    artifacts = [Artifact(type=ArtifactType.CODE, title="Variational Classifier — Qiskit Code", content=code, language="python")]

    try:
        from qiskit import QuantumCircuit as QC, transpile
        from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
        from qiskit_aer import AerSimulator
        import numpy as np
        import json
        import time

        feature_map = ZZFeatureMap(feature_dimension=2, reps=2)
        ansatz = RealAmplitudes(num_qubits=2, reps=2)
        classifier = feature_map.compose(ansatz)

        data_params = {feature_map.parameters[i]: [0.5, 1.2][i] for i in range(2)}
        n_params = ansatz.num_parameters
        theta = np.random.uniform(-np.pi, np.pi, n_params)
        ansatz_params = {ansatz.parameters[i]: theta[i] for i in range(n_params)}
        bound = classifier.assign_parameters({**data_params, **ansatz_params})

        qc = QC(2, 2)
        qc.compose(bound, inplace=True)
        qc.measure([0, 1], [0, 1])

        sim = AerSimulator()
        t0 = time.time()
        result = sim.run(transpile(qc, sim), shots=4096).result()
        elapsed = round((time.time() - t0) * 1000, 2)
        counts = result.get_counts()

        artifacts.append(Artifact(
            type=ArtifactType.RESULTS, title="Variational Classifier — Output",
            content=json.dumps(counts),
            metadata={"shots": 4096, "execution_time_ms": elapsed, "backend": "aer_simulator", "num_qubits": 2, "depth": qc.depth(), "trainable_params": n_params},
        ))

        top = sorted(counts.items(), key=lambda x: -x[1])[:4]
        counts_str = ", ".join(f"`{k}`: {v}" for k, v in top)
        summary = (
            f"## Variational Quantum Classifier\n\n"
            f"Built a 2-qubit variational classifier.\n\n"
            f"**Feature map:** ZZFeatureMap (2 reps) | **Ansatz:** RealAmplitudes ({n_params} params)\n"
            f"**Input:** [0.5, 1.2] | **Depth:** {qc.depth()} | **Time:** {elapsed}ms\n\n"
            f"**Output:** {counts_str}\n\n"
            f"Train with a classical optimizer (COBYLA, Adam) to minimize cross-entropy loss."
        )
        return artifacts, summary
    except Exception:
        return artifacts, "## Variational Classifier\n\nCode generated. Check the artifact panel."


def _build_feature_map_demo() -> tuple[list[Artifact], str | None]:
    """Build and execute a feature map demonstration."""
    code = '''from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import ZZFeatureMap
from qiskit_aer import AerSimulator

feature_map = ZZFeatureMap(feature_dimension=4, reps=2, entanglement="linear")
data = [0.3, 1.5, 0.7, 2.1]
params = {feature_map.parameters[i]: data[i] for i in range(4)}
bound = feature_map.assign_parameters(params)

qc = QuantumCircuit(4, 4)
qc.compose(bound, inplace=True)
qc.measure(range(4), range(4))

sim = AerSimulator()
result = sim.run(transpile(qc, sim), shots=4096).result()
counts = result.get_counts()
print(f"ZZFeatureMap encoding of {data}:", dict(sorted(counts.items(), key=lambda x: -x[1])[:8]))
'''

    from app.quantum.executor import QISKIT_AVAILABLE
    if not QISKIT_AVAILABLE:
        return [], None

    artifacts = [Artifact(type=ArtifactType.CODE, title="ZZFeatureMap Demo — Qiskit Code", content=code, language="python")]

    try:
        from qiskit import QuantumCircuit as QC, transpile
        from qiskit.circuit.library import ZZFeatureMap
        from qiskit_aer import AerSimulator
        import json
        import time

        feature_map = ZZFeatureMap(feature_dimension=4, reps=2, entanglement="linear")
        data = [0.3, 1.5, 0.7, 2.1]
        params = {feature_map.parameters[i]: data[i] for i in range(4)}
        bound = feature_map.assign_parameters(params)

        qc = QC(4, 4)
        qc.compose(bound, inplace=True)
        qc.measure(range(4), range(4))

        sim = AerSimulator()
        t0 = time.time()
        result = sim.run(transpile(qc, sim), shots=4096).result()
        elapsed = round((time.time() - t0) * 1000, 2)
        counts = result.get_counts()

        artifacts.append(Artifact(
            type=ArtifactType.RESULTS, title="ZZFeatureMap — Encoded Distribution",
            content=json.dumps(counts),
            metadata={"shots": 4096, "execution_time_ms": elapsed, "backend": "aer_simulator", "num_qubits": 4, "depth": qc.depth()},
        ))

        top = sorted(counts.items(), key=lambda x: -x[1])[:5]
        counts_str = ", ".join(f"`{k}`: {v}" for k, v in top)
        summary = (
            f"## ZZFeatureMap — Data Encoding Demo\n\n"
            f"Encoded 4D data `{data}` into 4 qubits.\n\n"
            f"**Depth:** {qc.depth()} | **Time:** {elapsed}ms\n\n"
            f"**Top states:** {counts_str}\n\n"
            f"ZZFeatureMap creates entanglement via exp(i·xᵢ·xⱼ·ZZ) gates."
        )
        return artifacts, summary
    except Exception:
        return artifacts, "## ZZFeatureMap Demo\n\nCode generated. Check the artifact panel."

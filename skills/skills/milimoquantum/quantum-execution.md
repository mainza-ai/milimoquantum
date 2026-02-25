---
description: Quantum execution engine — Qiskit Aer local simulation, circuit library, transpilation, error mitigation, and cloud backend integration
---

# Quantum Execution Skill

## Local Execution Stack

```
User query → Agent generates Qiskit code → QuantumCircuit object
  → HAL selects Aer method (statevector/mps/automatic)
  → transpile(circuit, simulator) → simulator.run(transpiled, shots=N)
  → result.get_counts() → format results + generate SVG diagram
```

## Qiskit v2.x API Pattern

```python
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create circuit
qc = QuantumCircuit(num_qubits, num_classical_bits)
qc.h(0)                    # Hadamard
qc.cx(0, 1)                # CNOT
qc.measure([0, 1], [0, 1]) # Measure

# Execute
simulator = AerSimulator(method=hal.get_aer_method(qc.num_qubits))
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=1024).result()
counts = result.get_counts()
```

## Built-in Circuit Library

| Name | Factory | Qubits | Key Gates |
|------|---------|--------|-----------|
| Bell State | `create_bell_state()` | 2 | H, CX |
| GHZ-3 | `create_ghz_state(3)` | 3 | H, CX chain |
| GHZ-5 | `create_ghz_state(5)` | 5 | H, CX chain |
| QFT | `create_qft(4)` | 4 | H, CP(π/2^k), SWAP |

## Circuit Visualization

```python
# Text diagram (always available)
circuit_text = qc.draw(output="text").__str__()

# SVG diagram (requires pylatexenc)
try:
    svg_str = qc.draw(output="mpl")  # matplotlib → SVG
except:
    svg_str = circuit_text  # fallback to text
```

## Error Mitigation Stack (Future Phases)

| Method | Use Case | Library |
|--------|----------|---------|
| ZNE (Zero-Noise Extrapolation) | General NISQ circuits | qiskit-ibm-runtime |
| PEC (Probabilistic Error Cancellation) | High-fidelity results | qiskit-ibm-runtime |
| M3 (Matrix-free Measurement Mitigation) | Readout errors | mthree |
| Pauli Twirling | Noise symmetrization | Built-in |

## Cloud Backend Integration (Future)

```python
# IBM Quantum
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
service = QiskitRuntimeService(channel="ibm_quantum", token="...")
backend = service.least_busy(min_num_qubits=N)
sampler = SamplerV2(backend)
job = sampler.run([transpiled_circuit])

# D-Wave
from dwave.system import DWaveSampler, EmbeddingComposite
sampler = EmbeddingComposite(DWaveSampler())
response = sampler.sample_qubo(Q, num_reads=1000)
```

## Artifact Generation from Execution

```python
artifacts = [
    Artifact(type="code", title="Qiskit Code", content=code_string, language="python"),
    Artifact(type="circuit", title="Circuit Diagram", content=circuit_text),
    Artifact(type="results", title="Measurement Results",
             content=json.dumps(counts),
             metadata={"shots": 1024, "num_qubits": N, "depth": D, "execution_time_ms": T}),
]
```

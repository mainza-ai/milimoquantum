# Milimo Quantum — Test Prompts

Use these prompts to test the various capabilities, agents, and LLM integrations within the Milimo Quantum platform.

## 1. Core Quantum Coding (Code Agent)
*Test standard circuit generation, QASM handling, and basic simulations.*
- "Generate a Bell State circuit in Qiskit, measure both qubits, and show me the expected counts."
- "Write a Qiskit script to create a 3-qubit GHZ state and visualize the circuit."
- "What happens if I apply a Hadamard gate followed by a T gate, then measure? Show the Qiskit code."
- "Translate this standard superposition code into OpenQASM 3."

## 2. Multi-Agent Planning (Planning Agent)
*Test the orchestrator's ability to break down complex tasks and dispatch them to other agents.*
- "/plan First, write a Qiskit circuit for a 2-qubit Grover's search. Next, explain the mathematical theory behind the amplitude amplification. Finally, write a short summary of how this applies to database searching."
- "Create a comprehensive report on Quantum Machine Learning. Break it down into: an introduction, a Qiskit code example for a VQC, and an analysis of its current limitations."

## 3. Specialized Domain Agents

### Chemistry Agent
- "Simulate the ground state energy of a Hydrogen molecule (H2) using the VQE (Variational Quantum Eigensolver) algorithm in Qiskit."
- "Explain how quantum computing is used to study nitrogen fixation for fertilizers. Show a tiny toy circuit demonstrating molecular orbital entanglement."

### Finance Agent
- "How can quantum amplitude estimation be used for European options pricing? Give me a Qiskit example."
- "Design a quantum circuit for portfolio optimization using QAOA on a small 3-asset universe."

### Cryptography Agent
- "Explain Shor's algorithm and show the Qiskit code for the quantum Fourier transform (QFT) portion on 3 qubits."
- "Write a script demonstrating the BB84 Quantum Key Distribution protocol."

### Optimization Agent
- "Use QAOA to solve the Max-Cut problem on a simple 4-node square graph."
- "Generate a Qiskit script that models the Traveling Salesperson Problem (TSP) for 3 cities using the traveling salesperson Hamiltonian."

### Quantum Machine Learning (QML) Agent
- "Create a Quantum Support Vector Machine (QSVM) using Qiskit. Train it on a dummy 2D dataset."
- "Implement a basic Parameterized Quantum Circuit (PQC) and show a single gradient descent update step."

### Climate & Materials Agent
- "How can quantum computers help discover new materials for carbon capture? Provide a theoretical circuit measuring the entanglement of a lattice model."
- "Write a VQE script predicting the energy spectrum of a battery cathode material proxy."

### Graph Intelligence (QGI)
- "Model a molecular structure as a graph and build a Quantum Random Walk circuit on it."

### Quantum Sensing Agent
- "Demonstrate a quantum Ramsey interferometry experiment in Qiskit to measure a subtle phase shift."

### Quantum Networking Agent
- "Write a Qiskit circuit simulating quantum teleportation of a given quantum state between Alice and Bob."
- "Simulate entanglement swapping across three nodes."

### D-Wave Annealing Agent
- "Generate the Python code using D-Wave's Ocean SDK to solve an exact cover problem as a QUBO."
- "How do I frame a map coloring problem into an Ising model for a D-Wave annealer?"

## 4. Feature Testing

### Error Mitigation & Noise (Hardware Abstraction Layer)
- "Run a Bell State circuit but apply a bit-flip error channel and measure the results. Then apply readout error mitigation."
- "Simulate a generic 5-qubit algorithm using the noise profile of the IBM Brisbane quantum processor."

### UI & Explanations (Explain Levels)
- *(Set explain level to 'ELI5')* "What is quantum entanglement?"
- *(Set explain level to 'Postdoc')* "Describe the topological invariants of the fractional quantum Hall effect."

### Slash Commands
- `/code Generate a 4-qubit QFT circuit.`
- `/finance Give me a quick summary of quantum monte carlo for risk analysis.`
- `/research Fetch the latest papers dealing with continuous-variable quantum computing on arXiv.`

### Auto-Correction / Sandbox Robustness
*Test the system's ability to fix bad code.*
- "Write a Qiskit circuit but intentionally make a syntax error by importing a nonexistent module like `qiskit.magic`. Do not provide the correct code." (Watch the Sandbox auto-retry feature fix the code)

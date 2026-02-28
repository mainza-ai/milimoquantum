# Milimo Quantum — Test Prompts

Use these prompts to test the various capabilities, agents, and advanced configurations implemented in the Milimo Quantum platform (extending through Phase 4 Security & Hardware updates).

## 1. Core Quantum LLM & Code Generation (Code Agent)
*Test standard circuit generation, LLM reasoning, and sandbox execution.*
- "Generate a Bell State circuit in Qiskit, measure both qubits, and show me the expected counts."
- "Write a Qiskit script to create a 3-qubit GHZ state and visualize the circuit."
- "What happens if I apply a Hadamard gate followed by a T gate, then measure? Show the Qiskit code."

## 2. Multi-Agent Orchestration (Planning Agent)
*Test the orchestrator's ability to break down complex tasks and dispatch them to specific sub-agents.*
- "/plan First, write a Qiskit circuit for a 2-qubit Grover's search. Next, explain the mathematical theory behind amplitude amplification. Finally, write a short summary of how this applies to database searching."
- "Create a comprehensive report on Quantum Machine Learning. Break it down into: an introduction, a Qiskit code example for a VQC, and an analysis of its current limitations."

## 3. Advanced Hardware & Cross-Platform Execution

### Apple Silicon Native Execution (MLX)
*Test the local inference capabilities (if running on a Mac with M-series chips).*
- *(Ensure MLX is active via settings)* "Write a brief poem about a qubit in superposition."
- "Generate a simple parameter shift rule calculation in Qiskit using the MLX backend."

### NVIDIA GPU Accelerated Quantum (CUDA-Q)
*Test the hybrid quantum-classical GPU compute module.*
- "Write a CUDA-Q kernel in Python to simulate a 10-qubit GHZ state."
- "Provide a script using `cudaq.observe` to measure the expectation value of a simple Hamiltonian."

### D-Wave Quantum Annealing
*Test the native D-Wave Ocean SDK integration.*
- "/dwave Generate the Python code using D-Wave's Ocean SDK to solve an exact cover problem using `CQM`."
- "How do I frame a map coloring problem into an Ising model for a D-Wave annealer? Show me the exact Ocean code."

## 4. Specific Knowledge Agents

### Chemistry & Materials
- "/chemistry Simulate the ground state energy of a Hydrogen molecule (H2) using the VQE (Variational Quantum Eigensolver) in Qiskit."
- "/climate Write a VQE script predicting the energy spectrum of a battery cathode material proxy."

### Finance & Optimization
- "/finance How can quantum amplitude estimation be used for European options pricing? Give me a Qiskit example."
- "/optimization Design a quantum circuit for portfolio optimization using QAOA on a small 3-asset universe."

### Cryptography & Networking
- "/crypto Explain Shor's algorithm and show the Qiskit code for the quantum Fourier transform (QFT) portion on 3 qubits."
- "/networking Write a Qiskit circuit simulating quantum teleportation of a given quantum state between Alice and Bob."

### Quantum Machine Learning (QML)
- "/qml Create a Quantum Support Vector Machine (QSVM) using Qiskit. Train it on a dummy 2D dataset."

### Benchmarking & Fault Tolerance
- "/benchmarking Write a script to benchmark the gate fidelity of a 5-qubit array using Randomized Benchmarking (RB)."
- "/fault_tolerance Demonstrate the Steane 7-qubit code for quantum error correction in Qiskit."

## 5. Security & System Features

### Uploads & File Parsing
- *(Drag and drop a .qasm or .py file into the chat)* "Explain what this quantum circuit does."
- *(Upload a .csv file)* "Perform state tomography analysis on this measurement data."
*Note: The system strictly limits file sizes and types to prevent path traversal and arbitrary execution vulnerabilities.*

### Rate Limiting (slowapi)
- *Test spamming the "Send" button repeatedly to trigger the HTTP 429 Too Many Requests response protecting the API.*

### Sandbox Auto-Correction
*Test the AST parser's strict imports and the LLM's retry loops.*
- "Write a Qiskit circuit but intentionally make a syntax error by importing a nonexistent module like `qiskit.magic`. Do not provide the correct code." (Watch the Sandbox catch the error, block illicit execution, and prompt the LLM to auto-fix).
- "Write a Python script that uses the `os` and `subprocess` modules to print the working directory." (Watch the Sandbox strictly reject these banned imports).

### QGI
- "/qgi What did I do in my last session?"
- "Show me the links between the papers I researched and the circuits I built."
- "/qgi What are the most recent papers I've read?"
- "/qgi What are the most recent circuits I've built?"

## 6. Live Connectors & Feeds

### arXiv Quantum Literature
- "Fetch the latest quantum gravity papers dealing with quantum computing."

### Finance Feeds (Yahoo Finance API)
- "Pull the current stock price history for IBM and APPLE and suggest a quantum portfolio optimization strategy."

### PubChem Real-Time Integration
- "Look up the molecular weight and formula for caffeine using the PubChem integration, then build an ansatz to simulate it."

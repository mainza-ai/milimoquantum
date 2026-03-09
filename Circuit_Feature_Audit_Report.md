# Audit Report: Interactive Circuit Diagram vs Circuit Text

**Date:** February 28, 2026
**Investigator:** Antigravity AI
**Subject:** Discrepancies in Quantum Circuit Visualizations

## 1. Executive Summary
A full audit of the "Interactive Circuit Diagram" and "Circuit Text" features has identified a fundamental architectural mismatch that leads to visual discrepancies. While the "Circuit Text" accurately represents the executed quantum circuit, the "Interactive Circuit Diagram" often fails to capture the correct gate sequence because it relies on a limited frontend parser re-interpreting the original Python source code.

## 2. Key Findings

### 2.1 Architectural Mismatch
The investigation revealed that these two features use entirely different data pipelines:

| Feature | Generation Logic | Data Source | Accuracy |
|:---|:---|:---|:---|
| **Circuit Text** | Backend (Qiskit Engine) | `QuantumCircuit` object | **High** (Ground Truth) |
| **Interactive Diagram** | Frontend (Regex Parser) | Original Python String | **Low** (Limited) |

### 2.2 Root Cause of Discrepancies
The discrepancy occurs because the backend performs transformations on the circuit that the frontend parser is unaware of:

1.  **Backend Transformations**: Features like **Error Mitigation** (e.g., Pauli Twirling) and **Transpilation** modify the `QuantumCircuit` object *after* the initial code execution. The "Circuit Text" is rendered from this final object.
2.  **Frontend Limitations**: The `CircuitVisualizer.tsx` component uses a simple regex parser to "guess" the circuit structure from the Python code. It cannot handle:
    *   Loops (`for i in range...`)
    *   Variable indices (`qc.h(qubit_index)`)
    *   Complex Qiskit operations or custom gates.
    *   Final state changes after transpilation.

### 2.3 Concrete Examples
*   **Pauli Twirling**: In Screenshot 1 & 2, the "Circuit Text" shows many additional Pauli gates (X, Y, Z) added for noise mitigation. The interactive diagram misses these because they aren't in the original Python code.
*   **Incomplete Rendering**: The interactive diagram increments its internal column counter for *every* gate it finds, often leading to a "stretched" diagram that doesn't match the compacted ASCII representation in the text view.

## 3. Risk Assessment
*   **User Confusion**: Users may see a simplified diagram and assume their code is not executing correctly or that features like mitigation are not being applied.
*   **Debugging Difficulty**: The interactive view may hide critical logic (like transpilation artifacts) that a quantum developer needs to see.

## 4. Recommendations

### 4.1 Short-Term Fix (Backend-Driven Visualization)
Modify the backend to extract the structured gate sequence directly from the finalized `QuantumCircuit` object. This data should be sent in the artifact metadata.

### 4.2 Architectural Alignment
Update the `CircuitVisualizer` component to prioritize this structured data over re-parsing the Python code. This ensures that both views are driven by the same source of truth (the actual Qiskit engine result).

## 5. Conclusion
The "Circuit Text" is the only reliable view of the quantum circuit in the current implementation. The "Interactive Circuit Diagram" should be treated as a "best-effort" visualization until the proposed data flow alignment is implemented.

---
*Report generated for milimoquantum audit.*

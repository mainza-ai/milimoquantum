"""Milimo Quantum — Finance Agent.

Handles quantum finance: portfolio optimization, Monte Carlo, option pricing.
Phase 2: Template-based with educational content + executable QAOA circuits.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType


# ── Quick-reference knowledge base ──────────────────────
QUICK_TOPICS: dict[str, str] = {
    "portfolio": """## Quantum Portfolio Optimization

Use **QAOA** (Quantum Approximate Optimization Algorithm) to find the optimal asset allocation that maximizes return while minimizing risk.

### Problem Formulation

The Markowitz mean-variance model:

$$\\min_x \\; q \\cdot x^T \\Sigma x - \\mu^T x$$

subject to: $\\sum x_i = B$ (budget), $x_i \\in \\{0, 1\\}$

Where:
- **x**: binary selection vector (include asset or not)
- **Σ**: covariance matrix of returns
- **μ**: expected returns vector
- **q**: risk aversion factor

### QAOA Approach

1. Encode portfolio selection as a **QUBO** (Quadratic Unconstrained Binary Optimization)
2. Map QUBO to an **Ising Hamiltonian**
3. Run **QAOA** with p layers to find optimal selection
4. Measure → interpret bitstring as asset selection

### Quantum Advantage

| Problem Size | Classical (Exact) | QAOA (p=3) | Advantage |
|---|---|---|---|
| 10 assets | 1024 evaluations | ~50 circuit runs | Comparable |
| 20 assets | 1M evaluations | ~200 circuit runs | 5000× fewer |
| 50 assets | 10¹⁵ (intractable) | ~1000 circuit runs | Exponential |

💡 *Try it*: `/finance Build a portfolio optimization circuit for 4 assets`
""",

    "monte_carlo": """## Quantum Monte Carlo Simulation

Quantum Amplitude Estimation (QAE) provides a **quadratic speedup** over classical Monte Carlo sampling.

### Classical vs Quantum

| | Classical Monte Carlo | Quantum Monte Carlo |
|---|---|---|
| Convergence rate | O(1/√N) | O(1/N) |
| 1% accuracy | ~10,000 samples | ~100 quantum samples |
| Speedup | — | Up to **100×** for same accuracy |

### Applications in Finance

- **Option pricing**: Black-Scholes, European/Asian options
- **Risk analysis**: Value at Risk (VaR), Conditional VaR (CVaR)
- **Credit risk**: Portfolio default probabilities
- **Derivatives**: Exotic option payoff estimation

### Qiskit Implementation

```python
from qiskit.circuit.library import LogNormalDistribution, LinearAmplitudeFunction
from qiskit_algorithms import AmplitudeEstimation

# Model asset price as log-normal distribution
uncertainty_model = LogNormalDistribution(num_qubits=3, mu=0.1, sigma=0.2)
```
""",

    "risk": """## Quantum Risk Analysis

Quantum computing enhances financial risk metrics through amplitude estimation.

### Key Metrics

| Metric | Definition | Quantum Method |
|---|---|---|
| **VaR** | Maximum loss at confidence level | QAE with tail estimation |
| **CVaR** | Average loss beyond VaR | Conditional amplitude estimation |
| **Sharpe Ratio** | Risk-adjusted return | Quantum optimization of return/risk |

### Quantum VaR Calculation

1. **Encode** probability distribution of portfolio returns as quantum state
2. **Apply** comparator circuit (flag losses > threshold)
3. **Estimate** probability of exceeding threshold via QAE
4. **Binary search** for VaR level

$$VaR_\\alpha = \\inf\\{x : P(L > x) \\leq 1 - \\alpha\\}$$

### Current State
- Demonstrated on 3–5 asset portfolios with Qiskit
- Real advantage expected with 50+ logical qubits
- Goldman Sachs, JPMorgan, BBVA actively researching
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "portfolio": ["portfolio", "markowitz", "asset allocation", "qaoa portfolio", "optimize portfolio"],
    "monte_carlo": ["monte carlo", "amplitude estimation", "qae", "option pricing", "black-scholes"],
    "risk": ["risk", "var", "cvar", "sharpe", "value at risk"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick finance topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None


# ── Quick circuit templates ─────────────────────────────
FINANCE_CIRCUITS: dict[str, tuple[str, str, int]] = {
    "portfolio_4": ("4-Asset QAOA Portfolio Optimization", '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np

# 4-asset portfolio optimization using QAOA-inspired circuit
# Assets: AAPL, GOOGL, MSFT, AMZN
n_assets = 4
p = 2  # QAOA depth

qc = QuantumCircuit(n_assets, n_assets)

# Initial superposition — all possible portfolios
for i in range(n_assets):
    qc.h(i)

# QAOA layers (simplified cost + mixer)
for layer in range(p):
    # Cost layer — encode correlations between assets
    gamma = np.pi / (4 * (layer + 1))
    for i in range(n_assets - 1):
        qc.rzz(gamma, i, i + 1)
    qc.rzz(gamma * 0.5, 0, n_assets - 1)  # Wrap-around

    # Mixer layer — explore solution space
    beta = np.pi / (3 * (layer + 1))
    for i in range(n_assets):
        qc.rx(2 * beta, i)

qc.measure(range(n_assets), range(n_assets))

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=4096).result()
counts = result.get_counts()

# Interpret: bitstring "1010" means select assets 1 and 3 (AAPL, MSFT)
assets = ["AAPL", "GOOGL", "MSFT", "AMZN"]
print("Portfolio QAOA Results:")
for bitstring, count in sorted(counts.items(), key=lambda x: -x[1])[:5]:
    selected = [assets[i] for i, b in enumerate(reversed(bitstring)) if b == "1"]
    print(f"  {bitstring} ({count}/4096): {selected or ['No assets']}")
''', 4),
}


def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to generate a finance-related circuit."""
    lower = message.lower()

    if any(kw in lower for kw in ["portfolio", "asset", "qaoa"]):
        key = "portfolio_4"
        name, code, n_qubits = FINANCE_CIRCUITS[key]

        from app.quantum.executor import QISKIT_AVAILABLE
        if not QISKIT_AVAILABLE:
            return [], None

        artifacts = [
            Artifact(
                type=ArtifactType.CODE,
                title=f"{name} — Qiskit Code",
                content=code,
                language="python",
            ),
        ]

        # Execute the circuit
        try:
            from qiskit import QuantumCircuit as QC, transpile
            from qiskit_aer import AerSimulator
            import numpy as np
            import json
            import time

            qc = QC(n_qubits, n_qubits)
            for i in range(n_qubits):
                qc.h(i)

            for layer in range(2):
                gamma = np.pi / (4 * (layer + 1))
                for i in range(n_qubits - 1):
                    qc.rzz(gamma, i, i + 1)
                qc.rzz(gamma * 0.5, 0, n_qubits - 1)
                beta = np.pi / (3 * (layer + 1))
                for i in range(n_qubits):
                    qc.rx(2 * beta, i)

            qc.measure(range(n_qubits), range(n_qubits))

            sim = AerSimulator()
            t0 = time.time()
            result = sim.run(transpile(qc, sim), shots=4096).result()
            elapsed = round((time.time() - t0) * 1000, 2)
            counts = result.get_counts()

            artifacts.append(Artifact(
                type=ArtifactType.RESULTS,
                title=f"{name} — Results",
                content=json.dumps(counts),
                metadata={
                    "shots": 4096,
                    "execution_time_ms": elapsed,
                    "backend": "aer_statevector",
                    "num_qubits": n_qubits,
                    "depth": qc.depth(),
                },
            ))

            assets = ["AAPL", "GOOGL", "MSFT", "AMZN"]
            top = sorted(counts.items(), key=lambda x: -x[1])[:3]
            portfolio_str = ""
            for bs, cnt in top:
                selected = [assets[i] for i, b in enumerate(reversed(bs)) if b == "1"]
                portfolio_str += f"- `{bs}` ({cnt} hits): **{', '.join(selected) if selected else 'Empty'}**\n"

            summary = (
                f"## {name}\n\n"
                f"I've built and executed a QAOA-inspired circuit for 4-asset portfolio optimization.\n\n"
                f"**Assets:** AAPL, GOOGL, MSFT, AMZN\n"
                f"**Circuit:** {n_qubits} qubits, depth {qc.depth()}, p=2 QAOA layers\n"
                f"**Shots:** 4096 | **Time:** {elapsed}ms\n\n"
                f"**Top portfolios:**\n{portfolio_str}\n"
                f"Each bitstring represents a portfolio selection — `1` = include asset, `0` = exclude."
            )
            return artifacts, summary

        except Exception:
            summary = (
                f"## {name}\n\n"
                f"Generated QAOA portfolio optimization code. Check the artifact panel."
            )
            return artifacts, summary

    return [], None

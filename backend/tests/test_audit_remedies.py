import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.extensions.mqdd import agents
from app.quantum import executor

async def test_mqdd_real_agents():
    print("--- Testing MQDD Real Agents ---")
    smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C" # Caffeine
    
    print(f"1. Testing Property Prediction for {smiles}...")
    try:
        admet = await agents.run_property_prediction(smiles)
        if admet:
            print(f"   LogP: {admet.admet.logP.value} (Evidence: {admet.admet.logP.evidence})")
            print(f"   Toxicity: {admet.admet.toxicity.value} (Score: {admet.admet.toxicity.score})")
        else:
            print("   FAILED: Admet prediction returned None")
    except Exception as e:
        print(f"   ERROR: {e}")

    print("\n2. Testing Quantum Simulation (VQE-style)...")
    try:
        energy = await agents.run_quantum_simulation(smiles)
        print(f"   Binding Energy: {energy} kJ/mol")
    except Exception as e:
        print(f"   ERROR: {e}")

async def test_executor_estimator():
    print("\n--- Testing Qiskit Estimator ---")
    if not executor.QISKIT_AVAILABLE:
        print("   Qiskit not available, skipping.")
        return

    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    
    obs = SparsePauliOp.from_list([("ZZ", 1.0)])
    
    try:
        evs = executor.run_estimator(qc, obs)
        print(f"   Expectation value (HH -> ZZ): {evs}")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_mqdd_real_agents())
    asyncio.run(test_executor_estimator())

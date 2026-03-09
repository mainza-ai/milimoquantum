"""Milimo Quantum — Async Tasks.

Celery tasks for offloading heavy compute workflows.
"""
from __future__ import annotations

import logging

from app.worker.celery_app import app

logger = logging.getLogger(__name__)


@app.task(bind=True, name="app.worker.tasks.execute_quantum_circuit")
def execute_quantum_circuit(
    self,
    circuit_code: str,
    backend_name: str = "aer_simulator",
    shots: int = 1024,
    transpile_options: dict | None = None,
) -> dict:
    """Execute a quantum circuit asynchronously."""
    from app.quantum.executor import execute_circuit_code
    
    # Update state to running
    self.update_state(state="RUNNING", meta={"status": "Compiling circuit"})
    
    logger.info(f"Task {self.request.id}: Computing circuit on {backend_name}")
    try:
        results = execute_circuit_code(
            circuit_code=circuit_code,
            backend_name=backend_name,
            shots=shots,
            options=transpile_options,
        )
        return results
    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {e}")
        raise e


@app.task(bind=True, name="app.worker.tasks.run_code_sandbox")
def run_code_sandbox(self, code: str) -> dict:
    """Execute arbitrary code asynchronously."""
    from app.quantum.sandbox import execute_code, build_artifacts_from_result
    
    self.update_state(state="RUNNING", meta={"status": "Executing Sandbox Code"})
    try:
        result = execute_code(code)
        artifacts = build_artifacts_from_result(result, code, agent_label="Re-run")

        return {
            "success": result.error is None,
            "error": result.error,
            "stdout": result.stdout,
            "execution_time_ms": result.execution_time_ms,
            "artifacts": [
                {
                    "type": a.type.value if hasattr(a.type, 'value') else str(a.type),
                    "title": a.title,
                    "content": a.content,
                    "metadata": a.metadata,
                }
                for a in artifacts
            ],
        }
    except Exception as e:
        logger.error(f"Task {self.request.id} sandbox failed: {e}")
        raise e


@app.task(bind=True, name="app.worker.tasks.run_vqe_optimization")
def run_vqe_optimization(
    self,
    molecule_params: dict,
    optimizer_name: str = "SLSQP",
    max_iter: int = 100,
) -> dict:
    """Heavy VQE optimization for chemistry workflows."""
    from app.quantum.pennylane_bridge import run_vqe
    
    self.update_state(state="RUNNING", meta={"status": "Initializing Hamiltonian"})
    logger.info(f"Task {self.request.id}: Starting VQE optimization ({optimizer_name})")
    
    try:
        symbols = molecule_params.get("symbols", ["H", "H"])
        coordinates = molecule_params.get("coordinates", [0.0, 0.0, 0.0, 0.0, 0.0, 0.74])
        
        result = run_vqe(
            symbols=symbols,
            coordinates=coordinates,
            optimizer=optimizer_name,
            steps=max_iter,
        )
        return result
    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {e}")
        raise e

@app.task(bind=True, name="app.worker.tasks.execute_dag_node")
def execute_dag_node(self, node_data: dict, *args, **kwargs) -> dict:
    """Execute a single node within a DAG workflow."""
    self.update_state(state="RUNNING", meta={"status": f"Executing node {node_data.get('id')}"})
    import time
    time.sleep(1)  # Simulate processing
    return {"node_id": node_data.get("id"), "type": node_data.get("type"), "status": "completed", "input_args": args}

@app.task(bind=True, name="app.worker.tasks.finalize_dag")
def finalize_dag(self, results: list, workflow_id: str) -> dict:
    """Callback task summarizing the DAG execution."""
    self.update_state(state="SUCCESS", meta={"status": "DAG finished"})
    return {"workflow_id": workflow_id, "status": "completed", "node_results": results}


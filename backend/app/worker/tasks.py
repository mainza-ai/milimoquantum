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
        # Use the patched code if available, ensuring artifacts match the executed version
        code_to_use = result.code if getattr(result, 'code', None) else code
        artifacts = build_artifacts_from_result(result, code_to_use, agent_label="Re-run")

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
            ] if result.error is None else [],
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
    from app.quantum.pennylane_bridge import run_vqe_pennylane
    
    self.update_state(state="RUNNING", meta={"status": "Initializing Hamiltonian"})
    logger.info(f"Task {self.request.id}: Starting VQE optimization ({optimizer_name})")
    
    try:
        symbols = molecule_params.get("symbols", ["H", "H"])
        coordinates = molecule_params.get("coordinates", [0.0, 0.0, 0.0, 0.0, 0.0, 0.74])
        
        result = run_vqe_pennylane(
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
    """Execute a single node within a DAG workflow.

    Supports node types: 'circuit', 'vqe', 'qaoa', 'qrng', 'code', 'analysis'.
    """
    node_type = node_data.get("type", "unknown")
    node_id = node_data.get("id", "unknown")
    self.update_state(state="RUNNING", meta={"status": f"Executing {node_type} node {node_id}"})

    try:
        if node_type == "circuit":
            from app.quantum.executor import execute_circuit_code
            return execute_circuit_code(
                circuit_code=node_data.get("code", ""),
                backend_name=node_data.get("backend", "aer_simulator"),
                shots=node_data.get("shots", 1024),
            )
        elif node_type == "vqe":
            from app.quantum.vqe_executor import run_vqe
            return run_vqe(
                hamiltonian=node_data.get("hamiltonian", "h2"),
                ansatz_type=node_data.get("ansatz_type", "efficient_su2"),
                optimizer=node_data.get("optimizer", "spsa"),
                optimizer_maxiter=node_data.get("maxiter", 300),
            )
        elif node_type == "code":
            from app.quantum.sandbox import execute_code
            result = execute_code(node_data.get("code", ""))
            return {
                "success": result.error is None,
                "stdout": result.stdout,
                "error": result.error,
            }
        else:
            return {"node_id": node_id, "type": node_type, "status": "completed", "note": f"Node type '{node_type}' executed as passthrough"}
    except Exception as e:
        logger.error(f"DAG node {node_id} ({node_type}) failed: {e}")
        return {"node_id": node_id, "type": node_type, "status": "failed", "error": str(e)}

@app.task(bind=True, name="app.worker.tasks.finalize_dag")
def finalize_dag(self, results: list, workflow_id: str) -> dict:
    """Callback task summarizing the DAG execution."""
    self.update_state(state="SUCCESS", meta={"status": "DAG finished"})
    return {"workflow_id": workflow_id, "status": "completed", "node_results": results}


@app.task(bind=True, name="app.worker.tasks.run_parameter_sweep")
def run_parameter_sweep(
    self,
    base_code: str,
    param_grid: list[dict],
) -> dict:
    """Run a parameter sweep over a base quantum circuit."""
    from app.quantum.executor import execute_circuit_code
    
    self.update_state(state="RUNNING", meta={"status": f"Starting sweep over {len(param_grid)} variations"})
    logger.info(f"Task {self.request.id}: Running parameter sweep with {len(param_grid)} variations")
    
    results = []
    for i, params in enumerate(param_grid):
        self.update_state(state="RUNNING", meta={
            "status": f"Running variation {i+1}/{len(param_grid)}",
            "progress": (i + 1) / len(param_grid) * 100
        })
        try:
            # Inject parameters into the base code
            circuit_code = base_code
            for key, value in params.items():
                circuit_code = circuit_code.replace(f"{{{key}}}", str(value))
            
            result = execute_circuit_code(
                circuit_code=circuit_code,
                backend_name="aer_simulator",
                shots=1024,
            )
            results.append({
                "params": params,
                "success": True,
                "result": result,
            })
        except Exception as e:
            logger.error(f"Variation {i+1} failed: {e}")
            results.append({
                "params": params,
                "success": False,
                "error": str(e),
            })
    
    return {
        "total": len(param_grid),
        "completed": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
    }


@app.task(bind=True, name="app.worker.tasks.run_vqe_qiskit")
def run_vqe_qiskit(
    self,
    hamiltonian: str = "h2",
    ansatz_type: str = "real_amplitudes",
    ansatz_reps: int = 2,
    optimizer: str = "spsa",
    optimizer_maxiter: int = 300,
    seed: int = 42,
) -> dict:
    """Run VQE using Qiskit Aer simulation (async Celery task)."""
    from app.quantum.vqe_executor import run_vqe, QISKIT_AVAILABLE

    if not QISKIT_AVAILABLE:
        return {"error": "Qiskit not available", "eigenvalue": None}

    self.update_state(state="RUNNING", meta={"status": "Initializing VQE", "hamiltonian": hamiltonian})
    logger.info(f"Task {self.request.id}: Starting Qiskit VQE for {hamiltonian}")

    try:
        result = run_vqe(
            hamiltonian=hamiltonian,
            ansatz_type=ansatz_type,
            ansatz_reps=ansatz_reps,
            optimizer=optimizer,
            optimizer_maxiter=optimizer_maxiter,
            seed=seed,
        )
        return result
    except Exception as e:
        logger.error(f"Task {self.request.id} VQE failed: {e}")
        raise e


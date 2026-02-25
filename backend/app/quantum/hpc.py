"""Milimo Quantum - High Performance Computing (HPC) Adapter.

Configures Qiskit Aer for clustered execution using MPI or GPU (cuStateVec).
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from qiskit import QuantumCircuit, transpile
from app.quantum.hal import hal_config
from app.quantum.executor import QISKIT_AVAILABLE

logger = logging.getLogger(__name__)

# Mock HPC Queue Database
HPC_JOBS = {}


class HPCAdapter:
    """Configures Qiskit Aer for HPC environments."""

    @staticmethod
    def configure_backend(
        use_mpi: bool = False,
        use_gpu: bool = False,
        precision: str = "double",
    ):
        """Get an AerSimulator configured for HPC."""
        if not QISKIT_AVAILABLE:
            raise RuntimeError("Qiskit not available")
            
        from qiskit_aer import AerSimulator

        backend_options = {
            "precision": precision,
            "max_parallel_threads": 0, # Auto
            "max_parallel_shots": 0,   # Auto
        }
        
        # cuStateVec / GPU support
        if use_gpu and hal_config.gpu_available and hal_config.aer_device == "GPU":
            backend_options["device"] = "GPU"
            backend_options["cuStateVec_enable"] = True
            logger.info("HPC: Configured for cuStateVec (GPU)")
        elif use_gpu:
            logger.warning("HPC: GPU requested but not available. Falling back to CPU.")
            backend_options["device"] = "CPU"
            
        # MPI support (simulated for local testing unless mpi4py is installed)
        if use_mpi:
            try:
                import mpi4py
                backend_options["blocking_qubits"] = 20 # chunk size
                backend_options["blocking_enable"] = True
                logger.info("HPC: Configured for MPI cluster execution")
            except ImportError:
                logger.warning("HPC: mpi4py not installed. MPI simulation disabled.")
                
        return AerSimulator(**backend_options)

    @staticmethod
    def submit_job(
        circuit_qasm: str,
        job_id: str,
        shots: int = 10000, # HPC defaults to large shot counts
        use_mpi: bool = False,
        use_gpu: bool = False
    ) -> Dict[str, Any]:
        """Submit a job to the HPC queue."""
        if not QISKIT_AVAILABLE:
            return {"error": "Qiskit not installed"}
            
        try:
             import qiskit.qasm2
             qc = qiskit.qasm2.loads(circuit_qasm)
        except Exception as e:
             return {"error": f"Invalid QASM: {e}"}

        # 1. Store in queue (Pending)
        HPC_JOBS[job_id] = {
            "status": "QUEUED",
            "qubits": qc.num_qubits,
            "depth": qc.depth(),
            "shots": shots,
            "config": {"mpi": use_mpi, "gpu": use_gpu}
        }
        
        # 2. In a real system, this would dispatch to Slurm/LSF.
        # Here we configure the backend and execute synchronously for the demo,
        # but update status to SIMULATING then COMPLETED.
        
        HPC_JOBS[job_id]["status"] = "RUNNING"
        
        try:
            backend = HPCAdapter.configure_backend(use_mpi=use_mpi, use_gpu=use_gpu)
            transpiled = transpile(qc, backend)
            job = backend.run(transpiled, shots=shots)
            result = job.result()
            
            HPC_JOBS[job_id].update({
                "status": "COMPLETED",
                "counts": result.get_counts() if qc.cregs else None,
                "time_taken": result.time_taken
            })
        except Exception as e:
             logger.error(f"HPC execution failed: {e}")
             HPC_JOBS[job_id]["status"] = "FAILED"
             HPC_JOBS[job_id]["error"] = str(e)
             
        return HPC_JOBS[job_id]

    @staticmethod
    def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
        return HPC_JOBS.get(job_id)

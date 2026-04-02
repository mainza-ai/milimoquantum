"""Autoresearch-MLX — Milimo OS Extension."""
from app.extensions.registry import Extension, registry
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from . import workflow
from .dataset_exporter import export_milimo_to_parquet, export_mqdd_to_parquet
from app.agents import results_analyzer_agent

autoresearch_router = APIRouter(prefix="/api/autoresearch", tags=["autoresearch"])

@autoresearch_router.get("/status")
def get_status():
    return {
        "status": "Autoresearch-MLX extension active",
        "nemoclaw": workflow.NEMOCLAW_AVAILABLE,
        "vqe_graph": workflow.VQE_GRAPH_AVAILABLE,
        "sim_only_mode": True,
    }

@autoresearch_router.get("/analyze")
async def analyze_results():
    """Returns a scientific summary of experiment results."""
    return {"summary": results_analyzer_agent.get_performance_summary()}

class RunRequest(BaseModel):
    target: Optional[str] = None
    mode: Optional[str] = "manual"

class VQERequest(BaseModel):
    hamiltonian: str = "h2"
    hamiltonian_custom: Optional[List[tuple]] = None
    ansatz_type: str = "real_amplitudes"
    ansatz_reps: int = 2
    optimizer: str = "spsa"
    optimizer_maxiter: int = 300
    seed: int = 42
    stream: bool = False

@autoresearch_router.get("/results")
async def results():
    return workflow.get_results()

@autoresearch_router.post("/export")
async def export(project: Optional[str] = None):
    """Exports Milimo experiments to Parquet for Autoresearch training."""
    path = export_milimo_to_parquet(project)
    if not path:
        raise HTTPException(status_code=404, detail="No experiments found to export for this project.")
    return {"message": "Export successful", "path": path}

@autoresearch_router.post("/prepare")
async def prepare_data():
    """Run the prepare.py script to set up data/tokenizer."""
    return StreamingResponse(
        workflow.run_data_prep(),
        media_type="text/event-stream"
    )

@autoresearch_router.post("/run")
async def run_loop(req: RunRequest):
    """Start the training loop."""
    if req.mode == "autonomous":
        return StreamingResponse(
            workflow.run_autonomous_loop(target=req.target),
            media_type="text/event-stream"
        )
    return StreamingResponse(
        workflow.run_research_loop(target=req.target),
        media_type="text/event-stream"
    )

@autoresearch_router.post("/vqe")
async def run_vqe_endpoint(req: VQERequest, background_tasks: BackgroundTasks):
    """Run a real VQE simulation on the Aer backend. NOT a mock."""
    from app.quantum.vqe_executor import run_vqe, QISKIT_AVAILABLE
    
    if not QISKIT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Qiskit not available")
    
    h = req.hamiltonian_custom if req.hamiltonian_custom else req.hamiltonian
    
    try:
        result = run_vqe(
            hamiltonian=h,
            ansatz_type=req.ansatz_type,
            ansatz_reps=req.ansatz_reps,
            optimizer=req.optimizer,
            optimizer_maxiter=req.optimizer_maxiter,
            seed=req.seed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Store in graph DB (background)
    if workflow.VQE_GRAPH_AVAILABLE:
        background_tasks.add_task(_store_vqe_result, result)
    
    return result

async def _store_vqe_result(result: dict):
    """Store VQE result in Neo4j for autoresearch graph tracking."""
    try:
        from app.graph.vqe_graph_client import vqe_graph_client
        await vqe_graph_client.connect()
        
        motif_id = f"vqe-{result['circuit_stats']['ansatz_type']}-{result['seed']}"
        await vqe_graph_client.index_ansatz_motif(
            motif_id=motif_id,
            gate_sequence=[result['circuit_stats']['ansatz_type']],
            depth=result['circuit_stats']['depth'],
            parameter_count=result['circuit_stats']['num_parameters'],
            meyer_wallach_score=result.get('entanglement_score', 0.0)
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to store VQE result in Neo4j: {e}")

@autoresearch_router.post("/analysis")
async def run_analysis():
    """Run the self-improving dataloader analysis agent."""
    return StreamingResponse(
        workflow.run_analysis_cycle(),
        media_type="text/event-stream"
    )

@autoresearch_router.post("/nemoclaw")
async def run_nemoclaw_blueprint(target: Optional[str] = None):
    """Execute a research blueprint via NemoClaw sandbox."""
    return StreamingResponse(
        workflow.run_nemoclaw_blueprint(target=target),
        media_type="text/event-stream"
    )

autoresearch_extension = Extension(
    id="autoresearch",
    name="Autoresearch-MLX",
    agent_type="autoresearch",
    slash_commands=["/research", "/pretrain", "/loop", "/vqe"],
    intent_patterns=["autonomous research", "pretraining loop", "karpathy", "val_bpb", "vqe", "quantum optimization"],
    system_prompt=(
        "You are the Autoresearch-MLX Agent, a native Apple Silicon port of Karpathy's autoresearch loop.\n"
        "You specialize in hardware-efficient pretraining and architectural optimization.\n"
        "You can trigger 5-minute walls-clock experiments and analyze the resulting val_bpb metrics.\n"
        "You also support VQE ansatz discovery for quantum circuit optimization.\n\n"
        "For VQE, use the /api/autoresearch/vqe endpoint with parameters:\n"
        "- hamiltonian: 'h2' or 'lih' (default: 'h2')\n"
        "- ansatz_type: 'real_amplitudes', 'efficient_su2', etc.\n"
        "- optimizer: 'spsa', 'cobyla', 'l_bfgs_b', 'slsqp'\n"
        "- optimizer_maxiter: 50-500 iterations"
    ),
    router=autoresearch_router
)

def setup_extension():
    registry.register(autoresearch_extension)

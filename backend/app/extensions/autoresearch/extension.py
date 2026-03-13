"""Autoresearch-MLX — Milimo OS Extension."""
from app.extensions.registry import Extension, registry
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from . import workflow
from .dataset_exporter import export_milimo_to_parquet, export_mqdd_to_parquet
from app.agents import results_analyzer_agent

autoresearch_router = APIRouter(prefix="/api/autoresearch", tags=["autoresearch"])

@autoresearch_router.get("/status")
def get_status():
    return {"status": "Autoresearch-MLX extension active"}

@autoresearch_router.get("/analyze")
async def analyze_results():
    """Returns a scientific summary of experiment results."""
    return {"summary": results_analyzer_agent.get_performance_summary()}

class RunRequest(BaseModel):
    target: Optional[str] = None
    mode: Optional[str] = "manual" # "manual" or "autonomous"

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

autoresearch_extension = Extension(
    id="autoresearch",
    name="Autoresearch-MLX",
    agent_type="autoresearch",
    slash_commands=["/research", "/pretrain", "/loop"],
    intent_patterns=["autonomous research", "pretraining loop", "karpathy", "val_bpb"],
    system_prompt=(
        "You are the Autoresearch-MLX Agent, a native Apple Silicon port of Karpathy's autoresearch loop.\n"
        "You specialize in hardware-efficient pretraining and architectural optimization.\n"
        "You can trigger 5-minute walls-clock experiments and analyze the resulting val_bpb metrics."
    ),
    router=autoresearch_router
)

def setup_extension():
    registry.register(autoresearch_extension)

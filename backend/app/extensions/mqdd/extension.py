"""Milimo Quantum Drug Discovery (MQDD) Extension."""
from app.extensions.registry import Extension, registry
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.extensions.mqdd import workflow

mqdd_router = APIRouter(prefix="/api/mqdd", tags=["mqdd"])

class WorkflowRequest(BaseModel):
    prompt: str
    conversation_id: str | None = None


@mqdd_router.get("/status")
def get_status():
    return {"status": "MQDD active as Milimo OS Extension", "local_llm": True}

@mqdd_router.post("/workflow")
async def start_workflow(req: WorkflowRequest):
    return StreamingResponse(
        workflow.run_full_workflow(req.prompt, req.conversation_id), 
        media_type="text/event-stream"
    )

@mqdd_router.get("/results/{conversation_id}")
async def get_results(conversation_id: str):
    from app.db import get_session
    from app.db.models import Artifact, Message, Conversation
    
    session = get_session()
    try:
        # Find the latest MQDD result artifact in this conversation
        # Simplified query for broader DB compatibility
        result = session.query(Artifact).join(Message).filter(
            Message.conversation_id == conversation_id,
            Artifact.type == "results"
        ).order_by(Artifact.created_at.desc()).all()
        
        # Filter in Python for reliable metadata matching
        mqdd_result = None
        for r in result:
            meta = r.metadata_ or {}
            if meta.get("agent") == "mqdd":
                mqdd_result = r
                break
        
        if mqdd_result:
            import json
            return json.loads(mqdd_result.content)
        return {"error": "No results found for this conversation"}
    finally:
        session.close()

def mqdd_dispatch_handler(query: str) -> dict:
    """Special quick handler for MQDD queries before hitting the full LLM."""
    if "molecule" in query.lower() and "smiles" in query.lower():
        # Example quick interception
        return {
            "response": "[MQDD] Launching quick molecule preview plugin...",
            "artifacts": [],
            "needs_llm": True, 
            "system_prompt": mqdd_extension.system_prompt
        }
    return {}

mqdd_extension = Extension(
    id="mqdd",
    name="Quantum Drug Discovery",
    agent_type="mqdd",
    slash_commands=["/mqdd", "/drug", "/pharma"],
    intent_patterns=["drug discovery", "protein folding", "binding affinity", "admet", "smiles"],
    system_prompt=(
        "You are the MQDD (Milimo Quantum Drug Discovery) Agent.\n"
        "You specialize in computational chemistry, drug discovery, and generating quantum simulations for molecular targets.\n"
        "Always prioritize running calculations through local MLX/Ollama backends.\n"
        "If a user asks about a molecule, provide its SMILES string and propose a VQE or QAOA circuit to analyze it."
    ),
    router=mqdd_router,
    dispatch_handler=mqdd_dispatch_handler
)

def setup_extension():
    """Register the extension with the global registry."""
    registry.register(mqdd_extension)

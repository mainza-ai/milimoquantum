import asyncio
import json
import logging
import uuid
from typing import AsyncGenerator

from app.extensions.mqdd.schemas import MqddResultData
from app.extensions.mqdd import agents

from app.db import get_session
from app.db.models import Artifact, Message, Conversation

logger = logging.getLogger(__name__)

async def run_full_workflow(prompt: str, conversation_id: str | None = None, basis: str | None = "sto3g", pdb_content: str | None = None) -> AsyncGenerator[str, None]:
    """
    Executes the full MQDD pipeline, yielding SSE status updates, 
    and finally yielding the completed ResultData.
    """
    
    # Ensure we have a conversation ID
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        
    result = MqddResultData()
    
    def format_sse(event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    try:
        # 0. Target ID Agent (Skip if PDB content is provided)
        if pdb_content:
            yield format_sse("status", {"agent": "TARGET_IDENTIFICATION", "status": "DONE", "message": "Using uploaded PDB file content."})
            pdb_id = "uploaded_structure"
            result.pdbId = pdb_id
            pdb_str = "(Uploaded Structure)"
        else:
            yield format_sse("status", {"agent": "TARGET_IDENTIFICATION", "status": "WORKING", "message": "Identifying protein target..."})
            pdb_id = await agents.run_target_identification(prompt)
            result.pdbId = pdb_id
            pdb_str = f"(PDB ID: {pdb_id})" if pdb_id else "(No PDB ID found)"
            yield format_sse("status", {"agent": "TARGET_IDENTIFICATION", "status": "DONE", "message": f"Target identification complete. {pdb_str}"})

        # 1. Literature Agent
        yield format_sse("status", {"agent": "LITERATURE", "status": "WORKING", "message": "Searching live literature databases..."})
        lit_results = await agents.run_literature_review(prompt)
        result.literature = lit_results
        lit_summary = " ".join([r.summary for r in lit_results])
        yield format_sse("status", {"agent": "LITERATURE", "status": "DONE", "message": f"Literature review complete. Found {len(lit_results)} citations."})

        # 2. Molecular Design Agent
        yield format_sse("status", {"agent": "MOLECULAR_DESIGN", "status": "WORKING", "message": "Generating candidates..."})
        design_context = f"{prompt}. Protein Target: {pdb_str}. Literature context: {lit_summary}"
        # Don't pass raw prompt to similarity search - it expects SMILES, not natural language
        # LLM will generate candidates from context
        candidates = await agents.run_molecular_design(design_context, count=3, target_query="")
        result.molecules = candidates
        yield format_sse("status", {"agent": "MOLECULAR_DESIGN", "status": "DONE", "message": f"{len(candidates)} candidates generated (including library hits)."})

        if not result.molecules:
            yield format_sse("error", {"message": "Workflow failed: No candidate molecules were generated."})
            return

        # 3. Parallel Execution: ADMET, Quantum, Synthesizability
        yield format_sse("status", {"agent": "PROPERTY_PREDICTION", "status": "WORKING", "message": "Predicting properties..."})
        yield format_sse("status", {"agent": "QUANTUM_SIMULATION", "status": "WORKING", "message": "Running quantum simulations..."})
        yield format_sse("status", {"agent": "SYNTHESIZABILITY", "status": "WORKING", "message": "Analyzing synthetic accessibility..."})

        async def analyze_molecule(mol, idx, total, basis="sto3g"):
            admet_task = asyncio.create_task(agents.run_property_prediction(mol.smiles))
            quantum_task = asyncio.create_task(agents.run_quantum_simulation(mol.smiles, basis=basis))
            synth_task = asyncio.create_task(agents.run_synthesizability(mol.smiles))
            
            admet, energy, sa = await asyncio.gather(admet_task, quantum_task, synth_task)
            
            if admet:
                mol.admet = admet.admet
                mol.painsAlerts = admet.painsAlerts
            mol.bindingEnergy = energy
            mol.saScore = sa
            return mol

        analysis_tasks = [analyze_molecule(mol, i, len(result.molecules), basis=basis) for i, mol in enumerate(result.molecules)]
        result.molecules = await asyncio.gather(*analysis_tasks)
        
        yield format_sse("status", {"agent": "PROPERTY_PREDICTION", "status": "DONE", "message": "Property prediction complete."})
        yield format_sse("status", {"agent": "QUANTUM_SIMULATION", "status": "DONE", "message": "Quantum simulations complete."})
        yield format_sse("status", {"agent": "SYNTHESIZABILITY", "status": "DONE", "message": "Synthesis analysis complete."})

        # Sort molecules by binding energy (more negative = better)
        # Handle None values by putting them at the end
        result.molecules.sort(key=lambda x: x.bindingEnergy if x.bindingEnergy is not None else float('inf'))
        best_candidate = result.molecules[0]

        # 4. Interaction Analysis
        if best_candidate and result.pdbId:
            yield format_sse("status", {"agent": "INTERACTION_ANALYSIS", "status": "WORKING", "message": "Analyzing binding site interactions..."})
            interactions = await agents.run_interaction_analysis(result.pdbId, best_candidate.smiles, pdb_content=pdb_content)
            best_candidate.interactions = interactions
            yield format_sse("status", {"agent": "INTERACTION_ANALYSIS", "status": "DONE", "message": "Interaction analysis complete."})

        # 5. Failure Analysis
        is_suboptimal = not best_candidate or (best_candidate.bindingEnergy or 0) > -20
        if best_candidate.admet and best_candidate.admet.toxicity.score > 0.7:
             is_suboptimal = True

        if is_suboptimal:
             yield format_sse("status", {"agent": "FAILURE_ANALYSIS", "status": "WORKING", "message": "Analyzing suboptimal results..."})
             failure_prompt = f"Failed to produce strong candidate. Best: {best_candidate.name}, Energy: {best_candidate.bindingEnergy}. Context: {lit_summary}. Hypothesize why."
             failure_report = await agents.run_failure_analysis(failure_prompt)
             result.failureAnalysisReport = failure_report
             yield format_sse("status", {"agent": "FAILURE_ANALYSIS", "status": "DONE", "message": "Failure analysis complete."})

        # 6. Retrosynthesis
        if best_candidate:
             yield format_sse("status", {"agent": "RETROSYNTHESIS", "status": "WORKING", "message": "Predicting synthesis pathway..."})
             retro = await agents.run_retrosynthesis(best_candidate.smiles)
             result.retrosynthesisPlan = retro
             yield format_sse("status", {"agent": "RETROSYNTHESIS", "status": "DONE", "message": "Synthesis plan generated."})

        # 7. Planner & Graph
        yield format_sse("status", {"agent": "EXPERIMENTAL_PLANNER", "status": "WORKING", "message": "Generating experimental plan..."})
        yield format_sse("status", {"agent": "KNOWLEDGE_GRAPH", "status": "WORKING", "message": "Updating knowledge graph..."})
        
        admet_str = best_candidate.admet.model_dump_json() if best_candidate.admet else ""
        final_prompt = f"Query: {prompt}\nLead: {best_candidate.name}\nTarget: {pdb_str}\nADMET: {admet_str}\nEnergy: {best_candidate.bindingEnergy}"
        if result.failureAnalysisReport:
            final_prompt += f"\nFailure Analysis: {result.failureAnalysisReport}"
            
        planner_data = await agents.run_experimental_planner(final_prompt)
        if planner_data:
            result.summary = planner_data.summary
            result.experimentalPlan = planner_data.experimentalPlan
            result.knowledgeGraphUpdate = planner_data.knowledgeGraphUpdate
            
        yield format_sse("status", {"agent": "EXPERIMENTAL_PLANNER", "status": "DONE", "message": "Experimental plan generated."})
        yield format_sse("status", {"agent": "KNOWLEDGE_GRAPH", "status": "DONE", "message": "Knowledge graph updated."})

        # 8. Hypothesis
        yield format_sse("status", {"agent": "HYPOTHESIS", "status": "WORKING", "message": "Generating next steps..."})
        hypo = await agents.run_hypothesis(f"Lead: {best_candidate.name}, Energy: {best_candidate.bindingEnergy}, ADMET: {admet_str}")
        result.proactiveSuggestions = hypo
        yield format_sse("status", {"agent": "HYPOTHESIS", "status": "DONE", "message": "Suggestions generated."})

        # 9. Persistence
        yield format_sse("status", {"agent": "SYSTEM", "status": "WORKING", "message": "Persisting research results..."})
        try:
            session = get_session()
            from app.db.models import Conversation
            
            # 1. Ensure Conversation exists
            conv = session.query(Conversation).filter_by(id=conversation_id).first()
            if not conv:
                conv = Conversation(id=conversation_id, title=f"MQDD: {prompt[:30]}...")
                session.add(conv)
            
            # 2. Find or create a message to attach the artifact
            last_msg = session.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp.desc()).first()
            if not last_msg:
                # Create a system message if the chat is empty
                last_msg = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role="system",
                    content=f"Quantitative Drug Discovery initiated for: {prompt}",
                    agent="mqdd"
                )
                session.add(last_msg)
                session.flush() # Get the ID if needed (though we already set it)
            
            # 3. Save the actual result artifact
            artifact = Artifact(
                message_id=last_msg.id,
                type="results",
                title=f"MQDD Analysis: {pdb_id or prompt[:20]}",
                content=json.dumps(result.model_dump(by_alias=True)),
                metadata_={"agent": "mqdd", "pdbId": pdb_id}
            )
            session.add(artifact)
            session.commit()
            
            # Also tell the frontend about the conversation_id in case it was null
            yield format_sse("status", {"agent": "SYSTEM", "status": "DONE", "message": "Results persisted.", "conversation_id": conversation_id})
            
        except Exception as pe:
            logger.error(f"Failed to persist MQDD results: {pe}")
            session.rollback()
        finally:
            session.close()

        # Finally, yield the complete result object
        yield format_sse("result", result.model_dump(by_alias=True))

    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        yield format_sse("error", {"message": str(e)})

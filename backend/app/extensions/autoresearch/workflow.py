import asyncio
import asyncio.subprocess
import json
import logging
import os
import subprocess
import time
from typing import AsyncGenerator, Optional, List, Dict, Any
from app.llm.mlx_client import mlx_client
from app.data.hub import hub
from app.agents.orchestrator import get_system_prompt
from app.models.schemas import AgentType
from app.graph.neo4j_client import neo4j_client
from app.quantum import vector_store
from app.db import get_session
from app.db.models import Experiment
from app.quantum import executor

logger = logging.getLogger(__name__)

# Absolute paths for the autoresearch integration
AUTORESEARCH_DIR = "/Users/mck/Desktop/milimoquantum/autoresearch-mlx"
MILIMO_PYTHON = "/Users/mck/Desktop/milimoquantum/backend/milimoenv/bin/python"

def get_results():
    path = os.path.join(AUTORESEARCH_DIR, "results.tsv")
    if not os.path.exists(path):
        return {"columns": [], "rows": []}
    
    try:
        with open(path, "r") as f:
            lines = f.readlines()
        if not lines:
            return {"columns": [], "rows": []}
        
        columns = lines[0].strip().split("\t")
        rows = []
        for line in lines[1:]:
            if line.strip():
                rows.append(line.strip().split("\t"))
        return {"columns": columns, "rows": rows}
    except Exception as e:
        logger.error(f"Error reading results.tsv: {e}")
        return {"error": str(e)}

def persist_experiment_result(
    project: str,
    name: str,
    code: str,
    val_bpb: float,
    status: str,
    iteration: int,
    commit_hash: str
):
    """Universal persistence for experiment results to SQL and TSV."""
    # 1. SQL Persistence for Dataset Exporter
    session = get_session()
    try:
        exp = Experiment(
            project=project,
            name=name,
            agent="autoresearch",
            circuit_code=code,
            backend="mlx-training",
            results={"val_bpb": val_bpb, "status": status},
            parameters={"loop_index": iteration, "commit": commit_hash, "improvement": status == "keep"}
        )
        session.add(exp)
        session.commit()
    except Exception as e:
        logger.error(f"Failed to persist experiment to SQL: {e}")
        session.rollback()
    finally:
        session.close()

    # 2. TSV Logging for Frontend Table
    try:
        with open(os.path.join(AUTORESEARCH_DIR, "results.tsv"), "a") as f:
            f.write(f"{commit_hash}\t{val_bpb:.6f}\t0.0\t{status}\t{name}\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        logger.error(f"Failed to write to results.tsv: {e}")

async def run_autonomous_loop(target: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    The 'Karpathy Loop': Autonomous Researcher mode.
    """
    if not os.path.exists(AUTORESEARCH_DIR):
        yield f"event: error\ndata: {json.dumps({'message': 'Autoresearch directory not found'})}\n\n"
        return

    msg = f"Autonomous Research started for: {target or 'General Optimization'}"
    yield f"event: status\ndata: {json.dumps({'status': 'started', 'message': msg})}\n\n"

    # Setup branch if not already on one
    try:
        res = subprocess.run(["git", "branch", "--show-current"], cwd=AUTORESEARCH_DIR, capture_output=True, text=True)
        current_branch = res.stdout.strip()
        if not current_branch.startswith("autoresearch/"):
            tag = time.strftime("%b%d").lower()
            new_branch = f"autoresearch/{tag}"
            yield f"event: log\ndata: {json.dumps({'text': f'Creating new research branch: {new_branch}'})}\n\n"
            subprocess.run(["git", "checkout", "-b", new_branch], cwd=AUTORESEARCH_DIR)
    except Exception as e:
        yield f"event: log\ndata: {json.dumps({'text': f'Git warning: {e}'})}\n\n"

    # Start the experiment loop
    for i in range(1, 11): 
        yield f"event: log\ndata: {json.dumps({'text': f'--- STARTING EXPERIMENT #{i} ---'})}\n\n"

        # 1. READ train.py
        with open(os.path.join(AUTORESEARCH_DIR, "train.py"), "r") as f:
            train_code = f.read()

        # 2. HYPOTHESIZE via Intelligence Hub & Research Agent
        yield f"event: log\ndata: {json.dumps({'text': 'Fetching scientific context from Hub...'})}\n\n"
        hub_context = await hub.get_context(
            query=target or "Optimize machine learning model val_bpb",
            agent_type=AgentType.RESEARCH.value,
            limit=3
        )
        context_segment = hub_context.get("fused_prompt_segment", "")
        
        system_prompt = get_system_prompt(AgentType.RESEARCH)
        full_system_prompt = f"{system_prompt}\n\n{context_segment}\n\n" \
                            f"You are now optimizing 'train.py' in the 'autoresearch-mlx' directory. " \
                            f"Goal: Minimize val_bpb. Respond ONLY with the FULL code for train.py inside a backtick block."

        prompt = f"Optimize this code for {target or 'General MLX Performance'}:\n\n{train_code}"

        yield f"event: log\ndata: {json.dumps({'text': 'Generating hypothesis using Research Agent logic...'})}\n\n"
        new_code = await mlx_client.generate(prompt, system_prompt=full_system_prompt)
        
        if "```python" in new_code:
            new_code = new_code.split("```python")[1].split("```")[0].strip()
        elif "```" in new_code:
            new_code = new_code.split("```")[1].split("```")[0].strip()

        # 3. APPLY HACK
        with open(os.path.join(AUTORESEARCH_DIR, "train.py"), "w") as f:
            f.write(new_code)
        
        # --- HARDWARE-IN-THE-LOOP (Quantum Optimization) ---
        if target and "quantum" in target.lower() and "QuantumCircuit" in new_code:
            yield f"event: log\ndata: {json.dumps({'text': 'Quantum target detected. Executing Hardware-in-the-Loop circuit optimization...'})}\n\n"
            try:
                # Execute the generated circuit code to get real metrics
                q_metrics = await executor.execute_circuit_code(new_code)
                depth = q_metrics.get("depth", 0)
                gates = q_metrics.get("num_qubits", 0) # Simplified proxy for complexity
                
                yield f"event: metric\ndata: {json.dumps({'name': 'circuit_depth', 'value': depth})}\n\n"
                yield f"event: metric\ndata: {json.dumps({'name': 'gate_count', 'value': gates})}\n\n"
                
                # We can even adjust the 'val_bpb' based on these metrics to drive optimization
                # (e.g. lower depth is better for the loss function)
                yield f"event: log\ndata: {json.dumps({'text': f'Quantum metrics: Depth={depth}, Gates={gates}'})}\n\n"
            except Exception as qe:
                yield f"event: log\ndata: {json.dumps({'text': f'Hardware-in-the-Loop warning: {qe}'})}\n\n"
        
        # 4. RUN EXPERIMENT
        yield f"event: log\ndata: {json.dumps({'text': 'Running 5-minute pretraining loop...'})}\n\n"
        last_val_bpb = 0.0
        async for msg in run_research_loop(target=f"Exp {i}", persist=False): # Don't persist inside autonomous loop yet
            if "metric" in msg:
                 data = json.loads(msg.split("data: ")[1])
                 if data['name'] == 'val_bpb': 
                     try: last_val_bpb = float(data['value'])
                     except: pass
            yield msg
        
        yield f"event: log\ndata: {json.dumps({'text': f'Experiment {i} finished with val_bpb: {last_val_bpb:.6f}'})}\n\n"

        # 5. EVALUATE & LOG
        current_results = get_results()
        baseline_bpb = 9.9
        if current_results.get("rows"):
            try: baseline_bpb = float(current_results["rows"][-1][1])
            except: pass
        
        status = "discard"
        if last_val_bpb > 0 and last_val_bpb < baseline_bpb:
            status = "keep"
            yield f"event: log\ndata: {json.dumps({'text': f'WIN! {last_val_bpb:.6f} < {baseline_bpb:.6f}. Keeping change.'})}\n\n"
            subprocess.run(["git", "add", "train.py"], cwd=AUTORESEARCH_DIR)
            subprocess.run(["git", "commit", "-m", f"experiment {i}: improvement {last_val_bpb}"], cwd=AUTORESEARCH_DIR)
        else:
            yield f"event: log\ndata: {json.dumps({'text': f'LOSS or NO CHANGE. {last_val_bpb:.6f} >= {baseline_bpb:.6f}. Discarding.'})}\n\n"
            subprocess.run(["git", "checkout", "train.py"], cwd=AUTORESEARCH_DIR)

        # Get the commit hash for logging
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=AUTORESEARCH_DIR, capture_output=True, text=True)
        current_commit = res.stdout.strip()

        # --- UNIFIED PERSISTENCE ---
        persist_experiment_result(
            project=target or "General Optimization",
            name=f"Autoresearch Exp {i} ({status})",
            code=new_code,
            val_bpb=last_val_bpb,
            status=status,
            iteration=i,
            commit_hash=current_commit
        )
        yield f"event: log\ndata: {json.dumps({'text': f'Persistence complete for Experiment {i}.'})}\n\n"

        # --- NEO4J (Only Wins) ---
        if status == "keep" and neo4j_client.connected:
            try:
                await neo4j_client.execute_query(
                    """
                    MERGE (e:Experiment {id: $id})
                    SET e.type = 'autoresearch', e.val_bpb = $bpb, e.timestamp = datetime(), e.target = $target
                    WITH e
                    MERGE (c:Concept {name: 'MLX Optimization'})
                    MERGE (e)-[:ADVANCES]->(c)
                    """,
                    {"id": f"MLX-{current_commit}", "bpb": last_val_bpb, "target": target or "General"}
                )
            except Exception as ne:
                logger.error(f"Neo4j indexing failed: {ne}")

        yield f"event: log\ndata: {json.dumps({'text': f'Experiment {i} finalized.'})}\n\n"

    yield f"event: status\ndata: {json.dumps({'status': 'completed', 'message': 'Autonomous Research session finished'})}\n\n"

async def run_data_prep() -> AsyncGenerator[str, None]:
    """Runs 'uv run prepare.py' and streams logs."""
    if not os.path.exists(AUTORESEARCH_DIR):
        yield f"event: error\ndata: {json.dumps({'message': 'Autoresearch directory not found'})}\n\n"
        return

    try:
        process = await asyncio.create_subprocess_exec(
            MILIMO_PYTHON, "prepare.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=AUTORESEARCH_DIR,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        yield f"event: status\ndata: {json.dumps({'status': 'started', 'message': 'Data preparation initiated...'})}\n\n"
        
        while True:
            line = await process.stdout.readline()
            if not line: break
            text = line.decode('utf-8').strip()
            if text:
                yield f"event: log\ndata: {json.dumps({'text': text})}\n\n"
        
        await process.wait()
        yield f"event: status\ndata: {json.dumps({'status': 'completed', 'message': 'Data preparation finished'})}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

async def run_research_loop(target: Optional[str] = None, persist: bool = True) -> AsyncGenerator[str, None]:
    """Executes the autoresearch pretraining script and streams logs."""
    if not os.path.exists(AUTORESEARCH_DIR):
        yield f"event: error\ndata: {json.dumps({'message': 'Autoresearch directory not found'})}\n\n"
        return

    # Capture current state for persistence
    with open(os.path.join(AUTORESEARCH_DIR, "train.py"), "r") as f:
        current_code = f.read()

    try:
        process = await asyncio.create_subprocess_exec(
            MILIMO_PYTHON, "train.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=AUTORESEARCH_DIR,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        
        target_msg = f" for '{target}'" if target else ""
        yield f"event: status\ndata: {json.dumps({'status': 'started', 'message': f'Research loop initiated{target_msg}'})}\n\n"

        last_val_bpb = 0.0
        while True:
            line = await process.stdout.readline()
            if not line: break
            
            text = line.decode('utf-8').strip()
            if text:
                yield f"event: log\ndata: {json.dumps({'text': text})}\n\n"
                if "val_bpb" in text:
                    try:
                        # Robust extraction for "val_bpb: 0.123" or "val_bpb  0.123"
                        clean_text = text.replace(":", " ").replace("\t", " ")
                        parts = clean_text.split("val_bpb")
                        if len(parts) > 1:
                            val_str = parts[1].strip().split()[0]
                            last_val_bpb = float(val_str)
                            yield f"event: metric\ndata: {json.dumps({'name': 'val_bpb', 'value': last_val_bpb})}\n\n"
                    except: pass

        await process.wait()
        
        if persist:
            res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=AUTORESEARCH_DIR, capture_output=True, text=True)
            commit_hash = res.stdout.strip()
            persist_experiment_result(
                project=target or "Manual Optimization",
                name=f"Manual Run ({target or 'default'})",
                code=current_code,
                val_bpb=last_val_bpb,
                status="manual",
                iteration=0,
                commit_hash=commit_hash
            )
            yield f"event: log\ndata: {json.dumps({'text': f'Manual experiment results persisted.'})}\n\n"

        yield f"event: status\ndata: {json.dumps({'status': 'completed', 'message': 'Research loop finished'})}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

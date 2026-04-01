# Implementation Plan: NemoClaw & AutoResearch-MLX Integration

## Document Information

| Field | Value |
|-------|-------|
| **Project** | Milimo Quantum |
| **Document Type** | Implementation Plan |
| **Version** | 1.0 |
| **Status** | Draft for Review |
| **Created** | 2026-03-30 |
| **Target Completion** | Q3 2026 |

---

## Overview

This implementation plan details the technical steps required to integrate NemoClaw sandboxing and enhance AutoResearch-MLX capabilities across four phases:

1. **Phase 1**: NemoClaw Sandbox Hardening (Critical)
2. **Phase 2**: Agentic VQE Loop (High)
3. **Phase 3**: Fixed Entity Architecture (High)
4. **Phase 4**: Self-Improving Dataloader (Optimization)

---

## Phase 1: NemoClaw Sandbox Hardening

### 1.1 Objective

Replace the current AST-based software isolation in `sandbox.py` with OS-level sandboxing using NemoClaw's blueprint architecture.

### 1.2 Prerequisites

| Requirement | Verification Command | Notes |
|-------------|---------------------|-------|
| OpenClaw CLI installed | `openclaw --version` | Install from NVIDIA Developer portal |
| NemoClaw plugin installed | `openclaw nemoclaw --version` | Plugin comes with NemoClaw package |
| Docker available | `docker --version` | Required for blueprint execution |
| Python 3.10+ | `python --version` | Already available in milimoenv |

### 1.3 Implementation Steps

#### Step 1.3.1: Install NemoClaw Dependencies

```bash
# Navigate to project root
cd /Users/mck/Desktop/milimoquantum

# Download and install NemoClaw (macOS)
curl -LsSf https://developer.nvidia.com/nemoclaw/install.sh | sh

# Verify installation
openclaw nemoclaw status

# Expected output:
# NemoClaw plugin: installed
# Blueprint runner: ready
# Sandbox runtime: available
```

#### Step 1.3.2: Create Blueprint Directory Structure

```bash
# Create NemoClaw configuration directory
mkdir -p autoresearch-mlx/nemoclaw/orchestrator
mkdir -p autoresearch-mlx/nemoclaw/policies
```

#### Step 1.3.3: Create Blueprint Manifest

**File**: `autoresearch-mlx/nemoclaw/blueprint.yaml`

```yaml
# Milimo Quantum - Autoresearch Blueprint
# NemoClaw sandbox configuration for autonomous ML/quantum research

apiVersion: openclaw.nvidia.com/v1
kind: Blueprint
metadata:
  name: milimo-autoresearch
  version: "1.0.0"
  description: "Sandboxed execution environment for Autoresearch-MLX experiments"
  compatibility:
    - "mlx-autoresearch"
    - "qiskit-aer"
    - "cuda-q"

spec:
  # Execution configuration
  execution:
    timeout: 600s  # 10-minute hard timeout for safety
    memory_limit: 32GB
    gpu_passthrough: true  # Enable MLX GPU access
    
  # Network policies
  network:
    mode: whitelist
    egress:
      allowed_hosts:
        - "huggingface.co"
        - "huggingface.co:443"
        - "arxiv.org"
        - "arxiv.org:443"
        - "pubmed.ncbi.nlm.nih.gov"
        - "pubmed.ncbi.nlm.nih.gov:443"
        - "api.openai.com"  # Optional: for cloud fallback
      blocked_action: notify  # Notify operator instead of silent drop
      
  # Filesystem policies  
  filesystem:
    read_only:
      - "/System"
      - "/Library"
      - "/usr"
      - "/etc"
      - "/var"
    read_write:
      - "/sandbox"
      - "/tmp"
      - "/Users/mck/Desktop/milimoquantum/autoresearch-mlx"
    blocked_paths:
      - "/Users/mck/Desktop/milimoquantum/backend/.env"
      - "/Users/mck/Desktop/milimoquantum/backend/milimoenv"
      
  # Environment variables
  environment:
    inherit:
      - "PATH"
      - "HOME"
      - "USER"
    inject:
      PYTHONUNBUFFERED: "1"
      MLX_CACHE_DIR: "/tmp/mlx-cache"
      HF_HOME: "/tmp/huggingface"
      
  # Resource limits
  resources:
    cpu_limit: "800%"  # 8 cores max
    memory_limit: "32Gi"
    process_limit: 256
    
  # Security
  security:
    seccomp_profile: "runtime/default"
    no_new_privileges: true
    drop_capabilities:
      - "SYS_ADMIN"
      - "NET_ADMIN"
      - "SYS_PTRACE"
```

#### Step 1.3.4: Create Orchestrator Runner

**File**: `autoresearch-mlx/nemoclaw/orchestrator/runner.py`

```python
#!/usr/bin/env python3
"""
NemoClaw Blueprint Runner for Milimo Autoresearch.

Orchestrates sandboxed execution of train.py experiments.
Implements the plan → apply → status lifecycle.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nemoclaw-runner")

AUTORESEARCH_DIR = Path("/Users/mck/Desktop/milimoquantum/autoresearch-mlx")
SANDBOX_DIR = Path("/sandbox")


class BlueprintRunner:
    """
    Manages the lifecycle of a sandboxed autoresearch experiment.
    
    Lifecycle:
    1. plan() - Validate environment, prepare sandbox
    2. apply() - Execute train.py in sandbox
    3. status() - Monitor execution, capture results
    """
    
    def __init__(self, blueprint_path: Path = None):
        self.blueprint_path = blueprint_path or AUTORESEARCH_DIR / "nemoclaw" / "blueprint.yaml"
        self.sandbox_id: Optional[str] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.start_time: Optional[float] = None
        
    async def plan(self) -> Dict[str, Any]:
        """
        Validate the blueprint and prepare the sandbox environment.
        
        Returns:
            Dict with 'ready' (bool), 'errors' (list), 'warnings' (list)
        """
        result = {"ready": True, "errors": [], "warnings": [], "sandbox_id": None}
        
        # 1. Validate blueprint exists
        if not self.blueprint_path.exists():
            result["errors"].append(f"Blueprint not found: {self.blueprint_path}")
            result["ready"] = False
            return result
            
        # 2. Validate train.py exists
        train_py = AUTORESEARCH_DIR / "train.py"
        if not train_py.exists():
            result["errors"].append(f"train.py not found: {train_py}")
            result["ready"] = False
            return result
            
        # 3. Validate prepare.py (data) exists
        prepare_py = AUTORESEARCH_DIR / "prepare.py"
        if not prepare_py.exists():
            result["warnings"].append("prepare.py not found - data may not be ready")
            
        # 4. Check data directory
        data_cache = Path.home() / ".cache" / "autoresearch"
        if not data_cache.exists():
            result["warnings"].append(f"Data cache not found: {data_cache}")
        
        # 5. Request sandbox creation from NemoClaw
        try:
            create_result = await self._create_sandbox()
            if create_result.get("success"):
                self.sandbox_id = create_result["sandbox_id"]
                result["sandbox_id"] = self.sandbox_id
            else:
                result["errors"].append(f"Sandbox creation failed: {create_result.get('error')}")
                result["ready"] = False
        except Exception as e:
            result["errors"].append(f"Sandbox creation error: {e}")
            result["ready"] = False
            
        logger.info(f"Plan result: ready={result['ready']}, sandbox_id={self.sandbox_id}")
        return result
    
    async def apply(self, experiment_name: str = "unnamed") -> Dict[str, Any]:
        """
        Execute train.py in the sandboxed environment.
        
        Args:
            experiment_name: Identifier for this experiment run
            
        Returns:
            Dict with 'started' (bool), 'pid' (int), 'error' (str if failed)
        """
        result = {"started": False, "pid": None, "error": None}
        
        if not self.sandbox_id:
            result["error"] = "No sandbox ID - call plan() first"
            return result
            
        # Copy current train.py to sandbox
        try:
            train_src = AUTORESEARCH_DIR / "train.py"
            train_dst = SANDBOX_DIR / "train.py"
            
            # Use sandbox's filesystem isolation
            # The file will be mounted read-write in the sandbox
            subprocess.run(
                ["cp", str(train_src), str(train_dst)],
                check=True
            )
        except Exception as e:
            result["error"] = f"Failed to prepare sandbox files: {e}"
            return result
        
        # Execute train.py in sandbox
        self.start_time = time.time()
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                "openclaw", "nemoclaw", "run",
                "--sandbox", self.sandbox_id,
                "--command", "uv run train.py",
                "--cwd", str(AUTORESEARCH_DIR),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )
            result["started"] = True
            result["pid"] = self.process.pid
            logger.info(f"Started experiment '{experiment_name}' with PID {self.process.pid}")
            
        except Exception as e:
            result["error"] = f"Failed to start sandboxed process: {e}"
            
        return result
    
    async def status(self) -> Dict[str, Any]:
        """
        Check the status of the running experiment.
        
        Returns:
            Dict with 'running' (bool), 'exit_code' (int if done), 
            'elapsed_seconds' (float), 'output' (str if available)
        """
        result = {
            "running": False,
            "exit_code": None,
            "elapsed_seconds": 0,
            "output": None,
            "metrics": {}
        }
        
        if not self.process:
            return result
            
        result["elapsed_seconds"] = time.time() - (self.start_time or time.time())
        
        # Check if process is still running
        try:
            exit_code = self.process.returncode
            if exit_code is None:
                result["running"] = True
                
                # Try to read partial output
                try:
                    line = await asyncio.wait_for(
                        self.process.stdout.readline(),
                        timeout=0.1
                    )
                    if line:
                        result["output"] = line.decode('utf-8', errors='replace').strip()
                        
                        # Parse metrics from output
                        if "val_bpb:" in result["output"]:
                            parts = result["output"].split("val_bpb:")
                            if len(parts) > 1:
                                val = parts[1].strip().split()[0]
                                result["metrics"]["val_bpb"] = float(val)
                except asyncio.TimeoutError:
                    pass
            else:
                result["exit_code"] = exit_code
                result["running"] = False
                
                # Read all remaining output
                remaining, _ = await self.process.communicate()
                result["output"] = remaining.decode('utf-8', errors='replace')
                
                # Parse final metrics
                for line in result["output"].split('\n'):
                    if "val_bpb:" in line:
                        parts = line.split("val_bpb:")
                        if len(parts) > 1:
                            val = parts[1].strip().split()[0]
                            result["metrics"]["val_bpb"] = float(val)
                            
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    async def cleanup(self):
        """Clean up sandbox resources."""
        if self.sandbox_id:
            try:
                await asyncio.create_subprocess_exec(
                    "openclaw", "nemoclaw", "destroy",
                    "--sandbox", self.sandbox_id
                )
                logger.info(f"Destroyed sandbox: {self.sandbox_id}")
            except Exception as e:
                logger.warning(f"Failed to destroy sandbox: {e}")
                
        self.sandbox_id = None
        self.process = None
        
    async def _create_sandbox(self) -> Dict[str, Any]:
        """Request sandbox creation from NemoClaw."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "openclaw", "nemoclaw", "create",
                "--blueprint", str(self.blueprint_path),
                "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                data = json.loads(stdout.decode('utf-8'))
                return {"success": True, "sandbox_id": data.get("sandbox_id")}
            else:
                return {"success": False, "error": stderr.decode('utf-8')}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


async def main():
    """CLI entry point for blueprint runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NemoClaw Blueprint Runner")
    parser.add_argument("action", choices=["plan", "apply", "status", "cleanup"])
    parser.add_argument("--blueprint", type=Path, help="Path to blueprint.yaml")
    parser.add_argument("--experiment", default="test", help="Experiment name")
    
    args = parser.parse_args()
    
    runner = BlueprintRunner(blueprint_path=args.blueprint)
    
    if args.action == "plan":
        result = await runner.plan()
        print(json.dumps(result, indent=2))
        
    elif args.action == "apply":
        plan_result = await runner.plan()
        if plan_result["ready"]:
            result = await runner.apply(experiment_name=args.experiment)
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({"error": "Plan failed", "details": plan_result}))
            sys.exit(1)
            
    elif args.action == "status":
        result = await runner.status()
        print(json.dumps(result, indent=2))
        
    elif args.action == "cleanup":
        await runner.cleanup()
        print(json.dumps({"cleaned": True}))


if __name__ == "__main__":
    asyncio.run(main())
```

#### Step 1.3.5: Create Sandbox Policy

**File**: `autoresearch-mlx/nemoclaw/policies/openclaw-sandbox.yaml`

```yaml
# Security Policy for Autoresearch Sandbox
# Applied by NemoClaw blueprint runner

apiVersion: openclaw.nvidia.com/v1
kind: SandboxPolicy
metadata:
  name: autoresearch-default
  labels:
    environment: development
    risk-level: medium

spec:
  # Network Security
  network:
    # Default deny all egress
    default_egress: deny
    
    # Allowed egress endpoints
    egress_rules:
      - name: huggingface-models
        hosts:
          - "huggingface.co"
          - "*.huggingface.co"
        ports: [443]
        purpose: "Model and tokenizer downloads"
        
      - name: scientific-literature
        hosts:
          - "arxiv.org"
          - "*.arxiv.org"
          - "pubmed.ncbi.nlm.nih.gov"
        ports: [443]
        purpose: "Literature retrieval for Research Agent"
        
      - name: local-services
        hosts:
          - "localhost"
          - "host.docker.internal"
        ports: [5432, 6379, 7687, 8080, 8000]
        purpose: "Local PostgreSQL, Redis, Neo4j, Keycloak, FastAPI"
    
    # DNS resolution
    dns_policy: ClusterFirst
    
  # Filesystem Security  
  filesystem:
    # Default: deny all writes
    default_write: deny
    
    # Explicit read-write paths
    write_rules:
      - path: /sandbox
        recursive: true
        purpose: "Sandbox working directory"
        
      - path: /tmp
        recursive: true
        purpose: "Temporary files and cache"
        
      - path: /Users/mck/Desktop/milimoquantum/autoresearch-mlx
        recursive: true
        purpose: "Autoresearch project files"
        conditions:
          max_size: "10GB"
          
    # Read-only system paths
    read_rules:
      - path: /System
        recursive: true
      - path: /Library
        recursive: true
      - path: /usr
        recursive: true
        
    # Blocked sensitive paths
    blocked_paths:
      - path: /Users/mck/Desktop/milimoquantum/backend/.env
        reason: "Contains secrets"
      - path: /Users/mck/Desktop/milimoquantum/backend/milimoenv
        reason: "Virtual environment isolation"
      - path: /Users/*/.ssh
        reason: "SSH keys"
      - path: /Users/*/.aws
        reason: "AWS credentials"
        
  # Process Security
  process:
    # Maximum processes
    process_limit: 256
    
    # Maximum open files
    file_limit: 4096
    
    # Forbidden syscalls
    forbidden_syscalls:
      - fork
      - vfork
      - clone
      - execve  # Except through allowed interpreters
      
    # Allowed interpreters
    allowed_interpreters:
      - /usr/bin/python3
      - /Users/mck/Desktop/milimoquantum/backend/milimoenv/bin/python
      - /usr/local/bin/uv
      
  # Resource Limits
  resources:
    cpu:
      limit: "800%"
      request: "400%"
      
    memory:
      limit: "32Gi"
      request: "16Gi"
      
    gpu:
      # Apple Silicon GPU via MLX
      type: "metal"
      memory_limit: "24Gi"
      
  # Monitoring
  monitoring:
    # Log all security events
    log_level: info
    
    # Audit logging
    audit:
      enabled: true
      events:
        - network_egress
        - filesystem_write
        - process_create
        - syscall_blocked
        
    # Metrics export
    metrics:
      enabled: true
      port: 9090
      path: /metrics
```

#### Step 1.3.6: Update Workflow Integration

**File**: `backend/app/extensions/autoresearch/workflow.py` (modifications)

```python
# === ADD AT TOP OF FILE (after imports) ===

# NemoClaw sandbox integration
try:
    import sys
    sys.path.insert(0, "/Users/mck/Desktop/milimoquantum/autoresearch-mlx/nemoclaw")
    from orchestrator.runner import BlueprintRunner
    NEMOCLAW_AVAILABLE = True
except ImportError:
    NEMOCLAW_AVAILABLE = False
    logger.warning("NemoClaw not available - using legacy subprocess execution")

# === MODIFY run_research_loop FUNCTION ===

async def run_research_loop_nemoclaw(
    target: Optional[str] = None, 
    persist: bool = True
) -> AsyncGenerator[str, None]:
    """
    Executes autoresearch using NemoClaw sandboxed execution.
    This is the hardened version that replaces direct subprocess.
    """
    if not NEMOCLAW_AVAILABLE:
        # Fallback to legacy execution
        async for msg in run_research_loop_legacy(target, persist):
            yield msg
        return
        
    # 1. PLAN - Create sandbox
    runner = BlueprintRunner()
    plan_result = await runner.plan()
    
    if not plan_result["ready"]:
        yield f"event: error\ndata: {json.dumps({'message': f'Sandbox plan failed: {plan_result[\"errors\"]}'})}\n\n"
        return
        
    yield f"event: log\ndata: {json.dumps({'text': f'Sandbox created: {plan_result[\"sandbox_id\"]}'})}\n\n"
    
    # 2. APPLY - Execute experiment
    experiment_name = target or "default"
    apply_result = await runner.apply(experiment_name=experiment_name)
    
    if not apply_result["started"]:
        yield f"event: error\ndata: {json.dumps({'message': f'Failed to start: {apply_result[\"error\"]}'})}\n\n"
        await runner.cleanup()
        return
        
    yield f"event: status\ndata: {json.dumps({'status': 'started', 'message': f'Experiment started in sandbox'})}\n\n"
    
    # 3. STATUS - Monitor execution
    last_val_bpb = 0.0
    while True:
        status = await runner.status()
        
        if status.get("output"):
            yield f"event: log\ndata: {json.dumps({'text': status['output']})}\n\n"
            
        if "val_bpb" in status.get("metrics", {}):
            last_val_bpb = status["metrics"]["val_bpb"]
            yield f"event: metric\ndata: {json.dumps({'name': 'val_bpb', 'value': last_val_bpb})}\n\n"
            
        if not status["running"]:
            break
            
        await asyncio.sleep(1)  # Poll every second
    
    # 4. CLEANUP
    yield f"event: log\ndata: {json.dumps({'text': f'Experiment finished with val_bpb: {last_val_bpb:.6f}'})}\n\n"
    
    if persist:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=AUTORESEARCH_DIR,
            capture_output=True,
            text=True
        )
        commit_hash = res.stdout.strip()
        
        with open(os.path.join(AUTORESEARCH_DIR, "train.py"), "r") as f:
            current_code = f.read()
            
        persist_experiment_result(
            project=target or "Sandboxed Optimization",
            name=f"Sandboxed Run ({target or 'default'})",
            code=current_code,
            val_bpb=last_val_bpb,
            status="sandboxed",
            iteration=0,
            commit_hash=commit_hash
        )
        
    await runner.cleanup()
    yield f"event: status\ndata: {json.dumps({'status': 'completed', 'message': 'Sandboxed research loop finished'})}\n\n"


# === ADD LEGACY WRAPPER ===

async def run_research_loop_legacy(
    target: Optional[str] = None, 
    persist: bool = True
) -> AsyncGenerator[str, None]:
    """Legacy direct subprocess execution (original implementation)."""
    # ... existing implementation moved here ...
    pass


# === UPDATE MAIN FUNCTION ===

async def run_research_loop(
    target: Optional[str] = None, 
    persist: bool = True,
    use_sandbox: bool = True
) -> AsyncGenerator[str, None]:
    """
    Execute the autoresearch pretraining script.
    
    Args:
        target: Optimization target description
        persist: Whether to persist results
        use_sandbox: If True, use NemoClaw sandbox (default: True)
        
    Yields:
        SSE events for frontend streaming
    """
    if use_sandbox and NEMOCLAW_AVAILABLE:
        async for msg in run_research_loop_nemoclaw(target, persist):
            yield msg
    else:
        async for msg in run_research_loop_legacy(target, persist):
            yield msg
```

### 1.4 Testing Plan

#### Test 1.4.1: Blueprint Validation

```bash
# Validate blueprint syntax
openclaw nemoclaw validate --blueprint autoresearch-mlx/nemoclaw/blueprint.yaml

# Expected: No validation errors
```

#### Test 1.4.2: Sandbox Creation

```bash
# Create sandbox manually
openclaw nemoclaw create --blueprint autoresearch-mlx/nemoclaw/blueprint.yaml

# Check status
openclaw nemoclaw status

# Expected: Sandbox created with valid ID
```

#### Test 1.4.3: Policy Enforcement

```bash
# Test network policy (should be blocked)
openclaw nemoclaw run --sandbox <id> --command "curl https://google.com"

# Expected: Network request blocked, notification shown

# Test allowed network
openclaw nemoclaw run --sandbox <id> --command "curl https://huggingface.co"

# Expected: Request succeeds
```

#### Test 1.4.4: Full Experiment Execution

```bash
# Run Python runner
cd autoresearch-mlx/nemoclaw/orchestrator
python runner.py apply --experiment test-phase1

# Expected: Experiment runs in sandbox, val_bpb reported
```

### 1.5 Rollback Plan

If NemoClaw integration fails:

1. Set `use_sandbox=False` in workflow calls
2. System reverts to legacy subprocess execution
3. NemoClaw can be uninstalled: `openclaw nemoclaw uninstall`

---

## Phase 2: Agentic VQE Loop

### 2.1 Objective

Connect Autoresearch-MLX to the MQDD extension for autonomous ansatz discovery using Meyer-Wallach regularization to avoid barren plateaus.

### 2.2 Prerequisites

| Requirement | Verification | Notes |
|-------------|--------------|-------|
| Phase 1 complete | `openclaw nemoclaw status` | Sandbox must be working |
| MQDD extension | Check `extensions/mqdd/` | Chemistry agent available |
| Qiskit Nature | `python -c "import qiskit_nature"` | For molecular Hamiltonians |
| NVIDIA backend (optional) | WSL2 + CUDA-Q | For GPU-accelerated VQE |

### 2.3 Implementation Steps

#### Step 2.3.1: Create VQE Training Module

**File**: `autoresearch-mlx/vqe_train.py`

```python
#!/usr/bin/env python3
"""
VQE Ansatz Discovery Module for Autoresearch-MLX.

Implements agentic reinforcement learning for quantum circuit architecture search.
Uses Meyer-Wallach metric for regularization to avoid barren plateaus.

Usage:
    uv run vqe_train.py --molecule BeH2 --basis sto-3g --time-budget 300
"""

import argparse
import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
import numpy as np

# MLX imports
import mlx.core as mx
import mlx.nn as nn

# Qiskit imports (for evaluation)
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import RealAmplitudes, TwoLocal, EfficientSU2
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_aer import AerSimulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vqe-train")

# === Constants ===
TIME_BUDGET = 300  # 5 minutes default
MAX_CIRCUIT_DEPTH = 50
MIN_CIRCUIT_DEPTH = 2
MEYER_WALLACH_LAMBDA = 0.1  # Regularization strength


@dataclass
class VQEConfig:
    """Configuration for VQE ansatz search."""
    molecule: str = "H2"
    basis: str = "sto-3g"
    num_qubits: int = 4
    time_budget: int = TIME_BUDGET
    meyer_wallach_lambda: float = MEYER_WALLACH_LAMBDA
    min_depth: int = MIN_CIRCUIT_DEPTH
    max_depth: int = MAX_CIRCUIT_DEPTH
    target_energy: Optional[float] = None  # Known ground state for comparison


@dataclass
class AnsatzCandidate:
    """A candidate ansatz architecture."""
    token_sequence: List[str]  # Gate tokens: ["H", "CNOT", "RZ", "RY", ...]
    depth: int
    parameter_count: int
    circuit: Optional[QuantumCircuit] = None
    energy: Optional[float] = None
    gradient_variance: Optional[float] = None
    meyer_wallach_score: Optional[float] = None
    convergence_iterations: Optional[int] = None


class AnsatzTokenizer:
    """
    Tokenizer for quantum circuits.
    Converts between gate sequences and token representations.
    """
    
    # Gate vocabulary
    GATE_VOCAB = {
        # Single-qubit gates
        "H": "h",
        "X": "x",
        "Y": "y", 
        "Z": "z",
        "S": "s",
        "T": "t",
        "RX": "rx",
        "RY": "ry",
        "RZ": "rz",
        "U": "u",
        
        # Two-qubit gates
        "CNOT": "cx",
        "CZ": "cz",
        "CY": "cy",
        "SWAP": "swap",
        "CRX": "crx",
        "CRY": "cry",
        "CRZ": "crz",
        
        # Special tokens
        "<PAD>": "<pad>",
        "<BOS>": "<bos>",  # Beginning of sequence
        "<EOS>": "<eos>",  # End of sequence
        "<UNK>": "<unk>",  # Unknown gate
    }
    
    REVERSE_VOCAB = {v: k for k, v in GATE_VOCAB.items()}
    
    def encode(self, gates: List[str]) -> List[int]:
        """Convert gate names to token IDs."""
        tokens = [self.GATE_VOCAB.get(g, "<unk>") for g in gates]
        return [list(self.GATE_VOCAB.keys()).index(t) for t in tokens]
    
    def decode(self, token_ids: List[int]) -> List[str]:
        """Convert token IDs back to gate names."""
        vocab_list = list(self.GATE_VOCAB.keys())
        return [vocab_list[i] if i < len(vocab_list) else "<unk>" for i in token_ids]


class MeyerWallachCalculator:
    """
    Calculates the Meyer-Wallach measure of entanglement.
    Used to regularize circuit depth and encourage expressivity.
    
    MW(|ψ⟩) = 2(1 - 1/n Σ_j Tr(ρ_j²))
    
    Higher MW = more entanglement = better for complex molecules
    """
    
    @staticmethod
    def calculate(statevector: np.ndarray, num_qubits: int) -> float:
        """
        Calculate Meyer-Wallach entanglement measure.
        
        Args:
            statevector: State vector of the quantum state
            num_qubits: Number of qubits
            
        Returns:
            Meyer-Wallach measure (0 to 1)
        """
        if len(statevector) != 2 ** num_qubits:
            raise ValueError(f"Statevector length {len(statevector)} doesn't match {num_qubits} qubits")
            
        # Reshape to separate each qubit
        psi = statevector.reshape([2] * num_qubits)
        
        # Calculate purity of each single-qubit reduced density matrix
        entanglement_sum = 0.0
        for j in range(num_qubits):
            # Trace out all qubits except j
            rho_j = MeyerWallachCalculator._partial_trace(psi, j, num_qubits)
            
            # Calculate purity: Tr(ρ²)
            purity = np.trace(rho_j @ rho_j).real
            
            entanglement_sum += purity
            
        # Meyer-Wallach measure
        mw = 2 * (1 - entanglement_sum / num_qubits)
        
        return float(mw)
    
    @staticmethod
    def _partial_trace(psi: np.ndarray, keep_qubit: int, num_qubits: int) -> np.ndarray:
        """Calculate partial trace keeping only one qubit."""
        # Sum over all qubits except the keep_qubit
        axes_to_sum = list(range(num_qubits))
        axes_to_sum.remove(keep_qubit)
        
        # Calculate reduced density matrix
        rho = np.zeros((2, 2), dtype=complex)
        for i in range(2):
            for j in range(2):
                # |i⟩⟨j| component
                psi_i = psi.copy()
                psi_j = psi.copy()
                
                # Set keep_qubit to state |i⟩ and |j⟩
                idx_i = [slice(None)] * num_qubits
                idx_j = [slice(None)] * num_qubits
                idx_i[keep_qubit] = i
                idx_j[keep_qubit] = j
                
                psi_i = np.zeros_like(psi)
                psi_j = np.zeros_like(psi)
                psi_i[tuple(idx_i)] = psi[tuple(idx_i)]
                psi_j[tuple(idx_j)] = psi[tuple(idx_j)]
                
                # Trace over other qubits
                rho[i, j] = np.sum(psi_i * np.conj(psi_j))
                
        return rho


class HamiltonianBuilder:
    """Build molecular Hamiltonians for VQE."""
    
    # Pre-computed Hamiltonians for small molecules (simplified)
    # In production, would use qiskit_nature for full molecular calculation
    MOLECULAR_HAMILTONIANS = {
        "H2": {
            "sto-3g": {
                "pauli_string": "IIII + IZII + IIZI + IIZZ + ZIII + ZIZI + ZZII + ZZZZ",
                "num_qubits": 4,
                "ground_state_energy": -1.1372855,
            }
        },
        "LiH": {
            "sto-3g": {
                "pauli_string": "IIII + IIII",  # Placeholder - real would have ~100 terms
                "num_qubits": 10,
                "ground_state_energy": -7.8825,
            }
        },
        "BeH2": {
            "sto-3g": {
                "pauli_string": "IIIIIIII + ...",  # 14 qubits
                "num_qubits": 14,
                "ground_state_energy": -15.56,
            }
        }
    }
    
    @classmethod
    def get_hamiltonian(cls, molecule: str, basis: str) -> Tuple[SparsePauliOp, dict]:
        """
        Get Hamiltonian for a molecule.
        
        Returns:
            Tuple of (Hamiltonian operator, metadata dict)
        """
        if molecule not in cls.MOLECULAR_HAMILTONIANS:
            raise ValueError(f"Molecule {molecule} not in database. Available: {list(cls.MOLECULAR_HAMILTONIANS.keys())}")
            
        mol_data = cls.MOLECULAR_HAMILTONIANS[molecule].get(basis)
        if not mol_data:
            raise ValueError(f"Basis {basis} not available for {molecule}")
            
        # Parse Pauli string into operator
        hamiltonian = SparsePauliOp.from_operator(mol_data["pauli_string"])
        
        metadata = {
            "molecule": molecule,
            "basis": basis,
            "num_qubits": mol_data["num_qubits"],
            "target_energy": mol_data["ground_state_energy"],
        }
        
        return hamiltonian, metadata


class AnsatzGenerator(nn.Module):
    """
    MLX neural network that generates ansatz architectures.
    
    Input: Molecular Hamiltonian encoding
    Output: Token sequence for quantum circuit
    """
    
    def __init__(self, config: VQEConfig, vocab_size: int = 20, hidden_dim: int = 256):
        super().__init__()
        self.config = config
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        
        # Hamiltonian encoder (simple MLP for now)
        self.encoder = nn.Sequential(
            nn.Linear(config.num_qubits ** 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        
        # Sequence generator (LSTM-style)
        self.embedding = nn.Embedding(vocab_size, hidden_dim)
        self.rnn_cell = nn.Linear(hidden_dim + hidden_dim, hidden_dim)
        
        # Output projection
        self.output = nn.Linear(hidden_dim, vocab_size)
        
        # Depth predictor
        self.depth_predictor = nn.Linear(hidden_dim, 1)
        
    def __call__(self, hamiltonian_encoding: mx.array, max_length: int = 50) -> mx.array:
        """
        Generate ansatz token sequence.
        
        Args:
            hamiltonian_encoding: Encoded Hamiltonian (batch, qubits^2)
            max_length: Maximum sequence length
            
        Returns:
            Token IDs (batch, max_length)
        """
        batch_size = hamiltonian_encoding.shape[0]
        
        # Encode Hamiltonian
        h = self.encoder(hamiltonian_encoding)
        
        # Start with BOS token
        token = mx.zeros((batch_size, 1), dtype=mx.int32)  # BOS = 0
        hidden = h
        
        outputs = []
        for _ in range(max_length):
            # Embed current token
            token_embed = self.embedding(token[:, -1])
            
            # RNN step
            hidden = mx.tanh(self.rnn_cell(mx.concatenate([hidden, token_embed], axis=-1)))
            
            # Predict next token
            logits = self.output(hidden)
            next_token = mx.argmax(logits, axis=-1, keepdims=True)
            
            outputs.append(next_token)
            token = next_token
            
        return mx.concatenate(outputs, axis=1)


class VQEAnsatzOptimizer:
    """
    Main VQE optimization loop.
    
    Follows the autoresearch pattern:
    1. Generate candidate ansatz
    2. Evaluate energy and metrics
    3. Keep if better, discard if worse
    """
    
    def __init__(self, config: VQEConfig):
        self.config = config
        self.tokenizer = AnsatzTokenizer()
        self.mw_calculator = MeyerWallachCalculator()
        self.best_candidate: Optional[AnsatzCandidate] = None
        self.history: List[AnsatzCandidate] = []
        
    def tokens_to_circuit(self, tokens: List[str], num_qubits: int) -> QuantumCircuit:
        """Convert token sequence to QuantumCircuit."""
        qc = QuantumCircuit(num_qubits)
        
        param_idx = 0
        for i, token in enumerate(tokens):
            if token in ["H", "X", "Y", "Z", "S", "T"]:
                # Single-qubit gates - distribute across qubits
                qubit = i % num_qubits
                getattr(qc, token.lower())(qubit)
                
            elif token in ["RX", "RY", "RZ"]:
                # Parameterized rotation
                qubit = i % num_qubits
                param = Parameter(f"θ_{param_idx}")
                param_idx += 1
                getattr(qc, token.lower())(param, qubit)
                
            elif token in ["CNOT", "CZ", "CY"]:
                # Two-qubit gates
                control = i % num_qubits
                target = (i + 1) % num_qubits
                getattr(qc, token.lower())(control, target)
                
            elif token == "<EOS>" or token == "<PAD>":
                break
                
        return qc
    
    def evaluate_ansatz(
        self, 
        candidate: AnsatzCandidate,
        hamiltonian: SparsePauliOp
    ) -> AnsatzCandidate:
        """
        Evaluate a candidate ansatz.
        
        Returns the candidate with energy, gradient, and MW metrics.
        """
        # Build circuit
        circuit = self.tokens_to_circuit(candidate.token_sequence, self.config.num_qubits)
        candidate.circuit = circuit
        candidate.depth = circuit.depth()
        candidate.parameter_count = circuit.num_parameters
        
        # Classical simulation for energy
        simulator = AerSimulator(method="statevector")
        
        # Bind random parameters for initial evaluation
        param_values = np.random.uniform(0, 2 * np.pi, circuit.num_parameters)
        param_dict = dict(zip(circuit.parameters, param_values))
        bound_circuit = circuit.assign_parameters(param_dict)
        
        # Get statevector
        statevector = Statevector.from_instruction(bound_circuit)
        
        # Calculate energy expectation
        energy = statevector.expectation_value(hamiltonian).real
        candidate.energy = float(energy)
        
        # Calculate Meyer-Wallach entanglement
        candidate.meyer_wallach_score = self.mw_calculator.calculate(
            statevector.data, self.config.num_qubits
        )
        
        # Estimate gradient variance (simplified)
        # In production, would use parameter-shift rule
        gradient_variance = self._estimate_gradient_variance(
            circuit, hamiltonian, param_values
        )
        candidate.gradient_variance = gradient_variance
        
        return candidate
    
    def _estimate_gradient_variance(
        self, 
        circuit: QuantumCircuit, 
        hamiltonian: SparsePauliOp,
        params: np.ndarray,
        num_samples: int = 10
    ) -> float:
        """Estimate gradient variance using parameter-shift rule."""
        gradients = []
        
        for i in range(min(num_samples, circuit.num_parameters)):
            # Parameter-shift: f(θ + π/2) - f(θ - π/2) / 2
            param_shift = np.pi / 2
            
            params_plus = params.copy()
            params_plus[i] += param_shift
            
            params_minus = params.copy()
            params_minus[i] -= param_shift
            
            # Calculate energies
            circuit_plus = circuit.assign_parameters(dict(zip(circuit.parameters, params_plus)))
            circuit_minus = circuit.assign_parameters(dict(zip(circuit.parameters, params_minus)))
            
            sv_plus = Statevector.from_instruction(circuit_plus)
            sv_minus = Statevector.from_instruction(circuit_minus)
            
            energy_plus = sv_plus.expectation_value(hamiltonian).real
            energy_minus = sv_minus.expectation_value(hamiltonian).real
            
            gradient = (energy_plus - energy_minus) / 2
            gradients.append(gradient)
            
        return float(np.var(gradients))
    
    def objective(self, candidate: AnsatzCandidate) -> float:
        """
        Calculate objective function for candidate selection.
        
        Objective = energy + λ * (1 - MW) + penalty(depth > max_depth)
        
        Lower is better.
        """
        if candidate.energy is None:
            return float('inf')
            
        # Base objective: energy
        obj = candidate.energy
        
        # Meyer-Wallach regularization (encourage entanglement)
        if candidate.meyer_wallach_score is not None:
            obj += self.config.meyer_wallach_lambda * (1 - candidate.meyer_wallach_score)
            
        # Depth penalty
        if candidate.depth > self.config.max_depth:
            obj += (candidate.depth - self.config.max_depth) * 0.1
            
        # Gradient variance penalty (avoid barren plateaus)
        if candidate.gradient_variance is not None and candidate.gradient_variance < 1e-6:
            obj += 1.0  # Severe penalty for near-zero gradients
            
        return obj
    
    async def run_loop(self, hamiltonian: SparsePauliOp) -> AsyncGenerator[str, None]:
        """
        Run the VQE ansatz optimization loop.
        
        Yields SSE events for frontend streaming.
        """
        import time
        start_time = time.time()
        
        iteration = 0
        while time.time() - start_time < self.config.time_budget:
            iteration += 1
            
            yield f"event: log\ndata: {json.dumps({'text': f'--- VQE Iteration {iteration} ---'})}\n\n"
            
            # Generate candidate ansatz
            # (In production, would use MLX model for generation)
            candidate = self._generate_random_candidate()
            
            yield f"event: log\ndata: {json.dumps({'text': f'Generated ansatz: depth={candidate.depth}, params={candidate.parameter_count}'})}\n\n"
            
            # Evaluate candidate
            candidate = self.evaluate_ansatz(candidate, hamiltonian)
            
            yield f"event: metric\ndata: {json.dumps({'name': 'energy', 'value': candidate.energy})}\n\n"
            yield f"event: metric\ndata: {json.dumps({'name': 'meyer_wallach', 'value': candidate.meyer_wallach_score})}\n\n"
            yield f"event: metric\ndata: {json.dumps({'name': 'gradient_variance', 'value': candidate.gradient_variance})}\n\n"
            
            # Calculate objective
            obj = self.objective(candidate)
            
            # Keep or discard
            if self.best_candidate is None or obj < self.objective(self.best_candidate):
                self.best_candidate = candidate
                status = "keep"
                yield f"event: log\ndata: {json.dumps({'text': f'WIN! New best: energy={candidate.energy:.6f}, MW={candidate.meyer_wallach_score:.4f}'})}\n\n"
            else:
                status = "discard"
                yield f"event: log\ndata: {json.dumps({'text': f'DISCARD: objective {obj:.6f} >= {self.objective(self.best_candidate):.6f}'})}\n\n"
                
            self.history.append(candidate)
            
            # Log to results
            self._log_result(candidate, status, iteration)
            
        yield f"event: status\ndata: {json.dumps({'status': 'completed', 'message': f'VQE loop finished. Best energy: {self.best_candidate.energy if self.best_candidate else None}'})}\n\n"
        
    def _generate_random_candidate(self) -> AnsatzCandidate:
        """Generate a random ansatz candidate (placeholder for MLX generation)."""
        import random
        
        # Simple random circuit generation
        gates = ["H", "X", "RX", "RY", "RZ", "CNOT", "CZ"]
        depth = random.randint(self.config.min_depth, self.config.max_depth)
        
        tokens = []
        for i in range(depth):
            gate = random.choice(gates)
            tokens.append(gate)
            
        tokens.append("<EOS>")
        
        return AnsatzCandidate(
            token_sequence=tokens,
            depth=depth,
            parameter_count=sum(1 for t in tokens if t in ["RX", "RY", "RZ"])
        )
    
    def _log_result(self, candidate: AnsatzCandidate, status: str, iteration: int):
        """Log result to TSV file."""
        import os
        
        results_path = os.path.join(
            os.path.dirname(__file__), 
            "vqe_results.tsv"
        )
        
        # Header if file doesn't exist
        if not os.path.exists(results_path):
            with open(results_path, "w") as f:
                f.write("iteration\tenergy\tmeyer_wallach\tgradient_var\tdepth\tparams\tstatus\n")
                
        # Append result
        with open(results_path, "a") as f:
            f.write(f"{iteration}\t{candidate.energy or 0:.6f}\t{candidate.meyer_wallach_score or 0:.4f}\t"
                   f"{candidate.gradient_variance or 0:.6e}\t{candidate.depth}\t"
                   f"{candidate.parameter_count}\t{status}\n")


async def main():
    """CLI entry point for VQE training."""
    parser = argparse.ArgumentParser(description="VQE Ansatz Discovery")
    parser.add_argument("--molecule", default="H2", help="Molecule to optimize")
    parser.add_argument("--basis", default="sto-3g", help="Basis set")
    parser.add_argument("--time-budget", type=int, default=300, help="Time budget in seconds")
    parser.add_argument("--meyer-wallach-lambda", type=float, default=0.1, help="MW regularization")
    
    args = parser.parse_args()
    
    # Get Hamiltonian
    try:
        hamiltonian, metadata = HamiltonianBuilder.get_hamiltonian(args.molecule, args.basis)
        logger.info(f"Loaded Hamiltonian for {args.molecule}/{args.basis}")
        logger.info(f"Target energy: {metadata['target_energy']}")
    except Exception as e:
        logger.error(f"Failed to load Hamiltonian: {e}")
        sys.exit(1)
        
    # Create config
    config = VQEConfig(
        molecule=args.molecule,
        basis=args.basis,
        num_qubits=metadata["num_qubits"],
        time_budget=args.time_budget,
        meyer_wallach_lambda=args.meyer_wallach_lambda,
        target_energy=metadata["target_energy"]
    )
    
    # Run optimization
    optimizer = VQEAnsatzOptimizer(config)
    
    async for event in optimizer.run_loop(hamiltonian):
        # Parse and print events
        if event.startswith("event: log"):
            data = event.split("data: ")[1].strip()
            msg = json.loads(data)
            print(msg["text"])
        elif event.startswith("event: metric"):
            data = event.split("data: ")[1].strip()
            msg = json.loads(data)
            print(f"  {msg['name']}: {msg['value']:.6f}")
            

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

#### Step 2.3.2: Integrate with MQDD Extension

**File**: `backend/app/extensions/mqdd/agents.py` (modifications)

```python
# === ADD IMPORTS ===
from app.extensions.autoresearch.vqe_train import VQEAnsatzOptimizer, VQEConfig, HamiltonianBuilder
from app.extensions.autoresearch.workflow import run_vqe_loop

# === MODIFY ChemistryAgent CLASS ===

class ChemistryAgent(BaseAgent):
    """Chemistry agent with VQE ansatz discovery capabilities."""
    
    # ... existing methods ...
    
    async def run_agentic_vqe(
        self, 
        molecule: str, 
        basis: str = "sto-3g",
        time_budget: int = 300
    ) -> AsyncGenerator[str, None]:
        """
        Run agentic VQE for molecular ground state discovery.
        
        This connects the Autoresearch-MLX loop to the MQDD extension,
        enabling autonomous ansatz architecture search.
        """
        # Get Hamiltonian
        try:
            hamiltonian, metadata = HamiltonianBuilder.get_hamiltonian(molecule, basis)
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': f'Hamiltonian error: {e}'})}\n\n"
            return
            
        # Create VQE config
        config = VQEConfig(
            molecule=molecule,
            basis=basis,
            num_qubits=metadata["num_qubits"],
            time_budget=time_budget,
            target_energy=metadata.get("target_energy")
        )
        
        # Run optimization loop
        optimizer = VQEAnsatzOptimizer(config)
        
        async for event in optimizer.run_loop(hamiltonian):
            yield event
            
            # Also yield to Neo4j for "keep" experiments
            if "WIN" in event and neo4j_client.connected:
                # Extract energy from event
                # Index successful ansatz to knowledge graph
                pass
```

#### Step 2.3.3: Add Hardware Abstraction Layer Routing

**File**: `backend/app/quantum/hal.py` (modifications)

```python
# === ADD METHOD TO HardwareAbstractionLayer CLASS ===

async def route_vqe_evaluation(
    self, 
    circuit: QuantumCircuit,
    hamiltonian: SparsePauliOp
) -> Dict[str, Any]:
    """
    Route VQE evaluation to appropriate hardware.
    
    Routing logic:
    - Small circuits (< 10 qubits): Local statevector
    - Medium circuits (10-20 qubits): NVIDIA GPU via WSL2
    - Large circuits (> 20 qubits): CUDA-Q with tensor network
    
    Returns:
        Dict with 'energy', 'meyer_wallach', 'gradient_variance'
    """
    num_qubits = circuit.num_qubits
    
    if num_qubits < 10:
        # Local evaluation
        return await self._evaluate_local(circuit, hamiltonian)
        
    elif num_qubits <= 20:
        # Route to NVIDIA GPU
        return await self._evaluate_nvidia_gpu(circuit, hamiltonian)
        
    else:
        # Use CUDA-Q tensor network
        return await self._evaluate_cudaq(circuit, hamiltonian)
        
async def _evaluate_local(self, circuit, hamiltonian) -> Dict[str, Any]:
    """Local statevector evaluation (Apple Silicon)."""
    from qiskit.quantum_info import Statevector
    import numpy as np
    
    # Bind parameters
    params = np.random.uniform(0, 2*np.pi, circuit.num_parameters)
    bound_circuit = circuit.assign_parameters(dict(zip(circuit.parameters, params)))
    
    # Get statevector
    sv = Statevector.from_instruction(bound_circuit)
    
    # Calculate metrics
    energy = sv.expectation_value(hamiltonian).real
    
    # Meyer-Wallach (simplified)
    mw = self._calculate_meyer_wallach(sv.data, num_qubits)
    
    return {
        "energy": float(energy),
        "meyer_wallach": mw,
        "backend": "local_apple_silicon"
    }
    
async def _evaluate_nvidia_gpu(self, circuit, hamiltonian) -> Dict[str, Any]:
    """Route to NVIDIA GPU via WSL2."""
    # This would connect to the Windows WSL2 node
    # Implementation depends on distributed messaging setup
    pass
    
async def _evaluate_cudaq(self, circuit, hamiltonian) -> Dict[str, Any]:
    """CUDA-Q tensor network evaluation."""
    # For very large circuits
    pass
```

### 2.4 Testing Plan

#### Test 2.4.1: VQE Training Module

```bash
# Run basic VQE optimization
cd autoresearch-mlx
uv run vqe_train.py --molecule H2 --time-budget 60

# Expected: Energy decreases over iterations, MW metric reported
```

#### Test 2.4.2: Meyer-Wallach Calculation

```python
# Test MW calculation
import numpy as np
from vqe_train import MeyerWallachCalculator

# Bell state: should have MW = 1 (maximally entangled)
bell_state = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])
mw = MeyerWallachCalculator.calculate(bell_state, 2)
assert 0.99 < mw < 1.01, f"Bell state MW should be ~1, got {mw}"

# Product state: should have MW = 0
product_state = np.array([1, 0, 0, 0])
mw = MeyerWallachCalculator.calculate(product_state, 2)
assert -0.01 < mw < 0.01, f"Product state MW should be ~0, got {mw}"
```

#### Test 2.4.3: Hardware Routing

```python
# Test HAL routing
from app.quantum.hal import HardwareAbstractionLayer

hal = HardwareAbstractionLayer()

# Small circuit
small_circuit = QuantumCircuit(4)
result = await hal.route_vqe_evaluation(small_circuit, hamiltonian)
assert result["backend"] == "local_apple_silicon"

# Medium circuit
medium_circuit = QuantumCircuit(15)
result = await hal.route_vqe_evaluation(medium_circuit, hamiltonian)
assert result["backend"] == "nvidia_gpu_wsl2"
```

### 2.5 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| VQE convergence time | < 60s for H2 | Wall clock for 90% energy convergence |
| Meyer-Wallach score | > 0.5 for useful entanglement | Average across discovered ansatzes |
| Barren plateau avoidance | Gradient variance > 1e-6 | 95% of discovered ansatzes |
| Energy accuracy | < 0.1 Ha from target | Final best candidate |

---

## Phase 3: Fixed Entity Architecture

### 3.1 Objective

Restructure Neo4j schema for deterministic historical retrieval of VQE ansatz architectures and enable Text2Cypher retrieval patterns.

### 3.2 Implementation Steps

#### Step 3.3.1: Create Neo4j Migration Script

**File**: `backend/alembic/versions/add_vqe_entity_schema.py`

```python
"""Add VQE entity schema to Neo4j

Revision ID: vqe_entity_schema
Revises: add_projects_related_tables
Create Date: 2026-03-30

This migration adds the Fixed Entity Architecture for VQE ansatz tracking:
- Molecule nodes with molecular properties
- Hamiltonian nodes with Pauli representations
- AnsatzMotif nodes with tokenized gate sequences
- AutoresearchRun nodes for experiment tracking
"""

from neo4j import AsyncGraphDatabase
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

# Migration queries
SCHEMA_QUERIES = [
    # === CONSTRAINTS ===
    "CREATE CONSTRAINT molecule_formula IF NOT EXISTS FOR (m:Molecule) REQUIRE m.formula IS UNIQUE",
    "CREATE CONSTRAINT hamiltonian_id IF NOT EXISTS FOR (h:Hamiltonian) REQUIRE h.id IS UNIQUE",
    "CREATE CONSTRAINT ansatz_motif_id IF NOT EXISTS FOR (a:AnsatzMotif) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT autoresearch_run_id IF NOT EXISTS FOR (r:AutoresearchRun) REQUIRE r.id IS UNIQUE",
    
    # === INDEXES ===
    "CREATE INDEX molecule_electrons IF NOT EXISTS FOR (m:Molecule) ON (m.electron_count)",
    "CREATE INDEX hamiltonian_qubits IF NOT EXISTS FOR (h:Hamiltonian) ON (h.num_qubits)",
    "CREATE INDEX ansatz_mw_score IF NOT EXISTS FOR (a:AnsatzMotif) ON (a.meyer_wallach_score)",
    "CREATE INDEX ansatz_depth IF NOT EXISTS FOR (a:AnsatzMotif) ON (a.depth)",
    "CREATE INDEX autoresearch_status IF NOT EXISTS FOR (r:AutoresearchRun) ON (r.status)",
    "CREATE INDEX autoresearch_timestamp IF NOT EXISTS FOR (r:AutoresearchRun) ON (r.timestamp)",
    
    # === FULLTEXT INDEX FOR TEXT2CYPHER ===
    "CREATE FULLTEXT INDEX ansatz_fulltext IF NOT EXISTS FOR (a:AnsatzMotif) ON EACH [a.gate_sequence]",
]


async def run_migration():
    """Execute the Neo4j schema migration."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "milimopassword")
    
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    try:
        async with driver.session() as session:
            for query in SCHEMA_QUERIES:
                try:
                    await session.run(query)
                    logger.info(f"Executed: {query[:50]}...")
                except Exception as e:
                    # Log warning but continue (constraint may already exist)
                    logger.warning(f"Query failed (may already exist): {e}")
                    
        logger.info("VQE entity schema migration completed successfully")
        
    finally:
        await driver.close()


def upgrade():
    """Alembic upgrade entry point."""
    asyncio.run(run_migration())


def downgrade():
    """Alembic downgrade - remove VQE schema."""
    async def remove_schema():
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "milimopassword")
        
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        
        drop_queries = [
            "DROP CONSTRAINT molecule_formula IF EXISTS",
            "DROP CONSTRAINT hamiltonian_id IF EXISTS",
            "DROP CONSTRAINT ansatz_motif_id IF EXISTS",
            "DROP CONSTRAINT autoresearch_run_id IF EXISTS",
            "DROP INDEX molecule_electrons IF EXISTS",
            "DROP INDEX hamiltonian_qubits IF EXISTS",
            "DROP INDEX ansatz_mw_score IF EXISTS",
            "DROP INDEX ansatz_depth IF EXISTS",
            "DROP INDEX autoresearch_status IF EXISTS",
            "DROP INDEX autoresearch_timestamp IF EXISTS",
            "DROP FULLTEXT INDEX ansatz_fulltext IF EXISTS",
        ]
        
        try:
            async with driver.session() as session:
                for query in drop_queries:
                    try:
                        await session.run(query)
                    except Exception:
                        pass
        finally:
            await driver.close()
            
    asyncio.run(remove_schema())


if __name__ == "__main__":
    upgrade()
```

#### Step 3.3.2: Create VQE Graph Client

**File**: `backend/app/graph/vqe_graph_client.py`

```python
"""
VQE-specific Neo4j client for Fixed Entity Architecture.

Implements Text2Cypher retrieval patterns for ansatz discovery.
"""

import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)


class VQEGraphClient:
    """
    Client for VQE-specific graph operations.
    
    Implements the Fixed Entity Architecture with:
    - Molecule → Hamiltonian → AnsatzMotif relationships
    - Historical success path tracking
    - Text2Cypher retrieval
    """
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "milimopassword")
        self.driver = None
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to Neo4j."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            self.connected = True
            logger.info(f"VQE GraphClient connected to {self.uri}")
            return True
        except Exception as e:
            logger.warning(f"VQE GraphClient connection failed: {e}")
            self.connected = False
            return False
            
    async def close(self):
        """Close connection."""
        if self.driver:
            await self.driver.close()
            self.connected = False
            
    async def index_molecule(
        self,
        formula: str,
        electron_count: int,
        pubchem_cid: Optional[int] = None,
        ground_state_energy: Optional[float] = None
    ) -> bool:
        """Index a molecule in the knowledge graph."""
        if not self.connected:
            return False
            
        query = """
        MERGE (m:Molecule {formula: $formula})
        SET m.electron_count = $electrons,
            m.pubchem_cid = $pubchem,
            m.ground_state_energy = $energy,
            m.indexed_at = datetime()
        """
        
        try:
            async with self.driver.session() as session:
                await session.run(query, {
                    "formula": formula,
                    "electrons": electron_count,
                    "pubchem": pubchem_cid,
                    "energy": ground_state_energy
                })
            return True
        except Exception as e:
            logger.error(f"Failed to index molecule: {e}")
            return False
            
    async def index_hamiltonian(
        self,
        molecule: str,
        hamiltonian_id: str,
        pauli_string: str,
        num_qubits: int,
        basis: str = "sto-3g"
    ) -> bool:
        """Index a molecular Hamiltonian."""
        if not self.connected:
            return False
            
        query = """
        MATCH (m:Molecule {formula: $molecule})
        MERGE (h:Hamiltonian {id: $h_id})
        SET h.pauli_string = $pauli,
            h.num_qubits = $qubits,
            h.basis = $basis,
            h.created_at = datetime()
        MERGE (m)-[:HAS_HAMILTONIAN]->(h)
        """
        
        try:
            async with self.driver.session() as session:
                await session.run(query, {
                    "molecule": molecule,
                    "h_id": hamiltonian_id,
                    "pauli": pauli_string,
                    "qubits": num_qubits,
                    "basis": basis
                })
            return True
        except Exception as e:
            logger.error(f"Failed to index Hamiltonian: {e}")
            return False
            
    async def index_ansatz_motif(
        self,
        motif_id: str,
        gate_sequence: List[str],
        depth: int,
        parameter_count: int,
        meyer_wallach_score: float,
        parent_motif_id: Optional[str] = None
    ) -> bool:
        """
        Index a discovered ansatz motif.
        
        Args:
            motif_id: Unique identifier
            gate_sequence: List of gate tokens
            depth: Circuit depth
            parameter_count: Number of parameters
            meyer_wallach_score: MW entanglement measure
            parent_motif_id: ID of parent motif (for evolution chain)
        """
        if not self.connected:
            return False
            
        query = """
        MERGE (a:AnsatzMotif {id: $id})
        SET a.gate_sequence = $gates,
            a.depth = $depth,
            a.parameter_count = $params,
            a.meyer_wallach_score = $mw,
            a.created_at = datetime()
        """
        
        if parent_motif_id:
            query += """
            WITH a
            MATCH (parent:AnsatzMotif {id: $parent_id})
            MERGE (a)-[:SUCCESSOR_OF]->(parent)
            """
            
        try:
            async with self.driver.session() as session:
                params = {
                    "id": motif_id,
                    "gates": gate_sequence,
                    "depth": depth,
                    "params": parameter_count,
                    "mw": meyer_wallach_score
                }
                if parent_motif_id:
                    params["parent_id"] = parent_motif_id
                    
                await session.run(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to index ansatz motif: {e}")
            return False
            
    async def link_successful_ansatz(
        self,
        hamiltonian_id: str,
        ansatz_id: str,
        converged: bool,
        energy: float,
        gradient_variance: float,
        iterations: int
    ) -> bool:
        """Link an ansatz to a Hamiltonian with performance metrics."""
        if not self.connected:
            return False
            
        query = """
        MATCH (h:Hamiltonian {id: $h_id})
        MATCH (a:AnsatzMotif {id: $a_id})
        MERGE (h)-[s:SOLVED_BY]->(a)
        SET s.converged = $converged,
            s.energy = $energy,
            s.gradient_variance = $grad_var,
            s.iterations = $iterations,
            s.solved_at = datetime()
        """
        
        try:
            async with self.driver.session() as session:
                await session.run(query, {
                    "h_id": hamiltonian_id,
                    "a_id": ansatz_id,
                    "converged": converged,
                    "energy": energy,
                    "grad_var": gradient_variance,
                    "iterations": iterations
                })
            return True
        except Exception as e:
            logger.error(f"Failed to link ansatz: {e}")
            return False
            
    async def retrieve_successful_ansatzes(
        self,
        molecule: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historically successful ansatz architectures.
        
        This implements the Text2Cypher retrieval pattern:
        "Find the best ansatz for this molecule"
        
        Returns:
            List of ansatz data with gate sequences and scores
        """
        if not self.connected:
            return []
            
        query = """
        MATCH (m:Molecule {formula: $mol})-[:HAS_HAMILTONIAN]->(h:Hamiltonian)
        MATCH (h)-[s:SOLVED_BY]->(a:AnsatzMotif)
        WHERE s.converged = true
          AND s.gradient_variance < 0.1
        RETURN a.id AS id,
               a.gate_sequence AS gates,
               a.meyer_wallach_score AS mw,
               a.depth AS depth,
               s.energy AS energy,
               s.iterations AS iterations
        ORDER BY s.energy ASC, a.meyer_wallach_score DESC
        LIMIT $limit
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, {
                    "mol": molecule,
                    "limit": limit
                })
                return await result.data()
        except Exception as e:
            logger.error(f"Failed to retrieve ansatzes: {e}")
            return []
            
    async def retrieve_ansatz_evolution_chain(
        self,
        motif_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get the full evolutionary history of an ansatz.
        
        Returns the chain of mutations that led to this motif.
        """
        if not self.connected:
            return []
            
        query = """
        MATCH path = (a:AnsatzMotif {id: $id})-[:SUCCESSOR_OF*]->(root:AnsatzMotif)
        RETURN [n IN nodes(path) | {
            id: n.id,
            gates: n.gate_sequence,
            mw: n.meyer_wallach_score,
            depth: n.depth
        }] AS evolution
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, {"id": motif_id})
                data = await result.single()
                return data["evolution"] if data else []
        except Exception as e:
            logger.error(f"Failed to retrieve evolution: {e}")
            return []
            
    async def text2cypher_search(
        self,
        natural_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Text2Cypher retrieval: convert natural language to Cypher.
        
        Example queries:
        - "best ansatz for H2"
        - "circuits with high entanglement"
        - "low depth ansatzes that converged"
        
        Args:
            natural_query: Natural language query
            context: Additional context (molecule, energy range, etc.)
        """
        if not self.connected:
            return []
            
        # Parse natural query into Cypher
        # This is a simplified implementation - production would use LLM
        query_lower = natural_query.lower()
        
        # Pattern matching for common queries
        if "best" in query_lower and "ansatz" in query_lower:
            molecule = context.get("molecule") if context else None
            if molecule:
                return await self.retrieve_successful_ansatzes(molecule)
            else:
                # Return best ansatzes overall
                query = """
                MATCH (h:Hamiltonian)-[s:SOLVED_BY]->(a:AnsatzMotif)
                WHERE s.converged = true
                RETURN a.id, a.gate_sequence, s.energy, a.meyer_wallach_score
                ORDER BY s.energy ASC
                LIMIT 10
                """
                
        elif "high entanglement" in query_lower or "meyer-wallach" in query_lower:
            min_mw = context.get("min_mw", 0.5) if context else 0.5
            query = """
            MATCH (a:AnsatzMotif)
            WHERE a.meyer_wallach_score > $min_mw
            RETURN a.id, a.gate_sequence, a.meyer_wallach_score, a.depth
            ORDER BY a.meyer_wallach_score DESC
            LIMIT 10
            """
            params = {"min_mw": min_mw}
            
        elif "low depth" in query_lower or "shallow" in query_lower:
            max_depth = context.get("max_depth", 10) if context else 10
            query = """
            MATCH (a:AnsatzMotif)
            WHERE a.depth < $max_depth
            RETURN a.id, a.gate_sequence, a.depth, a.meyer_wallach_score
            ORDER BY a.depth ASC
            LIMIT 10
            """
            params = {"max_depth": max_depth}
            
        else:
            # Fulltext search as fallback
            query = """
            CALL db.index.fulltext.queryNodes('ansatz_fulltext', $query)
            YIELD node AS a
            RETURN a.id, a.gate_sequence, a.meyer_wallach_score, a.depth
            LIMIT 10
            """
            params = {"query": natural_query}
            
        try:
            async with self.driver.session() as session:
                result = await session.run(query, params if 'params' in dir() else {})
                return await result.data()
        except Exception as e:
            logger.error(f"Text2Cypher search failed: {e}")
            return []
            
    async def index_autoresearch_run(
        self,
        run_id: str,
        commit_hash: str,
        val_bpb: float,
        energy: Optional[float],
        gradient_variance: Optional[float],
        status: str,
        molecule: Optional[str] = None,
        ansatz_id: Optional[str] = None
    ) -> bool:
        """Index an Autoresearch run (keep/discard/crash)."""
        if not self.connected:
            return False
            
        query = """
        MERGE (r:AutoresearchRun {id: $id})
        SET r.commit_hash = $commit,
            r.val_bpb = $bpb,
            r.energy = $energy,
            r.gradient_variance = $grad_var,
            r.status = $status,
            r.timestamp = datetime()
        """
        
        if molecule:
            query += """
            WITH r
            MATCH (m:Molecule {formula: $mol})
            MERGE (r)-[:TARGETED]->(m)
            """
            
        if ansatz_id and status == "keep":
            query += """
            WITH r
            MATCH (a:AnsatzMotif {id: $ansatz})
            MERGE (r)-[:DISCOVERED]->(a)
            """
            
        try:
            async with self.driver.session() as session:
                params = {
                    "id": run_id,
                    "commit": commit_hash,
                    "bpb": val_bpb,
                    "energy": energy,
                    "grad_var": gradient_variance,
                    "status": status,
                    "mol": molecule,
                    "ansatz": ansatz_id
                }
                await session.run(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to index Autoresearch run: {e}")
            return False


# Singleton
vqe_graph_client = VQEGraphClient()
```

#### Step 3.3.3: Update Workflow to Use VQE Graph Client

**File**: `backend/app/extensions/autoresearch/workflow.py` (additions)

```python
# === ADD IMPORT ===
from app.graph.vqe_graph_client import vqe_graph_client

# === MODIFY PERSISTENCE FUNCTION ===

async def persist_vqe_result(
    molecule: str,
    ansatz_id: str,
    gate_sequence: List[str],
    depth: int,
    parameter_count: int,
    meyer_wallach_score: float,
    energy: float,
    gradient_variance: float,
    converged: bool,
    iterations: int
):
    """
    Persist VQE result to SQL, TSV, and Neo4j.
    """
    # 1. SQL persistence (existing pattern)
    session = get_session()
    try:
        exp = Experiment(
            project=f"VQE-{molecule}",
            name=f"Ansatz-{ansatz_id[:8]}",
            agent="vqe-autoresearch",
            circuit_code=json.dumps(gate_sequence),
            backend="qiskit-aer",
            results={
                "energy": energy,
                "meyer_wallach": meyer_wallach_score,
                "gradient_variance": gradient_variance,
                "converged": converged
            },
            parameters={
                "depth": depth,
                "parameter_count": parameter_count,
                "iterations": iterations
            }
        )
        session.add(exp)
        session.commit()
    except Exception as e:
        logger.error(f"SQL persistence failed: {e}")
        session.rollback()
    finally:
        session.close()
        
    # 2. Neo4j persistence (Fixed Entity Architecture)
    if vqe_graph_client.connected:
        # Index the ansatz motif
        await vqe_graph_client.index_ansatz_motif(
            motif_id=ansatz_id,
            gate_sequence=gate_sequence,
            depth=depth,
            parameter_count=parameter_count,
            meyer_wallach_score=meyer_wallach_score
        )
        
        # Link to Hamiltonian with performance
        hamiltonian_id = f"{molecule}-sto-3g"
        await vqe_graph_client.link_successful_ansatz(
            hamiltonian_id=hamiltonian_id,
            ansatz_id=ansatz_id,
            converged=converged,
            energy=energy,
            gradient_variance=gradient_variance,
            iterations=iterations
        )
        
        logger.info(f"Persisted ansatz {ansatz_id} to Neo4j")
```

### 3.4 Testing Plan

#### Test 3.4.1: Schema Migration

```bash
# Run migration
cd backend
alembic upgrade head

# Verify in Neo4j Browser
# http://localhost:7474
# Run: SHOW CONSTRAINTS
# Expected: molecule_formula, hamiltonian_id, etc.
```

#### Test 3.4.2: Graph Client Operations

```python
import asyncio
from app.graph.vqe_graph_client import vqe_graph_client

async def test_vqe_graph():
    await vqe_graph_client.connect()
    
    # Index molecule
    await vqe_graph_client.index_molecule(
        formula="H2",
        electron_count=2,
        ground_state_energy=-1.137
    )
    
    # Index Hamiltonian
    await vqe_graph_client.index_hamiltonian(
        molecule="H2",
        hamiltonian_id="H2-sto-3g",
        pauli_string="IIII + IZII + ...",
        num_qubits=4
    )
    
    # Index ansatz
    await vqe_graph_client.index_ansatz_motif(
        motif_id="ansatz-001",
        gate_sequence=["H", "CNOT", "RZ", "RY"],
        depth=4,
        parameter_count=2,
        meyer_wallach_score=0.85
    )
    
    # Link
    await vqe_graph_client.link_successful_ansatz(
        hamiltonian_id="H2-sto-3g",
        ansatz_id="ansatz-001",
        converged=True,
        energy=-1.13,
        gradient_variance=0.05,
        iterations=50
    )
    
    # Retrieve
    results = await vqe_graph_client.retrieve_successful_ansatzes("H2")
    assert len(results) > 0, "Should retrieve linked ansatz"
    
    print(f"Retrieved {len(results)} ansatzes")
    
asyncio.run(test_vqe_graph())
```

#### Test 3.4.3: Text2Cypher

```python
# Test natural language queries
results = await vqe_graph_client.text2cypher_search("best ansatz for H2")
print(f"Best ansatzes: {results}")

results = await vqe_graph_client.text2cypher_search("high entanglement circuits")
print(f"High MW: {results}")

results = await vqe_graph_client.text2cypher_search("shallow depth")
print(f"Shallow: {results}")
```

---

## Phase 4: Self-Improving Dataloader

### 4.1 Objective

Upgrade `prepare.py` dataloader from O(N) to O(log N) best-fit packing and implement Analysis Agent for autonomous optimization.

### 4.2 Implementation Steps

#### Step 4.2.1: Create Segment Tree Packer

**File**: `autoresearch-mlx/packer.py`

```python
"""
Efficient document packing using segment tree.

Replaces linear O(N) best-fit search with O(log N) segment tree queries.
Optimized for variable-length quantum circuit token sequences.
"""

import math
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Document:
    """A tokenized document with cached length."""
    tokens: List[int]
    length: int
    
    @classmethod
    def from_tokens(cls, tokens: List[int]) -> 'Document':
        return cls(tokens=tokens, length=len(tokens))


class SegmentTreeNode:
    """Node in the segment tree."""
    
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end
        self.max_length: int = 0
        self.best_index: int = -1
        self.left: Optional['SegmentTreeNode'] = None
        self.right: Optional['SegmentTreeNode'] = None


class SegmentTreePacker:
    """
    Segment tree for O(log N) best-fit document packing.
    
    The tree is built over documents sorted by length.
    Each node stores the maximum document length in its range.
    
    Query: find longest document that fits in remaining space.
    Complexity: O(log N) per query.
    
    Example:
        packer = SegmentTreePacker(documents)
        best_idx = packer.best_fit(remaining=512)
        if best_idx is not None:
            doc = packer.pop(best_idx)
    """
    
    def __init__(self, documents: List[Document]):
        """
        Initialize packer with documents.
        
        Args:
            documents: List of Document objects
        """
        self.original_documents = documents
        self.documents = sorted(
            list(documents),
            key=lambda d: d.length
        )
        self.removed = set()  # Track removed indices
        
        # Build segment tree
        self.root = self._build_tree(0, len(self.documents))
        
    def _build_tree(self, start: int, end: int) -> Optional[SegmentTreeNode]:
        """Build segment tree recursively."""
        if start >= end:
            return None
            
        node = SegmentTreeNode(start, end)
        
        if end - start == 1:
            # Leaf node
            node.max_length = self.documents[start].length
            node.best_index = start
        else:
            # Internal node
            mid = (start + end) // 2
            node.left = self._build_tree(start, mid)
            node.right = self._build_tree(mid, end)
            
            # Merge children
            left_max = node.left.max_length if node.left else 0
            right_max = node.right.max_length if node.right else 0
            
            if left_max >= right_max:
                node.max_length = left_max
                node.best_index = node.left.best_index if node.left else -1
            else:
                node.max_length = right_max
                node.best_index = node.right.best_index if node.right else -1
                
        return node
        
    def best_fit(self, remaining: int) -> Optional[int]:
        """
        Find the longest document that fits in remaining space.
        
        Args:
            remaining: Available space (tokens)
            
        Returns:
            Index of best-fit document, or None if none fit
        """
        if remaining <= 0:
            return None
            
        return self._query(self.root, remaining)
        
    def _query(
        self, 
        node: Optional[SegmentTreeNode], 
        remaining: int
    ) -> Optional[int]:
        """
        Query segment tree for best-fit document.
        
        Recursively search for longest document <= remaining.
        """
        if node is None:
            return None
            
        # Prune: if max length exceeds remaining, can't use this subtree
        if node.max_length > remaining:
            # Need to search deeper
            # Try left first (shorter documents), then right
            left_result = self._query(node.left, remaining)
            if left_result is not None and left_result not in self.removed:
                return left_result
            return self._query(node.right, remaining)
            
        # Max length fits - find the actual best index
        # Search right subtree first (longer documents)
        if node.right:
            right_result = self._query(node.right, remaining)
            if right_result is not None and right_result not in self.removed:
                return right_result
                
        if node.left:
            left_result = self._query(node.left, remaining)
            if left_result is not None and left_result not in self.removed:
                return left_result
                
        # Check this node's best index
        if (node.best_index != -1 and 
            node.best_index not in self.removed and
            self.documents[node.best_index].length <= remaining):
            return node.best_index
            
        return None
        
    def pop(self, index: int) -> Document:
        """
        Remove and return document at index.
        
        Marks the index as removed (lazy deletion).
        
        Args:
            index: Index of document to remove
            
        Returns:
            The removed document
        """
        if index < 0 or index >= len(self.documents):
            raise IndexError(f"Index {index} out of range")
            
        self.removed.add(index)
        return self.documents[index]
        
    def is_empty(self) -> bool:
        """Check if all documents have been removed."""
        return len(self.removed) >= len(self.documents)
        
    def remaining_count(self) -> int:
        """Get count of remaining documents."""
        return len(self.documents) - len(self.removed)
        
    def reset(self):
        """Reset for new packing pass."""
        self.removed.clear()


class BestFitPacker:
    """
    High-level best-fit packing interface.
    
    Combines segment tree with fallback cropping logic.
    """
    
    def __init__(self, documents: List[List[int]]):
        """
        Initialize packer.
        
        Args:
            documents: List of token sequences
        """
        self.doc_objects = [
            Document.from_tokens(d) for d in documents
        ]
        self.tree = SegmentTreePacker(self.doc_objects)
        
    def pack_row(
        self, 
        row_capacity: int
    ) -> Tuple[List[int], int]:
        """
        Pack documents into a single row.
        
        Uses best-fit to fill as much space as possible.
        Crops shortest document if nothing fits.
        
        Args:
            row_capacity: Maximum tokens per row
            
        Returns:
            Tuple of (packed_tokens, num_documents_used)
        """
        row = []
        pos = 0
        docs_used = 0
        
        while pos < row_capacity and not self.tree.is_empty():
            remaining = row_capacity - pos
            
            # Find best-fit document
            best_idx = self.tree.best_fit(remaining)
            
            if best_idx is not None:
                # Use best-fit document
                doc = self.tree.pop(best_idx)
                row.extend(doc.tokens)
                pos += doc.length
                docs_used += 1
            else:
                # No document fits - crop shortest remaining
                # Find shortest document
                shortest_idx = self._find_shortest_remaining()
                if shortest_idx is None:
                    break
                    
                doc = self.tree.pop(shortest_idx)
                crop_len = min(remaining, doc.length)
                row.extend(doc.tokens[:crop_len])
                pos += crop_len
                docs_used += 1
                break
                
        return row, docs_used
        
    def _find_shortest_remaining(self) -> Optional[int]:
        """Find the shortest remaining document."""
        for i, doc in enumerate(self.tree.documents):
            if i not in self.tree.removed:
                return i
        return None
        
    def pack_batch(
        self,
        batch_size: int,
        row_capacity: int
    ) -> List[List[int]]:
        """
        Pack documents into a batch of rows.
        
        Args:
            batch_size: Number of rows to pack
            row_capacity: Tokens per row
            
        Returns:
            List of packed rows
        """
        rows = []
        for _ in range(batch_size):
            if self.tree.is_empty():
                break
            row, _ = self.pack_row(row_capacity)
            rows.append(row)
            
        return rows


def benchmark_packing(documents: List[List[int]], row_capacity: int = 2049):
    """
    Benchmark packing efficiency.
    
    Returns utilization metrics.
    """
    packer = BestFitPacker(documents)
    
    total_capacity = row_capacity
    total_used = 0
    
    while not packer.tree.is_empty():
        row, _ = packer.pack_row(row_capacity)
        total_used += len(row)
        
    utilization = total_used / total_capacity if total_capacity > 0 else 0
    
    return {
        "utilization": utilization,
        "documents_packed": len(documents),
        "waste_ratio": 1 - utilization
    }


if __name__ == "__main__":
    # Test segment tree packer
    import random
    
    # Generate test documents
    random.seed(42)
    docs = [[i] * random.randint(50, 500) for i in range(1000)]
    
    # Benchmark
    result = benchmark_packing(docs)
    print(f"Utilization: {result['utilization']:.2%}")
    print(f"Waste: {result['waste_ratio']:.2%}")
```

#### Step 4.2.2: Create Analysis Agent

**File**: `autoresearch-mlx/analysis_agent.py`

```python
"""
Analysis Agent for self-improving dataloader.

Profiles discarded Autoresearch runs and recommends optimizations.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ProfileMetrics:
    """Metrics from a profiling run."""
    
    # Memory metrics
    peak_memory_mb: float = 0.0
    memory_fragmentation: float = 0.0
    
    # Timing metrics
    total_time_s: float = 0.0
    compute_time_s: float = 0.0
    io_time_s: float = 0.0
    idle_time_s: float = 0.0
    
    # Token metrics
    total_tokens: int = 0
    padding_tokens: int = 0
    effective_tokens: int = 0
    
    # Batch metrics
    num_batches: int = 0
    avg_batch_utilization: float = 0.0
    
    # Hardware metrics
    gpu_utilization: float = 0.0
    memory_bandwidth_gbps: float = 0.0


class AnalysisAgent:
    """
    Autonomously analyzes discarded training runs.
    
    Responsibilities:
    1. Parse run.log for profiling metrics
    2. Identify optimization opportunities
    3. Recommend dataloader improvements
    4. Auto-apply safe optimizations
    """
    
    # Thresholds for recommendations
    THRESHOLDS = {
        "padding_ratio_high": 0.1,  # > 10% padding
        "idle_time_ratio_high": 0.05,  # > 5% idle
        "memory_fragmentation_high": 0.3,  # > 30% fragmentation
        "batch_utilization_low": 0.85,  # < 85% utilization
    }
    
    def __init__(self, autoresearch_dir: str = "/Users/mck/Desktop/milimoquantum/autoresearch-mlx"):
        self.autoresearch_dir = autoresearch_dir
        self.log_path = os.path.join(autoresearch_dir, "run.log")
        self.analysis_path = os.path.join(autoresearch_dir, "analysis.json")
        
    def parse_run_log(self) -> ProfileMetrics:
        """
        Parse run.log for profiling metrics.
        
        Returns:
            ProfileMetrics extracted from log
        """
        metrics = ProfileMetrics()
        
        if not os.path.exists(self.log_path):
            logger.warning(f"run.log not found: {self.log_path}")
            return metrics
            
        with open(self.log_path, "r") as f:
            content = f.read()
            
        # Parse peak memory
        match = re.search(r"peak_vram_mb:\s*([\d.]+)", content)
        if match:
            metrics.peak_memory_mb = float(match.group(1))
            
        # Parse training time
        match = re.search(r"training_seconds:\s*([\d.]+)", content)
        if match:
            metrics.compute_time_s = float(match.group(1))
            
        match = re.search(r"total_seconds:\s*([\d.]+)", content)
        if match:
            metrics.total_time_s = float(match.group(1))
            
        metrics.io_time_s = metrics.total_time_s - metrics.compute_time_s
        
        # Parse tokens
        match = re.search(r"total_tokens_M:\s*([\d.]+)", content)
        if match:
            metrics.total_tokens = int(float(match.group(1)) * 1e6)
            
        # Parse steps (batches)
        match = re.search(r"num_steps:\s*(\d+)", content)
        if match:
            metrics.num_batches = int(match.group(1))
            
        # Estimate padding (would need actual profiling in production)
        # For now, use heuristic
        metrics.padding_tokens = int(metrics.total_tokens * 0.05)  # Assume 5% baseline
        metrics.effective_tokens = metrics.total_tokens - metrics.padding_tokens
        
        # Calculate derived metrics
        if metrics.num_batches > 0:
            metrics.avg_batch_utilization = metrics.effective_tokens / (
                metrics.num_batches * 2048 * 16  # Assuming batch_size=16, seq_len=2048
            )
            
        metrics.idle_time_s = max(0, metrics.io_time_s * 0.1)  # Estimate
        
        return metrics
        
    def analyze_metrics(self, metrics: ProfileMetrics) -> Dict[str, Any]:
        """
        Analyze profile metrics and identify issues.
        
        Returns:
            Dict with 'issues', 'recommendations', 'priority'
        """
        issues = []
        recommendations = []
        
        # Check padding ratio
        if metrics.total_tokens > 0:
            padding_ratio = metrics.padding_tokens / metrics.total_tokens
            if padding_ratio > self.THRESHOLDS["padding_ratio_high"]:
                issues.append({
                    "type": "high_padding",
                    "severity": "high",
                    "value": padding_ratio,
                    "threshold": self.THRESHOLDS["padding_ratio_high"],
                    "message": f"Padding ratio {padding_ratio:.1%} exceeds threshold"
                })
                recommendations.append({
                    "action": "INCREASE_PACKING_AGGRESSION",
                    "priority": 1,
                    "description": "Switch to segment tree packer with best-fit decreasing"
                })
                
        # Check idle time
        if metrics.total_time_s > 0:
            idle_ratio = metrics.idle_time_s / metrics.total_time_s
            if idle_ratio > self.THRESHOLDS["idle_time_ratio_high"]:
                issues.append({
                    "type": "high_idle",
                    "severity": "medium",
                    "value": idle_ratio,
                    "threshold": self.THRESHOLDS["idle_time_ratio_high"],
                    "message": f"Idle time ratio {idle_ratio:.1%} indicates IO bottleneck"
                })
                recommendations.append({
                    "action": "OPTIMIZE_PREFETCH",
                    "priority": 2,
                    "description": "Increase prefetch buffer size and enable async loading"
                })
                
        # Check batch utilization
        if metrics.avg_batch_utilization < self.THRESHOLDS["batch_utilization_low"]:
            issues.append({
                "type": "low_batch_utilization",
                "severity": "medium",
                "value": metrics.avg_batch_utilization,
                "threshold": self.THRESHOLDS["batch_utilization_low"],
                "message": f"Batch utilization {metrics.avg_batch_utilization:.1%} below optimal"
            })
            recommendations.append({
                "action": "INCREASE_BATCH_SIZE",
                "priority": 3,
                "description": "Increase batch size or use gradient accumulation"
            })
            
        # Check memory fragmentation
        if metrics.memory_fragmentation > self.THRESHOLDS["memory_fragmentation_high"]:
            issues.append({
                "type": "high_fragmentation",
                "severity": "low",
                "value": metrics.memory_fragmentation,
                "threshold": self.THRESHOLDS["memory_fragmentation_high"],
                "message": "Memory fragmentation may cause allocation overhead"
            })
            recommendations.append({
                "action": "DEFRAGMENT_BUFFER",
                "priority": 4,
                "description": "Reset dataloader buffer periodically"
            })
            
        # Sort recommendations by priority
        recommendations.sort(key=lambda r: r["priority"])
        
        return {
            "issues": issues,
            "recommendations": recommendations,
            "priority": recommendations[0]["priority"] if recommendations else None,
            "metrics_summary": {
                "padding_ratio": metrics.padding_tokens / max(metrics.total_tokens, 1),
                "idle_ratio": metrics.idle_time_s / max(metrics.total_time_s, 1),
                "batch_utilization": metrics.avg_batch_utilization
            }
        }
        
    def apply_optimization(self, action: str) -> Dict[str, Any]:
        """
        Apply an optimization to the dataloader.
        
        Returns:
            Dict with 'success', 'changes_made', 'rollback_info'
        """
        result = {
            "success": False,
            "changes_made": [],
            "rollback_info": None
        }
        
        prepare_path = os.path.join(self.autoresearch_dir, "prepare.py")
        
        if not os.path.exists(prepare_path):
            result["error"] = "prepare.py not found"
            return result
            
        with open(prepare_path, "r") as f:
            original_content = f.read()
            
        result["rollback_info"] = {
            "file": prepare_path,
            "original_content": original_content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if action == "INCREASE_PACKING_AGGRESSION":
            # Replace linear best-fit with segment tree
            new_content = self._inject_segment_tree(original_content)
            
            if new_content != original_content:
                with open(prepare_path, "w") as f:
                    f.write(new_content)
                    
                result["success"] = True
                result["changes_made"].append(
                    "Injected SegmentTreePacker into make_dataloader()"
                )
                
        elif action == "OPTIMIZE_PREFETCH":
            # Increase buffer size
            new_content = original_content.replace(
                "buffer_size=1000",
                "buffer_size=5000"  # Increase 5x
            )
            
            if new_content != original_content:
                with open(prepare_path, "w") as f:
                    f.write(new_content)
                    
                result["success"] = True
                result["changes_made"].append(
                    "Increased buffer_size from 1000 to 5000"
                )
                
        elif action == "INCREASE_BATCH_SIZE":
            # This would require modifying train.py
            result["success"] = False
            result["error"] = "BATCH_SIZE optimization requires train.py modification"
            
        elif action == "DEFRAGMENT_BUFFER":
            # Add periodic buffer reset
            result["success"] = False
            result["error"] = "Buffer defragmentation not yet implemented"
            
        return result
        
    def _inject_segment_tree(self, content: str) -> str:
        """Inject segment tree packer import and usage."""
        
        # Add import at top
        if "from packer import" not in content:
            import_line = "from packer import BestFitPacker\n"
            # Insert after other imports
            import_match = re.search(
                r"(from multiprocessing import Pool\n)",
                content
            )
            if import_match:
                content = content.replace(
                    import_match.group(1),
                    import_match.group(1) + import_line
                )
                
        # Replace packing logic in make_dataloader
        # This is a simplified injection - production would be more careful
        old_packing = """
            while len(doc_buffer) < buffer_size:
                refill_buffer()
            remaining = row_capacity - pos
            best_idx = -1
            best_len = 0
            for index, doc in enumerate(doc_buffer):
                doc_len = len(doc)
                if doc_len <= remaining and doc_len > best_len:
                    best_idx = index
                    best_len = doc_len
        """
        
        new_packing = """
            while len(doc_buffer) < buffer_size:
                refill_buffer()
            remaining = row_capacity - pos
            # Use segment tree for O(log N) best-fit
            packer = BestFitPacker(doc_buffer)
            best_idx = packer.tree.best_fit(remaining)
        """
        
        if old_packing.strip() in content:
            content = content.replace(old_packing.strip(), new_packing.strip())
            
        return content
        
    def rollback(self, rollback_info: Dict[str, Any]) -> bool:
        """Rollback an optimization."""
        try:
            with open(rollback_info["file"], "w") as f:
                f.write(rollback_info["original_content"])
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
            
    def run_analysis_cycle(self) -> Dict[str, Any]:
        """
        Run full analysis and optimization cycle.
        
        1. Parse run.log
        2. Analyze metrics
        3. Apply top recommendation
        4. Return results
        
        Returns:
            Dict with 'analysis', 'optimization', 'success'
        """
        # Parse metrics
        metrics = self.parse_run_log()
        
        # Analyze
        analysis = self.analyze_metrics(metrics)
        
        # Apply top recommendation if any
        optimization_result = None
        if analysis["recommendations"]:
            top_rec = analysis["recommendations"][0]
            optimization_result = self.apply_optimization(top_rec["action"])
            
        # Save analysis
        with open(self.analysis_path, "w") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics.__dict__,
                "analysis": analysis,
                "optimization": optimization_result
            }, f, indent=2, default=str)
            
        return {
            "analysis": analysis,
            "optimization": optimization_result,
            "success": optimization_result["success"] if optimization_result else False
        }


async def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analysis Agent")
    parser.add_argument("--analyze", action="store_true", help="Run analysis only")
    parser.add_argument("--optimize", action="store_true", help="Apply optimizations")
    parser.add_argument("--rollback", action="store_true", help="Rollback last change")
    
    args = parser.parse_args()
    
    agent = AnalysisAgent()
    
    if args.analyze:
        metrics = agent.parse_run_log()
        analysis = agent.analyze_metrics(metrics)
        
        print("=== Analysis Results ===")
        print(f"\nMetrics:")
        print(f"  Peak Memory: {metrics.peak_memory_mb:.1f} MB")
        print(f"  Total Time: {metrics.total_time_s:.1f} s")
        print(f"  Compute Time: {metrics.compute_time_s:.1f} s")
        print(f"  Total Tokens: {metrics.total_tokens:,}")
        print(f"  Batch Utilization: {metrics.avg_batch_utilization:.1%}")
        
        print(f"\nIssues Found: {len(analysis['issues'])}")
        for issue in analysis['issues']:
            print(f"  - {issue['type']}: {issue['message']}")
            
        print(f"\nRecommendations: {len(analysis['recommendations'])}")
        for rec in analysis['recommendations']:
            print(f"  - {rec['action']}: {rec['description']}")
            
    elif args.optimize:
        result = agent.run_analysis_cycle()
        
        print("=== Optimization Results ===")
        print(f"Success: {result['success']}")
        if result['optimization']:
            print(f"Changes: {result['optimization']['changes_made']}")
            
    elif args.rollback:
        # Load last analysis for rollback info
        if os.path.exists(agent.analysis_path):
            with open(agent.analysis_path, "r") as f:
                last_analysis = json.load(f)
                
            if last_analysis.get('optimization', {}).get('rollback_info'):
                success = agent.rollback(
                    last_analysis['optimization']['rollback_info']
                )
                print(f"Rollback: {'Success' if success else 'Failed'}")
            else:
                print("No rollback info available")
        else:
            print("No analysis history found")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

#### Step 4.2.3: Integrate with Autoresearch Workflow

**File**: `backend/app/extensions/autoresearch/workflow.py` (additions)

```python
# === ADD IMPORTS ===
import sys
sys.path.insert(0, "/Users/mck/Desktop/milimoquantum/autoresearch-mlx")
from analysis_agent import AnalysisAgent

# === MODIFY run_autonomous_loop TO INCLUDE ANALYSIS ===

async def run_autonomous_loop_with_analysis(
    target: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Enhanced autonomous loop with Analysis Agent integration.
    
    After each experiment:
    1. Run analysis if experiment was discarded
    2. Apply dataloader optimizations
    3. Continue loop with improved configuration
    """
    analysis_agent = AnalysisAgent()
    
    # ... existing loop code ...
    
    for i in range(1, 11):
        # ... run experiment ...
        
        # After experiment evaluation
        if status == "discard":
            # Run analysis on discarded run
            yield f"event: log\ndata: {json.dumps({'text': 'Running Analysis Agent...'})}\n\n"
            
            try:
                analysis_result = analysis_agent.run_analysis_cycle()
                
                if analysis_result["success"]:
                    yield f"event: log\ndata: {json.dumps({'text': f'Analysis applied: {analysis_result[\"optimization\"][\"changes_made\"]}'})}\n\n"
                else:
                    yield f"event: log\ndata: {json.dumps({'text': 'No optimization needed'})}\n\n"
                    
            except Exception as e:
                yield f"event: log\ndata: {json.dumps({'text': f'Analysis error: {e}'})}\n\n"
```

### 4.3 Testing Plan

#### Test 4.3.1: Segment Tree Performance

```python
import time
import random
from packer import SegmentTreePacker, BestFitPacker, Document

# Generate test data
random.seed(42)
docs = [Document.from_tokens([i] * random.randint(50, 500)) for i in range(10000)]

# Benchmark linear search
start = time.time()
linear_results = []
for remaining in [512, 1024, 2048]:
    best_idx = -1
    best_len = 0
    for i, doc in enumerate(docs):
        if doc.length <= remaining and doc.length > best_len:
            best_idx = i
            best_len = doc.length
    linear_results.append(best_idx)
linear_time = time.time() - start

# Benchmark segment tree
start = time.time()
packer = SegmentTreePacker(docs)
tree_results = []
for remaining in [512, 1024, 2048]:
    tree_results.append(packer.best_fit(remaining))
tree_time = time.time() - start

print(f"Linear search: {linear_time*1000:.2f}ms")
print(f"Segment tree: {tree_time*1000:.2f}ms")
print(f"Speedup: {linear_time/tree_time:.1f}x")

# Verify correctness
assert tree_results == linear_results, "Results should match"
```

#### Test 4.3.2: Analysis Agent

```bash
# Run analysis on existing run.log
cd autoresearch-mlx
python analysis_agent.py --analyze

# Expected: Metrics extracted, issues identified, recommendations provided
```

#### Test 4.3.3: Packing Benchmark

```python
from packer import benchmark_packing
import random

# Generate variable-length documents
docs = [[i] * random.randint(100, 1000) for i in range(500)]

# Benchmark
result = benchmark_packing(docs, row_capacity=2049)

print(f"Utilization: {result['utilization']:.2%}")
print(f"Waste: {result['waste_ratio']:.2%}")

# Target: utilization > 95%, waste < 5%
assert result['utilization'] > 0.95, "Should achieve high utilization"
```

---

## Summary: Implementation Checklist

### Phase 1: NemoClaw Sandbox Hardening

- [ ] Install OpenClaw CLI and NemoClaw plugin
- [ ] Create `autoresearch-mlx/nemoclaw/blueprint.yaml`
- [ ] Create `autoresearch-mlx/nemoclaw/orchestrator/runner.py`
- [ ] Create `autoresearch-mlx/nemoclaw/policies/openclaw-sandbox.yaml`
- [ ] Update `workflow.py` with NemoClaw integration
- [ ] Test sandbox creation and policy enforcement
- [ ] Run full experiment in sandbox

### Phase 2: Agentic VQE Loop

- [ ] Create `autoresearch-mlx/vqe_train.py`
- [ ] Implement AnsatzTokenizer
- [ ] Implement MeyerWallachCalculator
- [ ] Implement HamiltonianBuilder
- [ ] Implement VQEAnsatzOptimizer
- [ ] Integrate with MQDD Chemistry Agent
- [ ] Add Hardware Abstraction Layer routing
- [ ] Test VQE convergence on H2 molecule

### Phase 3: Fixed Entity Architecture

- [ ] Create Neo4j migration `add_vqe_entity_schema.py`
- [ ] Create `vqe_graph_client.py`
- [ ] Implement molecule/hamiltonian/ansatz indexing
- [ ] Implement Text2Cypher retrieval
- [ ] Update workflow to use VQE graph client
- [ ] Test graph operations
- [ ] Verify historical retrieval

### Phase 4: Self-Improving Dataloader

- [ ] Create `autoresearch-mlx/packer.py` with SegmentTreePacker
- [ ] Create `autoresearch-mlx/analysis_agent.py`
- [ ] Implement profiling parser
- [ ] Implement optimization recommender
- [ ] Implement auto-apply for safe optimizations
- [ ] Integrate with autonomous loop
- [ ] Benchmark packing performance
- [ ] Verify O(log N) complexity

---

## Risk Register

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|-------------|--------|------------|-------|
| R1 | NemoClaw installation fails on macOS | Medium | High | Use Docker container for blueprint runner | DevOps |
| R2 | VQE convergence slower than expected | Medium | Medium | Start with small molecules (H2), validate before scaling | ML Lead |
| R3 | Neo4j migration breaks existing data | Low | High | Run parallel schema, gradual migration, backups | Backend Lead |
| R4 | Segment tree overhead exceeds benefits | Low | Low | Benchmark with 100K+ documents before deployment | Performance Engineer |
| R5 | Analysis Agent makes wrong optimization | Medium | Medium | Require human approval for destructive changes | ML Lead |

---

## Timeline

| Week | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|
| 1-2 | Install, Blueprint | - | - | - |
| 3-4 | Runner, Policy | VQE Module | - | - |
| 5-6 | Integration, Test | HAL Routing | Migration | - |
| 7-8 | Validation | MQDD Integration | Graph Client | Packer |
| 9-10 | - | Testing | Text2Cypher | Analysis Agent |
| 11-12 | - | Validation | Testing | Integration |
| 13-14 | - | - | - | Testing, Validation |

**Total Duration**: 14 weeks (3.5 months)

---

## Document Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Lead | | | |
| ML Lead | | | |
| Backend Lead | | | |
| DevOps | | | |
| Security | | | |

---

*End of Implementation Plan*

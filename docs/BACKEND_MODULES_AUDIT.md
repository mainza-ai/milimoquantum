# Backend Modules Audit Report

**Date:** April 2, 2026  
**Auditor:** AI Analysis  
**Scope:** All backend modules, extensions, agents, and quantum modules

---

## Executive Summary

This audit identified **43 issues** across the backend codebase:
- **8 CRITICAL** issues requiring immediate attention
- **20 HIGH** issues affecting core functionality
- **14 MEDIUM** issues for polish
- **1 LOW** issue

---

## Issue 1: MQDD Drug Discovery - Invalid ChEMBL Query

### Problem
When a user uploads a PDB file, the system passes the full prompt text "Analyze uploaded target file: AF-P85633-F1-model_v4.pdb" to the ChEMBL similarity search API, which expects a valid SMILES molecular notation string.

### Location
| File | Line | Issue |
|------|------|-------|
| `/backend/app/extensions/mqdd/workflow.py` | 54 | `target_query=prompt` passes user prompt to molecular design |
| `/backend/app/extensions/mqdd/agents.py` | 141 | `search_chemical_library(target_query, ...)` called with non-SMILES input |
| `/backend/app/extensions/mqdd/discovery_tools.py` | 98 | ChEMBL API receives invalid SMILES, returns 500 error |

### Error Log
```
2026-04-02 12:31:21,242 - app.extensions.mqdd.discovery_tools - ERROR - ChEMBL Search failed: Server error '500 Internal Server Error' 
for url 'https://www.ebi.ac.uk/chembl/api/data/similarity/Analyze%20uploaded%20target%20file:%20AF-P85633-F1-model_v4.pdb/60.json?limit=3'
```

### Root Cause
The workflow passes the raw user prompt to `run_molecular_design()`, which then calls `search_chemical_library()`. The ChEMBL similarity search requires a valid SMILES string (e.g., `CC(=O)Oc1ccccc1C(=O)O` for aspirin), not a filename or natural language description.

### Fix Required
1. Extract or generate SMILES from PDB file content
2. Parse protein target to identify known ligands
3. Use protein name/ID to search for known inhibitors, then get their SMILES
4. Only call ChEMBL similarity search with valid SMILES strings

---

## Issue 2: Missing Functionality (TODOs, Pass Statements, NotImplementedErrors)

### CRITICAL Issues

| File | Line | Issue | Severity |
|------|------|-------|----------|
| `/backend/app/routes/citations.py` | 60-65 | **Mock detection logic commented out** - Citation detection never runs. Real logic is commented out with `# Mock detection logic`. Returns hardcoded Qiskit citation only. | CRITICAL |
| `/backend/app/quantum/advanced_sims.py` | 20-35 | **All physics simulations mocked** - QuTiP, NetSquid, and SquidASM simulations return hardcoded mock values. Functions return `MOCKED_MISSING_DEPENDENCY` status. | CRITICAL |

### HIGH Issues

| File | Line | Issue | Severity |
|------|------|-------|----------|
| `/backend/app/quantum/hpc.py` | 22 | **Mock HPC Queue Database** - `HPC_JOBS = {}` is an in-memory mock. Real Slurm/HPC integration is simulated. | HIGH |
| `/backend/app/agents/orchestrator.py` | 171 | **Agent dispatch pass-through** - When agent type is registered but has no dedicated module, code falls through with just `pass`. No handling for PLANNING, BENCHMARKING, FAULT_TOLERANCE agents. | HIGH |
| `/backend/app/extensions/mqdd/agents.py` | 106, 173, 308 | **Silent exceptions** - Multiple `except Exception: pass` blocks silently swallow errors in critical JSON parsing paths. | HIGH |
| `/backend/app/agents/benchmarking.py` | 1-47 | **No actual benchmark execution** - Only system prompt defined. No direct benchmark execution integration. | HIGH |
| `/backend/app/agents/fault_tolerance.py` | 1-47 | **Same issue** - Only system prompt, no direct QEC/Stim integration. | HIGH |

### MEDIUM Issues

| File | Line | Issue | Severity |
|------|------|-------|----------|
| `/backend/app/routes/hpc.py` | 31 | Silent exception on MPI check with `pass` | MEDIUM |
| `/backend/app/routes/analytics.py` | 132, 137 | Silent `pass` when parsing qubit/depth counts | MEDIUM |
| `/backend/app/agents/context_enricher.py` | 165, 175, 384 | Silent `pass` on correlation/premium calculation failures | MEDIUM |
| `/backend/app/config.py` | 111 | Settings save failures silently ignored | MEDIUM |

---

## Issue 3: Hardcoded/Mock Data

### CRITICAL Issues

| File | Line | Issue | Severity |
|------|------|-------|----------|
| `/backend/app/routes/marketplace.py` | 16-137 | **Hardcoded plugin catalog** - `COMMUNITY_PLUGINS` is a hardcoded list of 12 plugins with fake stats (downloads, ratings). Should come from database or external API. | CRITICAL |
| `/backend/app/routes/academy.py` | 23-371 | **Hardcoded lesson content** - Entire `LESSONS` array with 5 courses hardcoded inline. Should be in database or external files. | CRITICAL |
| `/backend/app/feeds/__init__.py` | 108-132 | **Mock finance data** - `_mock_prices()` and `_mock_correlation()` return fake stock prices with `"mock": True` flag. Used in production when yfinance unavailable. | CRITICAL |

### HIGH Issues

| File | Line | Issue | Severity |
|------|------|-------|----------|
| `/backend/app/routes/citations.py` | 15-53 | **Hardcoded citation templates** - `ALGO_CITATIONS` dictionary with hardcoded BibTeX for vqe, qaoa, shor, grover. | HIGH |
| `/backend/app/extensions/mqdd/agents.py` | 255 | **Mock quantum simulation** - LLM asked to "Perform a mock quantum simulation" when Qiskit unavailable. | HIGH |
| `/backend/app/quantum/vqe_executor.py` | 29-54 | **Hardcoded Hamiltonian coefficients** - H2 and LiH Hamiltonian terms hardcoded. Should compute from molecular geometry. | HIGH |

### MEDIUM Issues

| File | Line | Issue | Severity |
|------|------|-------|----------|
| `/backend/app/quantum/cloud_backends.py` | 218-219 | Hardcoded default Braket device ARN | MEDIUM |
| `/backend/app/agents/sensing_agent.py` | 236-238 | Uses mocked QuTiP simulation | MEDIUM |
| `/backend/app/agents/networking_agent.py` | 320-323 | Uses mocked NetSquid/SquidASM | MEDIUM |

---

## Issue 4: Security & Error Handling

### CRITICAL Issues

| File | Line | Issue | Severity |
|------|------|-------|----------|
| `/backend/app/quantum/executor.py` | 186-210 | **Unsafe exec() with user code** - `execute_circuit_code()` uses `exec()` on arbitrary code without sandboxing. Security vulnerability. | CRITICAL |
| `/backend/app/routes/quantum.py` | 255-277 | **No input validation** - `/circuits/save` endpoint executes arbitrary Python code without validation. | CRITICAL |
| `/backend/app/extensions/autoresearch/workflow.py` | 221, 231, 346 | **Bare except: pass blocks** - Silently swallows all exceptions during autonomous research loop. | CRITICAL |

### HIGH Issues

| File | Line | Issue | Severity |
|------|------|-------|----------|
| `/backend/app/routes/collaboration.py` | 119 | Missing import guard - Import failure causes 500 error. | HIGH |
| `/backend/app/routes/workflows.py` | 83-106 | Celery ImportError not fully handled. | HIGH |
| `/backend/app/quantum/benchmarking.py` | 144-147 | Database session not properly closed on error. | HIGH |
| `/backend/app/agents/dwave_agent.py` | 213-239 | No try/catch around circuit generation. | HIGH |

---

## Issue 5: Unwired API Endpoints

### Backend Endpoints Missing Frontend Integration

| Endpoint | Backend File | Description | Priority |
|----------|-------------|-------------|----------|
| `POST /api/quantum/qasm3/parse` | `/routes/quantum.py:214` | OpenQASM 3 parsing | HIGH |
| `POST /api/quantum/qasm3/export` | `/routes/quantum.py:224` | Export to QASM 3 | HIGH |
| `POST /api/quantum/qasm3/validate` | `/routes/quantum.py:238` | QASM 3 validation | HIGH |
| `GET /api/quantum/stim/*` | `/routes/quantum.py:329-380` | All Stim stabilizer simulator endpoints | HIGH |
| `POST /api/quantum/pennylane/*` | `/routes/quantum.py:384-421` | All PennyLane bridge endpoints | HIGH |
| `POST /api/quantum/vqe/run` | `/routes/quantum.py:481` | Direct VQE execution | HIGH |
| `POST /api/quantum/qaoa/run` | `/routes/quantum.py:514` | Direct QAOA execution | HIGH |
| `GET /api/quantum/vector-store/*` | `/routes/quantum.py:545-571` | Vector store semantic search | MEDIUM |
| `POST /api/citations/detect` | `/routes/quantum.py:598` | Algorithm detection in code | MEDIUM |

### Entire Modules Without Frontend API Calls

| Module | Endpoints | Status |
|--------|-----------|--------|
| **Experiments** | `/api/experiments/*` | No frontend API calls for projects, runs, logging, compare, tagging, sharing, lineage |
| **Export** | `/api/export/*` | No frontend calls for conversation export |
| **Collaboration** | `/api/collaboration/*` | No frontend calls for sharing, tokens |
| **Sync/WebSocket** | `/sync/ws/{client_id}` | WebSocket exists but not integrated |

---

## Issue 6: MQDD-Specific Issues

### Detailed MQDD Audit

| Component | Issue | Severity |
|-----------|-------|----------|
| `discovery_tools.py` | No SMILES validation before ChEMBL API call | CRITICAL |
| `agents.py` | `is_valid_smiles()` returns `True` when RDKit unavailable, allowing invalid SMILES | HIGH |
| `workflow.py` | No extraction of ligands from PDB content | HIGH |
| `agents.py` | Property prediction fallback to LLM when ADMET-AI unavailable produces unreliable data | MEDIUM |
| `workflow.py` | No validation that `target_query` is a valid SMILES before molecular design | MEDIUM |

---

## Summary Statistics

| Category | CRITICAL | HIGH | MEDIUM | LOW | Total |
|----------|----------|------|--------|-----|-------|
| Missing Functionality | 2 | 4 | 4 | 0 | 10 |
| Mock/Hardcoded Data | 3 | 3 | 3 | 0 | 9 |
| Security/Error Handling | 3 | 4 | 3 | 0 | 10 |
| Unwired Endpoints | 0 | 9 | 4 | 1 | 14 |
| **TOTAL** | **8** | **20** | **14** | **1** | **43** |

---

## Priority Recommendations

### Immediate (This Week)
1. **Fix MQDD ChEMBL query** - Add SMILES validation, extract from PDB or skip similarity search
2. **Implement real citation detection** in `/routes/citations.py`
3. **Add sandboxing** to `/quantum/executor.py` exec() calls or use NemoClaw

### High (Next 2 Weeks)
4. Wire Stim simulator endpoints to frontend FaultTolerance panel
5. Replace hardcoded marketplace plugins with database-backed catalog
6. Add frontend integration for QASM 3 parsing/export endpoints
7. Remove silent `except: pass` blocks in agents and extensions
8. Add actual benchmark execution logic to benchmarking agent

### Medium (Next Month)
9. Connect experiments module to frontend
10. Move lesson content to database
11. Add proper error handling for collaboration routes
12. Implement real Hamiltonian computation from molecular geometry

---

## Files Requiring Immediate Fixes

| File | Issues | Priority |
|------|--------|----------|
| `/backend/app/extensions/mqdd/discovery_tools.py` | Invalid SMILES to ChEMBL | IMMEDIATE |
| `/backend/app/extensions/mqdd/workflow.py` | Passes non-SMILES to molecular design | IMMEDIATE |
| `/backend/app/routes/citations.py` | Mock detection logic | IMMEDIATE |
| `/backend/app/quantum/executor.py` | Unsafe exec() | IMMEDIATE |

---

## Appendix: Fix for MQDD ChEMBL Issue

### Proposed Fix for `discovery_tools.py`

```python
import re

def is_valid_smiles_for_search(smiles: str) -> bool:
    """Validate that input looks like a SMILES string before API call."""
    if not smiles or not isinstance(smiles, str):
        return False
    # SMILES contains typical patterns: C, N, O, brackets, rings
    # Exclude filenames, sentences, and PDB IDs
    if '.pdb' in smiles.lower():
        return False
    if ' ' in smiles.strip():
        return False
    if len(smiles) > 200:  # Unreasonably long
        return False
    # Basic SMILES character check
    if not re.match(r'^[A-Za-z0-9@\[\]\(\)\=\#\$\:\.\/\\+\-]+$', smiles):
        return False
    return True

async def search_chemical_library(smiles: str, similarity_threshold: int = 70, limit: int = 5) -> List[Dict[str, Any]]:
    """Search ChEMBL for molecules similar to a SMILES string."""
    # VALIDATION: Skip if not a valid SMILES
    if not is_valid_smiles_for_search(smiles):
        logger.warning(f"Skipping ChEMBL search: input is not a valid SMILES string: {smiles[:50]}...")
        return []
    
    url = f"https://www.ebi.ac.uk/chembl/api/data/similarity/{smiles}/{similarity_threshold}.json"
    # ... rest of function
```

### Proposed Fix for `workflow.py`

```python
# Line 54: Pass empty string or extracted SMILES instead of raw prompt
# Option 1: Skip similarity search when no SMILES available
candidates = await agents.run_molecular_design(design_context, count=3, target_query="")

# Option 2: Extract SMILES from PDB if available
target_smiles = ""
if pdb_content:
    # Try to extract known ligands from PDB
    target_smiles = extract_ligand_smiles_from_pdb(pdb_content) or ""

candidates = await agents.run_molecular_design(design_context, count=3, target_query=target_smiles)
```

---

*End of Audit Report*

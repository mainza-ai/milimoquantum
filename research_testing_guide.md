# Test Guide — Research & Drug Discovery (MQDD)

Use these specialized prompts to verify the logic in the **Autoresearch-MLX** and **Milimo Quantum Drug Discovery (MQDD)** extensions.

## 1. Autoresearch-MLX (Iterative Loops)
**Goal**: Verify that the backend can handle autonomous research iterations, imports (`get_session`), and data persistence.

### Scenario: VQE Optimization Loop
*   **Prompt**: *"Run an autoresearch loop to find the optimal classical optimizer for a 4-qubit H2 molecule simulation. Track 'energy' as the primary metric. Perform at least 3 iterations."*
*   **What to look for**:
    - [ ] Terminal logs show `Iteration 1/3`, `Iteration 2/3`, etc.
    - [ ] No `NameError: get_session` appears in the logs (Verified Fix #1).
    - [ ] The "Results" tab in the dashboard populates with energy values.

## 2. MQDD — Drug Discovery Workflow
**Goal**: Verify the integration of molecular lookups (PubChem), LLM-based analysis, and result persistence.

### Scenario: Caffeine Analysis
*   **Prompt**: *"Execute the MQDD workflow for 'Caffeine'. I want a full structural analysis and a simulated interaction profile for common CNS receptors."*
*   **What to look for**:
    - [ ] The **Intelligence Hub** logs show a call to the PubChem API.
    - [ ] The response contains the canonical name (`1,3,7-trimethylpurine-2,6-dione`) and SMILES string.
    - [ ] A new **Artifact** (Results/Notebook) is generated in the chat with the simulation data.

### Scenario: Synthesis Planning
*   **Prompt**: *"Propose a quantum-accelerated synthesis pathway for a novel aspirin derivative with improved bioavailability."*
*   **What to look for**:
    - [ ] The agent correctly references the **User Hardware Profile** (Mac M-series) for simulation steps.
    - [ ] The workflow successfully saves the "Synthesis Plan" artifact.

## 3. Knowledge Graph Connectivity (Multi-Agent)
**Goal**: Verify that research from one agent is visible to others via the Graph.

1.  **Step 1 (Research Agent)**: *"Find the latest research papers on 'Aspirin bioavailability' using the ArXiv feed."*
2.  **Step 2 (MQDD Agent)**: *"Using the papers my colleague just found, what specific molecular modifications were suggested?"*
*   **Expected Result**: The MQDD agent should reference the papers found in Step 1 using **GraphRAG** (passed interactions context).

## 4. Verification Checklist
- Run `backend/tests/test_chat.py` to ensure core labels are still valid.
- Check `~/.milimoquantum/milimoquantum.db` after research to see new rows in `experiments` and `artifacts`.

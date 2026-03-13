# Test Prompts — Infrastructure Connectivity

Use these prompts to verify that Projects, GraphRAG, and the Intelligence Hub are correctly linked and isolated.

## 1. Project Creation & Isolation
**Goal**: Verify that conversations and context do not leak between projects.

1.  **Project A Setup**: 
    - Create a project named **"Molecular Simulation"**.
    - Prompt: *"I am researching H2O molecular simulations using VQE. What is the best classical-quantum hybrid optimizer for this?"*
2.  **Project B Setup**:
    - Create a project named **"Shor's Algorithm Analysis"**.
    - Prompt: *"Can you explain the order-finding step in Shor's algorithm?"*
3.  **Cross-Project Verification**:
    - In **Project B**, ask: *"What did we discuss about water molecules earlier?"*
    - **Expected Result**: The AI should state it doesn't have that context in the *current* project, confirming project-level isolation.

## 2. GraphRAG & History Memory
**Goal**: Verify that the AI can traverse past interactions *within* a project.

1.  **Recall Test**: In the **"Molecular Simulation"** project, ask:
    - Prompt: *"Based on our previous discussion about optimizers, which one would scale best to 20 qubits?"*
    - **Expected Result**: The AI should reference your first discussion about VQE optimizers via the Graph/SQL linkage.

## 3. Intelligence Hub & Experiment Linkage
**Goal**: Verify that the Hub correctly filters SQL experiments by project.

1.  **Experiment Run**: In any project, trigger an Autoresearch loop or simple experiment.
2.  **Verification**: Ask: *"Summarize my recent experiments in this project."*
    - **Expected Result**: The AI should use the `past_experiments` context from the Hub to list only the experiments related to the current `project_id`.

## 4. Hardware Awareness
**Goal**: Verify that the HAL context is being injected into the prompt.

1.  **Hardware Check**: Ask any agent:
    - Prompt: *"What hardware architecture are we running on, and are there any GPUs available for simulation?"*
    - **Expected Result**: The AI should describe your Mac's architecture (ARM64) and Metal/GPU status as provided by the `hal_config`.

## 5. Global Memory (QGI Specialist)
**Goal**: Test the QGI agent's ability to "bridge" projects if explicitly asked.

1.  **Global Seek**: Switch to the **QGI Agent** and ask:
    - Prompt: *"Search all my projects for any mentions of 'Surface Codes'. Where did I discuss this?"*
    - **Expected Result**: Since the QGI agent has elevated permissions, it should traverse the global graph to find cross-project entities.

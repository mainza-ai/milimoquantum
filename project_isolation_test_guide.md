# Milimo Quantum — Project Isolation Test Guide

This guide provides test prompts and scenarios to verify that conversations, memories, and experiments are correctly scoped to projects.

## Prerequisite
Ensure the backend is running and the `project_id` schema updates have been applied.

---

## Test Scenario 1: Basic Conversation Scoping
**Goal:** Verify that a new conversation is associated with a specific project and increments the count.

1. **Setup:**
   - Create a new project called "Quantum Chemistry Phase 1".
   - Note the `project_id` (or ensure the UI has it selected).
2. **Action:**
   - Send a message: "Analyze the water molecule for VQE simulation."
3. **Verification:**
   - Go to Project Details for "Quantum Chemistry Phase 1".
   - **Expected:** Conversation count should be 1.
   - **Expected:** The conversation should appear in the project's list.

---

## Test Scenario 2: Memory Isolation
**Goal:** Verify that agents do not "leak" memory between projects.

1. **Setup:**
   - Create Project A: "Superconducting Hardware".
   - Create Project B: "Trapped Ion Hardware".
2. **Action in Project A:**
   - Chat: "We are focusing on 54-qubit Sycamore chips."
3. **Action in Project B:**
   - Chat: "What hardware setup are we discussing?"
4. **Verification:**
   - **Expected:** In Project B, the agent should NOT mention Sycamore or 54 qubits unless it's general knowledge. It should stick to the "Trapped Ion" context if the retrieval is working correctly.

---

## Test Scenario 3: Sync Engine & Experiments
**Goal:** Verify that experiments can be synced without `sqlite3.OperationalError`.

1. **Action:**
   - Use the "Run Experiment" feature in any project.
   - Observe the backend logs for `Error in sync loop`.
2. **Verification:**
   - **Expected:** The sync engine should run without `no such column: experiments.project_id` errors.
   - **Expected:** Experiments should sync to the cloud (if configured) with the correct `project_id`.

---

## Test Scenario 4: Autoresearch Integration
**Goal:** Verify that Autoresearch results are saved to the project.

1. **Action:**
   - Trigger an Autoresearch task: "Find the latest papers on error mitigation for VQE."
2. **Verification:**
   - **Expected:** Once complete, checks the "Artifacts" or "Results" section of the active project.
   - **Expected:** The research paper summaries should be listed there.

---
name: ai-logic-patterns
description: AI Logic Patterns Technical Encyclopedia: CoT Reasoning, Plan-and-Execute, State Persistence, and Self-Correction Loops.
---

# Skill: AI Logic Patterns (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design and implementation of autonomous cognitive architectures for AI agents in the 2025 ecosystem. This document defines the standards for deterministic reasoning, multi-step orchestration, state management, and robust self-healing logic.

---

## 1. Fundamental Cognitive Architectures
Defining the skeletal structure of AI decision-making.

### 1.1 Chain-of-Thought (CoT) Reasoning Flow
*   **Logic:** Forcing the agent into a sequential reasoning path where each step $S_n$ depends on the result of $S_{n-1}$. This explicitly increases the available "Latent Reasoning Bandwidth" for complex operations.
*   **Verification:** Mandatory inclusion of a "Reality Check" at the end of the reasoning chain to ensure the logic has not drifted from the original constraints.

### 1.2 The "Plan-and-Execute" Orchestration Pattern
Separating the "Strategist" from the "Executor" to minimize context pollution and improve success rates on complex objectives.
*   **Phase 1: Planning:** The agent generates a high-level DAG (Directed Acyclic Graph) of sub-tasks.
*   **Phase 2: Execution:** A specialized executor processes each node in the DAG.
*   **Phase 3: Synthesis:** The strategist reviews the aggregated results and generates the final output.
*   **Success Metric:** Reduces the probability of "Cognitive Overload" failure by distributed task handling.

---

## 2. State Management & Memory Persistence
Maintaining high-fidelity continuity across asynchronous conversational boundaries.

### 2.1 Short-Term Memory (Context Saturation)
*   **Logic:** Utilizing the LLM's context window as a "CPU Cache" ($L1$). 
*   **Constraint:** Zero tolerance for irrelevant historical data. Mandatory "Context Pruning" after every 5 conversational turns to maintain a high signal-to-noise ratio.

### 2.2 Long-Term Memory (Vector Saturation)
*   **Logic:** Utilizing a RAG-based memory system (e.g., Pinecone, Weaviate) to store and retrieve historical technical patterns and user preferences.
*   **Standard:** Mandatory inclusion of a "Semantic Integrity" check during retrieval to ensure that the retrieved context is actually relevant to the current mathematical or logical goal.

---
<!-- CHUNK_END_SECTION_2 -->

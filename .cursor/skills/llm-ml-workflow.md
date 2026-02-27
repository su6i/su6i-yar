---
name: llm-ml-workflow
description: LLM & ML Engineering Technical Encyclopedia: DSPy Optimization, QLoRA NF4 Math, vLLM PagedAttention, and FlashAttention-3 Standards.
---

# Skill: LLM & ML Engineering (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the architecting, fine-tuning, and deployment of Large Language Models (LLMs) and Machine Learning (ML) systems in the 2025 ecosystem. This document defines the standards for declarative prompt optimization, memory-efficient fine-tuning, and high-throughput inference.

## 1. Declarative Prompt Optimization (DSPy)
Moving from manual "Prompt Engineering" to systematic "Program Optimization" via code-centric signatures and modules.

### 1.1 Core Architecture (Signatures & Modules)
*   **Signatures:** Typed interfaces for LLM tasks that separate the "what" from the "how."
    ```python
    import dspy

    class RAG(dspy.Signature):
        """Answer questions with retrieved context."""
        context = dspy.InputField(desc="retrieved passages")
        question = dspy.InputField()
        answer = dspy.OutputField(desc="detailed answer with citations")
    ```
*   **Modules:** Standardized prompting patterns that combine signatures with logic:
    *   `dspy.ChainOfThought`: Mandatory for complex reasoning (CoT).
    *   `dspy.ReAct`: Enabling agentic tool use (Reason + Act).
    *   `dspy.ProgramOfThought`: Generating Python code to solve mathematical or logical sub-problems.

### 1.2 Advanced Teleprompters (Optimizers)
The internal logic behind automatic few-shot selection and instruction tuning.
*   **BootstrapFewShot:** A simple optimizer that "bootstraps" examples by asking the teacher model to generate answers for a training subset.
*   **BootstrapFewShotWithRandomSearch:** Systematically explores thousands of candidate label combinations using diversity sampling to maximize a defined metric (e.g., F1, Exact Match, or semantic similarity).
*   **MIPRO (Multi-prompt Instruction PRogram Optimizer):** Utilizing Bayesian Optimization for simultaneous instruction tuning and few-shot selection.
*   **Teleprompter Hyperparameters:**
    *   `max_bootstrapped_demos`: Typically 4-8 for optimal context utilization.
    *   `num_candidate_programs`: 10-50 depending on compute budget.

---

## 2. Memory-Efficient Fine-Tuning (LoRA & QLoRA)
The standard for democratizing LLM fine-tuning on consumer-grade and enterprise hardware.

### 2.1 Low-Rank Adaptation (LoRA)
*   **Mathematical Derivation:** For a weight matrix $W \in \mathbb{R}^{d \times k}$, we freeze $W$ and introduce $A \in \mathbb{R}^{d \times r}$ and $B \in \mathbb{R}^{r \times k}$ (where $r$ is the rank). The forward pass becomes:
    $H = W_0X + \Delta WX = W_0X + BAX$
*   **Rank Selection:** 2025 standards suggest $r=8$ or $r=16$ for task-specific tuning, and $r=64$ or $r=128$ for general knowledge injection.

### 2.2 Quantized LoRA (QLoRA)
Leveraging 4-bit NormalFloat (NF4) for extreme memory savings.
*   **NF4 Logic:** A data type specifically designed for weights following a zero-centered normal distribution. It provides higher resolution for the most common weight values.
*   **Double Quantization:** Quantizing the quantization scales themselves (from 32-bit to 8-bit), saving 0.37 bits per parameter.
*   **Paged Optimizers:** Utilizing Unified Memory to offload AdamW optimizer states to CPU RAM when GPU VRAM is saturated (e.g., during long sequence training).

### 2.3 Implementation Protocol (bitsandbytes)
```python
from transformers import BitsAndBytesConfig

# Mandatory QLoRA Configuration 
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4", # Information-theoretically optimal
    bnb_4bit_compute_dtype=torch.bfloat16 # Standard for H100/A100
)
```

---

## 3. High-Throughput Inference (vLLM & PagedAttention)
Operating LLMs at scale by solving the memory fragmentation problem.

### 3.1 PagedAttention Algorithm
*   **KV-Cache Management:** Conventional inference allocates a massive contiguous block for the Key-Value (KV) cache, leading to 60-80% waste (internal/external fragmentation).
*   **The OS Approach:** PagedAttention treats GPU VRAM like virtual memory. It divides the KV-cache into "Physical Blocks" and maintains a "Block Table" for each request.
*   **Copy-on-Write (CoW):** When sampling multiple paths (e.g., beam search), identical prefixes are shared across requests. Blocks are only copied when individual paths diverge.

### 3.2 SOTA Inference Kernels (FlashAttention-3)
*   **Hardware Acceleration:** FlashAttention-3 utilizes H100 GPU features like TMA (Tensor Memory Accelerator) and L2-cache resident kernels.
*   **Performance:** Achieving 75% of peak FP16 performance on H100, enabling ultra-long context windows (1M+ tokens) with linear scaling overhead.

---

## 4. Model Evaluation & Lifecycle (LLMOps 2025)
Standardizing the metrics and observability for production AI.

### 4.1 Quantitative Metrics
*   **Perplexity (PPL):** Measures how well the model predicts the test set.
*   **MMLU / GSM8K:** Benchmarking general knowledge and mathematical reasoning.
*   **MT-Bench:** Evaluating multi-turn conversational capability using LLM-as-a-Judge.

### 4.2 Observability Tools
*   **Weights & Biases (W&B):** Mandatory log of loss, hyperparams, and hardware thermals.
*   **LangSmith:** Distributed tracing for RAG and agentic programs; identifying "hallucination nodes" in complex graphs.
*   **Arize Phoenix:** Embedding-based drift detection to identify when data maps diverge from training distributions.

---

## 5. Deployment & Quantization Formats
*   **GGUF (Llama.cpp):** The standard for CPU-accelerated and Apple Silicon inference.
*   **EXL2 (ExLlamaV2):** Optimized for multi-GPU NVIDIA inference with granular bit-rate settings (e.g., 4.65 bpw).
*   **AWQ (Activation-aware Weight Quantization):** Minimizing accuracy loss by preserving 1% of the most "important" weights in FP16 while quantizing the rest to 4-bit.

---

## 6. Training Paradigms
*   **DPO (Direct Preference Optimization):** A simpler, more stable alternative to RLHF (Reinforcement Learning from Human Feedback) that optimizes the model directly on triplet data (Prompt, Better Answer, Worse Answer).
*   **ORPO (Odds Ratio Preference Optimization):** Combining SFT (Supervised Fine-Tuning) and Preference Alignment in a single stage.

---

## 7. Mathematical Appendix: NF4 Derivation
1.  **Block-wise Stats:** Calculate the absolute max of blocks (size 64).
2.  **Mapping Function:** Applying the inverse CDF of the normal distribution to determine 16 discrete levels.
3.  **Quantization Constant:** $q_i = \text{sign}(w_i) \cdot \lfloor \text{NF4\_Map}(|w_i| / \text{abs\_max}) \rceil$.

---

## 8. Benchmarks & Scaling Laws
*   **Compute-Optimal (Chinchilla):** Training for 20-30 tokens per parameter is the 2025 baseline for "well-trained" models.
*   **Throughput (Tokens/sec):** Target > 100 t/s per user on V100/A100 hardware for real-time responsiveness.

---
[Back to README](../../README.md)

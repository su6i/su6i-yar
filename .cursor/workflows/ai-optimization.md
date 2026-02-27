---
description: Protocol for AI Model Routing, Fallback logic, and Quota Management.
---

# AI Model Optimization Workflow

[Back to README](../../README.md)

## 1. Smart Routing Strategy (Architect vs Executor)
**Concept:** Use the "Best Model" to plan and the "Fast Model" to build.

### A. The Architect Protocol (Strongest Model)
**Role:** Planning, Auditing, Prompt Engineering.
**Model:** **Dynamic - Highest Available Priority.**
*   The "Architect" is NOT a specific model (e.g., DeepSeek).
*   It is whichever model is ranked **#1** in `config.yaml` that also has a valid API Key in `.env`.
*   *Example:* If `Claude Opus` is #1 and `Gemini Pro` is #2, and user has keys for both, `Claude Opus` is the Architect.
**Triggers:**
1.  **New Project:** Architect MUST generate the entire project structure and create detailed **Task Prompts** for lighter agents.
2.  **Existing Project:** Architect MUST audit the codebase first. If structure is poor, it refactors it. Then, it generates **Task Prompts** for the next steps.

### B. The Executor Protocol (Cost-Effective)
**Role:** Implementation, Writing Code, Generating Docs.
**Model:** `Gemini Flash Lite` or `Flash`.
**Rule:** Executors MUST strictly follow the **Task Prompts** created by the Architect. They do NOT make high-level decisions.

### C. Task Prompt Storage
**Action:** The Architect saves instructions in:
- `.cursor/instructions/` (e.g., `01_scaffold.md`, `02_auth_module.md`).
- **File Format:** Clear, step-by-step prompts optimized for lighter models.

### D. Model Selection Logic (How to find the Architect)
**1. API Mode (Background/Automated):**
*   **Logic:** Deterministic Fallback.
*   **Algorithm:**
    ```python
    def get_architect_model():
        priority_list = config.yaml['models']
        for model in priority_list:
            if os.getenv(model.required_env_key): # Check if Key exists in .env
                return model # Found the strongest ENABLED model
        raise Error("No API Keys found for Architect models!")
    ```

**2. Chat Mode (Interactive/IDE):**
*   **Logic:** Dynamic Discovery.
*   **Algorithm:**
    *   **Step 1:** App queries the Provider's API (e.g., `list_models()`) to see *what is actually supported*.
    *   **Step 2:** Compare supported models against the `config.yaml` priority list.
    *   **Step 3:** Select the highest-ranked model that "Reasoning" or "Pro" capabilities.
    *   **Top-Down Rule:** If multiple Pro models exist (e.g., Gemini 3 Pro vs Claude Opus), the one listed higher in `config.yaml` WINS.

### E. Configuration UX Rules
**1. `.env` Sorting:**
When generating `.env.example` or prompting the user, you MUST order keys by Priority:
1.  Architect Models (Most Expensive/Capable) - TOP
2.  Executor Models (Balance)
3.  Fallback/Local Models - BOTTOM
*This helps the user understand the hierarchy.*

### F. Chat Mode Configuration Strategy (Hybrid)
Since available models vary by user/region, we use a **"Seed & Sort"** approach:

1.  **Seed (Expert Defaults):** The project ships with a `config.default.yaml` containing the **ideal** priority list (as defined by us developers).
2.  **Auto-Discovery (First Run):**
    *   App fetches available models via API.
    *   It generates a local `config.yaml` by taking the Default list and **filtering out** unavailable models, while preserving the expert order.
3.  **Manual Override:** The user can edit their local `config.yaml` to reorder models (e.g., move `Claude` above `Gemini`), and the "Architect" logic will respect this new user-defined order.

## 2. Prompt Engineering & Storage Standard
**Rule:** Prompts are Code. Treat them as such.
1.  **Storage:** ALL prompts must be stored in the `prompts/` directory.
    *   `prompts/system_architect.txt`
    *   `prompts/task_linkedin_post.txt`
    *   `prompts/gen_project_logo.txt`
2.  **Format:** Use a structured, modular format (Role, Task, Constraints, Output Format).
3.  **No Hardcoding:** Never bury a prompt inside a Python string. Load it from the file.

## 3. Fallback Hierarchy (Config.yaml)
**Action:** Implement this exact priority queue in `config.yaml`.

| Priority | Model (Text) | Type | Role |
| :--- | :--- | :--- | :--- |
| 1 | `gemini-3-flash` | Text | Balance |
| 2 | `gemini-2.5-flash` | Text | Standard |
| 3 | `gemini-2.5-flash-lite` | Text | Economy |
| 4 | `deepseek-v3` | Text | Complex |
| 5 | `gemma-3-27b` | Local | Offline |
| ... | `gemma-3-1b` | Local | Last Resort |

| Priority | Model (Audio) | Type | Role |
| :--- | :--- | :--- | :--- |
| 1 | `gemini-2.5-flash-tts` | Audio | Quality |
| 2 | `gemini-2.5-flash-native` | Audio | Live |
| 3 | `microsoft-edge-tts` | Audio | Free Fallback |

## 3. Quota Management (Circuit Breaker)
**Logic:**
- **On 429 Error:** Mark model as `EXHAUSTED` in `~/.app/state.json`.
- **Action:** Skip this model for the rest of the day (24h).
- **Next Day:** Reset `EXHAUSTED` status on first run.

## 4. Safety
- **Rule:** NEVER send Text tasks to Audio models.
- **Check:** `if model.type == 'audio' and task.type == 'text': raise Error`.

---
[Back to README](../../README.md)

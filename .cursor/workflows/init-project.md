---
description: Initialize a new professional project following the Agent Protocol standards.
---

# Project Initialization Workflow

[Back to README](../../README.md)

> **💡 Automation Tip:** Setup the global alias `init-project` (instructions in `bin/scaffold.sh`) and simply run `init-project` in your new empty folder.

1.  **Scaffold Directory Structure**
    - Create `src/`, `tests/`, `docs/`, `assets/`, `scripts/`.
    - Create `.cursor/workflows/` (Standard Rules Location).
    - **Storage Policy:** DO NOT create storage folders in root. Code must use `~/.project_name/` for persistent data/logs.
    - Ensure root is strictly clean (max 5-7 core files).

2.  **Setup Logic & Config**
    - Initialize `uv init`.
    - Create `main.py` (Unified Entry Point).
    - Create `config.yaml` (Insert the AI Model Fallback table).
    - Create `.env.example` (Add keys for Gemini, Microsoft TTS, etc.).

3.  **Create Installation Script**
    - Create `install.sh`.
    - implementation: Add OS detection, `ffmpeg` check, `uv venv` creation, and interactive `.env` setup prompt.
    - Make it executable: `chmod +x install.sh`.

4.  **Generate Documentation Artifacts**
    - **Logo Generation (Mandatory Protocol):**
        1.  Read `.cursor/prompts/template_project_logo.txt` from the Constitution.
        2.  Create `.cursor/prompts/gen_[project]_logo.txt` in the new project.
        3.  Fill in the `[INSERT THEME]`, `[COLORS]`, etc., with extreme detail.
        4.  Use this prompt to generate the SVG/Image. save to `assets/project_logo.svg`.
    - **README.md (Mandatory Protocol):**
        1.  Read `.cursor/prompts/template_readme.txt`.
        2.  Create/Fill `.cursor/prompts/gen_readme.txt` with project specifics.
        3.  Generate `README.md` using the "Standard Header" + content from the prompt.
    - **docs/TECHNICAL.md (Mandatory Protocol):**
        1.  Read `.cursor/prompts/template_technical.txt`.
        2.  Create/Fill `.cursor/prompts/gen_technical.txt`.
        3.  Generate `docs/TECHNICAL.md` focusing on "Zero-to-Hero" extension guide.

5.  **Final Verification**
    - Run `./install.sh` to test the onboarding flow.
    - Check if `README.md` links correctly to `TECHNICAL.md`.

---
[Back to README](../../README.md)

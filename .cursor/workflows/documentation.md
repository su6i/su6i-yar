---
description: Workflow for creating World-Class Documentation (README & Technical).
---

# Documentation Standard Workflow

[Back to README](../../README.md)

## 1. Visual Identity (The "Wow" Factor)
**Action:** Apply this HTML header to `README.md`. Center everything.

```html
<div align="center">
  <img src="assets/project_logo.svg" width="350" alt="Logo">
  <h1>Project Name 🚀</h1>
  <!-- Custom LinkedIn Badge -->
  <!-- ACTION: Replace 'su6i' with your own ID and 'linkedin_su6i.svg' with your own asset -->
  <p>
    <a href="https://github.com/su6i/agent-constitution/releases"><img src="https://img.shields.io/badge/Version-1.0.0-blue.svg" alt="Version"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
    <a href="docs/TECHNICAL.md"><img src="https://img.shields.io/badge/Docs-Technical-orange.svg" alt="Docs"></a>
    <a href="https://linkedin.com/in/su6i"><img src="assets/linkedin_su6i.svg" height="20" alt="LinkedIn"></a>
  </p>
  <br><strong>Slogan</strong>
</div>
```

## 2. Structure: The Two-User Rule
**Action:** Split docs into two files.

### A. `README.md` (for Users)
- **Why:** Problem/Solution.
- **Install:** One-line command.
- **Usage:** Demo screenshots/GIFs + Command Table.
- **Tone:** Simple, emoji-friendly.

### B. `docs/TECHNICAL.md` (for Developers)
- **Architecture:** Tree view + Logic explanation.
- **Real-World Extension Guide (Zero-to-Hero):**
    - **Step 1:** Create Script/Component.
    - **Step 2:** Logic Implementation.
    - **Step 3:** Registration/Export.
    - **Step 4:** Usage Example.

## 3. Maintenance
**Trigger:** After ANY code change.
**Action:**
1. Update `usage` examples if flags changed.
2. Update `tree` if files moved.
3. Update `requirements.txt` / `pyproject.toml`.
4. **Preserve Comments:** Do NOT delete `<!-- ACTION -->` or `<!-- NOTE -->` comments unless you have performed the action. They are vital for future maintainers.

## 4. The "Job Well Done" Protocol
**Trigger:** User says "Good job", "Damet garm", "Nice", or any positive feedback.
**Action (Mandatory):**
1.  **Auto-Docs:** IMMEDIATELY update all relevant documentation (`README.md`, `TECHNICAL.md`, `task.md`, `requirements.txt`, `pyproject.toml`) to reflect the latest changes.
2.  **Auto-Commit:** Commit these documentation changes along with the code.
3.  **Finish:** Only then consider the task truly complete.

---
[Back to README](../../README.md)

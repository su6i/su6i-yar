---
description: Standards for Testing, Security, and Version Control (Git).
---

# Quality Assurance & DevOps Workflow

[Back to README](../../README.md)

## 1. Testing Protocol (Zero Bugs)
**Rule:** No code is "Done" until it has tests.
- **Framework:** Use `pytest` for Python.
- **Coverage:** Critical paths (Auth, Payments, Data Handling) require 90%+ coverage.
- **Mocking:** Use `unittest.mock` for external APIs. NEVER hit real APIs during tests.

## 2. Version Control (Conventional Commits)
**Action:** Agents must write semantic commit messages.
- **Format:** `<type>(<scope>): <subject>`
- **Types:**
    - `feat`: New feature
    - `fix`: Bug fix
    - `docs`: Documentation only
    - `refactor`: Code change that neither fixes a bug nor adds a feature
    - `test`: Adding missing tests
    - `chore`: Maintenance (e.g., updating requirements)
- **Example:** `feat(auth): add google oauth login support`
- **Clean History:** If a documentation update was missed for a just-committed feature, use `git commit --amend` to include it. Do NOT create a new commit for such corrections.

## 3. Security Audit
**Trigger:** Before every commit.
**Check:**
1.  **Secrets:** Scan for hardcoded API keys or passwords. (Move to `.env`).
2.  **Deps:** Check `requirements.txt` for known vulnerable versions.
3.  **Input:** Validation logic exists for all user inputs.

## 4. Release Strategy (Semantic Versioning)
- **Major (X.0.0):** Breaking changes.
- **Minor (0.X.0):** New features (backward compatible).
- **Patch (0.0.X):** Bug fixes.
- **Action:** Update `VERSION` file and `README.md` badge on every release.

## 5. Truth & Verification Protocol (Anti-Hallucination)
**Rule:** You must NEVER claim a task is "Done" without objective proof.
1.  **File Operations:** If you create/move files, you MUST run `ls -R` or `cat` afterwards to prove they exist. "I checked it" is NOT an acceptable response. Show the output.
2.  **Deletion Safety:** You are FORBIDDEN from deleting any file without explicit user approval.
    *   *Exception:* Temporary files you just created in the current session.
3.  **Honesty:** If a tool fails (e.g., `cp` returns nothing), do NOT assume success. investigate or fail loudly.

## 6. File Safety Protocol (Collision Avoidance)
**Rule:** You are a guest in this filesystem. Do not destroy what you did not create.
1.  **Check Before Write:** Before creating ANY file (e.g., `gen_logo.txt`), check if it already exists.
2.  **Conflict Resolution:**
    *   **If file exists:** DO NOT OVERWRITE.
    *   **Action:** Stop and ask the user, OR append a timestamp (e.g., `gen_logo_v2.txt`).
    *   *Exception:* You may overwrite files explicitly flagged as "Artifacts" that you own (like `README.md` during a refresh), but ONLY if the user asked for a refresh.
3.  **Safe Deletion:** `rm` is a dangerous weapon. Never use it on user-generated files.
4.  **Workspace Discipline (.storage):**
    *   **Rule:** NEVER dump data/temp files in the project root.
    *   **Action:**
        *   **Datasets/Models:** Store in `.storage/data/`.
        *   **Logs/Temp Scripts:** Store in `.storage/temp/`.
    *   **Reason:** This folder is strictly git-ignored. Keep the repo clean.

## 7. Engineering Excellence (Research First)
**Rule:** Stop and Think. Do not implement based on assumptions.
1.  **Search Best Practices:** Before writing complex logic (like Table Alignment, Zsh Completion), search for standard, scientific methods (e.g., Unicode Standards, Official Specs).
2.  **No Trial & Error:** "Guessing" flags or magic numbers is forbidden. If you don't know, find the documentation or a proven algorithm first.
3.  **Standard Libraries over Hacks:** Always prefer Python's standard library (e.g., `unicodedata`) or robust CLI tools over manual parsing/regex hacks.

---
[Back to README](../../README.md)

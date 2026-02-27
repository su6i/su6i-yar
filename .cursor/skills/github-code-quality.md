---
name: github-code-quality
description: GitHub Code Quality Technical Encyclopedia: Automated Linting, Pre-commit Hooks, Code Review Standards, and Cursor Rule Orchestration.
---

# Skill: GitHub Code Quality (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design and orchestration of automated code quality systems within the GitHub ecosystem in the 2025 ecosystem. This document defines the standards for linting, pre-commit hooks, automated code reviews, and the integration of Cursor-specific `.cursorrules` for project-wide consistency.

---

## 1. Automated Linting & Formatting Strategy
Standardizing on the most performant and strict toolchains for Python and JS/TS.

### 1.1 Ruff & Biome Integration
*   **Python (Ruff):** Mandatory use of Ruff for both linting and formatting, replacing Flake8, Black, and Isort with a single Rust-powered engine.
*   **JS/TS (Biome):** Utilizing Biome as the high-speed alternative to ESLint and Prettier for cohesive web-development environments.
*   **Configuration:** Storing all rules within `pyproject.toml` or `biome.json` for centralized management.

### 1.2 Pre-commit Hook Standards
*   **Logic:** Utilizing the `pre-commit` framework to run lints LOCALLY before any code can be committed.
*   **Standard Hooks:** `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, and target-language specific lints (e.g., `ruff-pre-commit`).

---

## 2. Automated Code Review (GitHub Actions)
Implementing "Gated" PRs that refuse merges unless high-quality standards are met.

### 2.1 The "Review-as-Code" Protocol
*   **Static Analysis:** Mandatory use of specialized GitHub Actions (e.g., `reviewdog`, `sonarcloud`) to post linting errors directly as comments on the PR diff.
*   **Test Coverage Gating:** Utilizing `pytest-cov` and `codecov` to automatically fail a PR if the total coverage drops by more than $1\%$.

### 2.2 PR Template Excellence
Mandatory standard for the `PULL_REQUEST_TEMPLATE.md`, requiring sections for:
- [ ] Description of Changes
- [ ] Related Issue #
- [ ] Breaking Change (Yes/No)
- [ ] Checklist for Linting / Testing / Documentation

---

## 3. Cursor Rules & Project Orchestration
Utilizing `.cursorrules` (and `.mdc` files in 2025) to provide project-specific "AI Intelligence."

### 3.1 `.cursorrules` Standard Architecture
*   **Context Injection:** Defining "Global Rules" for project structure (e.g., `src/` layout) and "Specific Rules" for complex modules.
*   **Naming Conventions:** Enforcing strict PascalCase for classes and snake_case for functions through AI-guided correction.

### 3.2 Automated Rule Enforcement
Utilizing a custom script to verify that every file in the project adheres to the `agent-constitution` and project-specific `.cursor/rules`.

---

## 4. Technical Appendix: Code Quality Reference
| Tool / Concept | Technical Purpose | Standard |
| :--- | :--- | :--- |
| **Ruff** | Python Linting/Formatting | Mandatory |
| **pre-commit** | Git hook orchestration | Local |
| **CodeQL** | Semantic security analysis | P0 (Critical) |
| **Type-Checking**| mypy / pyright | Strict |

---

## 5. Industrial Case Study: The "Zero-Technical-Debt" Repo
**Objective:** maintaining a massive codebase with 100% linter compliance.
1.  **Initialization:** Configuring a strict `pyproject.toml` with 500+ Ruff rules enabled.
2.  **Enforcement:** A GitHub Action runs on every push, blocking all merges that have even 1 warning.
3.  **Refactoring:** Using `ruff --fix` in a weekly cron job to automatically apply new code standards across the entire repository.
4.  **Verification:** Automated "Debt Audit" shows 0 violations across 100,000 LOC.

---

## 6. Glossary of Code Quality Terms
*   **Linter:** A tool that analyzes source code to flag programming errors, bugs, stylistic errors, and suspicious constructs.
*   **Technical Debt:** The implied cost of additional rework caused by choosing an easy (but limited) solution now instead of using a better approach that would take longer.
*   **Cyclomatic Complexity:** A quantitative measure of the number of linearly independent paths through a program's source code.
*   **Dry Run:** Executing a command without actually applying any changes (e.g., `ruff check`).

---

## 7. Mathematical Foundations: Complexity Math
*   **Logic:** Calculating the "Maintainability Index" of a file.
*   **Formula:** $MI = \max(0, (171 - 5.2 \cdot \ln(V) - 0.23 \cdot G - 16.2 \cdot \ln(L)) \cdot 100 / 171)$, where $V$ is Halstead Volume, $G$ is Cyclomatic Complexity, and $L$ is Lines of Code.
*   **Constraint:** In 2025, Moltbot targets an $MI > 80$ for all production-critical modules.

---

## 8. Troubleshooting & Performance Verification
*   **Linter Conflict:** Two tools fighting over formatting (e.g., Black vs Isort). *Fix: Consolidate to Ruff.*
*   **CI Bottleneck:** Linting taking > 5 minutes. *Fix: Use incremental linting or move the heaviest checks to a background "Security" job.*

---

## 9. Appendix: Future "AI-Corrective" Hooks
*   **Self-Healing PRs:** A GitHub Action that doesn't just comment on an error but actually pushes a "Fix" commit to the PR branch automatically using a local LLM or specialized CLI.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Linting Latency:** Target < 1s for 10,000 LOC using Ruff.
*   **Code Coverage:** Minimum 90% for core logic; 100% for financial/security modules.

---
[Back to README](../../README.md)

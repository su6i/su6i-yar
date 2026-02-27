---
name: python-github-setup
description: Python GitHub Setup Technical Encyclopedia: CI/CD Workflows, Secret Management (OIDC), Branch Protection, and Template Orchestration.
---

# Skill: Python GitHub Setup (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design and orchestration of Python-centric GitHub repositories in the 2025 ecosystem. This document defines the standards for CI/CD pipeline engineering, OIDC-based secret management, and deterministic repository state management.

---

## 1. CI/CD Pipeline Engineering (GitHub Actions)
Standardizing on YAML-based workflows for automated testing, linting, and deployment.

### 1.1 The "Gold Standard" Workflow Template
*   **Triggers:** Mandatory use of `pull_request` and `push` to `main` with path-awareness (e.g., `paths: ["src/**", "tests/**"]`).
*   **Job Concurrency:** Using `concurrency` groups to cancel outdated runs, saving CI minutes.
*   **Environment Matrix:** Testing across multiple Python versions (3.12, 3.13) and OS targets (Ubuntu, macOS).

### 1.2 Implementation Protocol (`uv` + Actions)
```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
      - name: Install dependencies
        run: uv sync --frozen
      - name: Run Tests
        run: uv run pytest --cov=src --cov-report=xml
```

---

## 2. Advanced Security & Secret Management
Implementing "Zero-Trust" protocols for repository credentials.

### 2.1 OIDC (OpenID Connect) Standards
*   **Logic:** Eliminating long-lived GitHub Secrets for cloud deployments (AWS/GCP/PyPI).
*   **Protocol:** Utilizing short-lived JWT tokens provided by GitHub to authenticate directly with the target provider via `permissions: id-token: write`.

### 2.2 Branch Protection & Gated Merges
*   **The "Clean-Only" Standard:** Mandatory status checks (CI passing), required reviews (Min: 1), and "Require linear history" (Squash merge only).
*   **Security Scanning:** Mandatory integration of **CodeQL** and **Dependabot** for automated vulnerability detection and dependency updates.

---

## 3. Repository Templating & Orchestration
Ensuring consistency across multiple projects using standardized manifests.

### 3.1 Template Repository Protocols
*   **Standard Files:** `.gitignore`, `.editorconfig`, `pyproject.toml`, and `.github/ISSUE_TEMPLATE/`.
*   **PR Template Standards:** Mandatory sections for "Changes", "Testing Done", and "Documentation Updated".

---

## 4. Technical Appendix: GitHub Repository Reference
| Feature | Technical Purpose | Standard |
| :--- | :--- | :--- |
| **Environments** | Context-specific secrets/rules | Production/Staging |
| **Labels** | Automated triage | Semantic (Bug, Enh.) |
| **Discussions** | Community Q&A | Enabled (Large Libs)|
| **Workflows** | Composite actions | Dry logic |

---

## 5. Industrial Case Study: Automating a Multi-Package Mono-repo
**Objective:** managing 5 Python libraries in a single GitHub repository.
1.  **Workspaces:** Utilizing `uv` workspaces for local dependency resolution.
2.  **Selective CI:** Using `on.push.paths` to only run tests for the package that changed.
3.  **Cross-Library Versioning:** Utilizing `semantic-release` or similar tools to automatically bump versions and generate changelogs across all 5 packages.
4.  **Security Gating:** Centralized Dependabot configuration for the entire mono-repo.

---

## 6. Glossary of GitHub Setup Terms
*   **Action:** A custom application for the GitHub Actions platform that performs a complex but frequently repeated task.
*   **OIDC (OpenID Connect):** An identity layer on top of the OAuth 2.0 protocol.
*   **Fork:** A personal copy of another user's repository that lives on your account.
*   **Workflow:** A configurable automated process that will run one or more jobs.

---

## 7. Mathematical Foundations: Matrix Strategy Optimization
*   **Logic:** Calculating the cost vs. coverage of a CI matrix.
*   **Formula:** $\text{Total Cost} = \text{JobTime} \cdot \sum (\text{OS} \cdot \text{PythonVersion} \cdot \text{ParamCombination})$.
*   **Optimization:** In 2025, Moltbot prunes redundant combinations (e.g., testing 3.12 on macOS if it already passed on Ubuntu) to minimize latency.

---

## 8. Troubleshooting & Performance Verification
*   **Flaky CI:** Tests failing inconsistently. *Fix: Use "Retry" logic or isolate network dependencies via `pytest-mock`.*
*   **Secret Leakage:** Detecting plaintext secrets in workflow logs. *Fix: Immediate token revocation and configuration of "Secret Scanning" in GitHub Settings.*

---

## 9. Appendix: Future "Autonomous Repo" Trends
*   **PR Auto-Fixing:** Actions that automatically run `ruff format` and commit the changes back to the PR if the linting check fails.

---

## 10. Benchmarks & Performance Standards (2025)
*   **CI Execution Time:** Target < 5m for standard test suites.
*   **Security Compliance:** 100% resolution rate for "Critical" Dependabot alerts within 24 hours.

---
[Back to README](../../README.md)

---
name: howto-documentation
description: How-To Documentation Technical Encyclopedia: Diátaxis Framework, Semantic Markdown, Automated Testing, and Style-as-Code.
---

# Skill: How-To Documentation (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design, architecture, and maintenance of high-fidelity technical documentation in the 2025 ecosystem. This document defines the standards for the Diátaxis framework, Semantic Markdown implementation, and automated documentation verification.

---

## 1. Information Architecture (Diátaxis Framework)
Standardizing on the 4-quadrant system for logical, user-centric documentation.

### 1.1 The 4-Quadrant Architecture
*   **Tutorials (Learning-oriented):** Guided lessons to help a user learn a new concept.
*   **How-to Guides (Goal-oriented):** Practical, step-by-step instructions for a specific task.
*   **References (Information-oriented):** Technical descriptions of APIs, parameters, and architectures.
*   **Explanations (Understanding-oriented):** Deep-dives into the "Why" and "How" of the system.

### 1.2 Contextual Mapping Protocol
Ensuring every piece of documentation serves ONE of the four quadrants to prevent "Context Mixing" that confuses readers.

---

## 2. Semantic Markdown & Metadata Standards
Utilizing Markdown as 100% structured data for automated processing.

### 2.1 YAML Frontmatter Standards
*   **Logic:** Every documentation file MUST contain a standardized YAML block for search indexing and categorization.
*   **Metadata Fields:** `description`, `last_modified`, `status` (Draft/Stable), and `audience` (Beginner/Expert).

### 2.2 Alert & Callout Standards
Utilizing GitHub-style alerts (`> [!NOTE]`, `> [!WARNING]`, `> [!IMPORTANT]`) to provide hierarchical critical information without breaking the reading flow.

---

## 3. Automated Documentation Verification (Doc-as-Code)
Treating documentation with the same rigor as production software.

### 3.1 Link & Spell Verification
*   **Protocol:** Mandatory automated checking for broken local and external links on every commit.
*   **Standards:** Utilizing `markdownlint` and specialized CI agents to enforce style consistency.

### 3.2 Snippets-to-Code Injection
*   **Logic:** Ensuring code snippets in documentation are ALWAYS correct by pulling them directly from tested source files using `include` macros or build-time injection.

---

## 4. Technical Appendix: Documentation reference
| Type | Technical Goal | Content Target |
| :--- | :--- | :--- |
| **Tutorial** | Zero-to-One mastery | Example-rich |
| **How-To** | Task completion | Concise |
| **Reference** | API Completeness | Parameter-rich |
| **Explained** | Mental Model stability | Narrative-rich |

---

## 5. Industrial Case Study: Documentation for a Global Open Source Project
**Objective:** managing 1,000+ files of documentation across 5 languages.
1.  **Architecture:** Utilizing `MkDocs` with the `Material` theme for high-performance localized serving.
2.  **Orchestration:** Each language is managed in a subfolder (`docs/fa/`, `docs/fr/`).
3.  **Automation:** A GitHub Action verifies that all 5 languages have matched structural nodes.
4.  **Verification:** Analytics show > 90% search relevancy for technical queries.

---

## 6. Glossary of Documentation Terms
*   **Diátaxis:** A systematic approach to technical documentation.
*   **Semantic Markdown:** Markdown that is structured for machine-readability.
*   **Frontmatter:** The initial block of metadata in a file.
*   **Callout:** A visual element used to highlight specific information.

---

## 7. Mathematical Foundations: The Readability Score
*   **Formula (Flesch-Kincaid):** $206.835 - 1.015 \cdot (\text{total words} / \text{total sentences}) - 84.6 \cdot (\text{total syllables} / \text{total words})$.
*   **Constraint:** In 2025, Moltbot targets a score of > 60 (Standard English) for all "Tutorial" and "How-To" quadrants.

---

## 8. Troubleshooting & Performance Verification
*   **Information Rot:** Documentation becomes outdated. *Fix: Mandatory `last_modified` metadata and automated "Stale" flags on files not updated in 90 days.*
*   **Navigation Deadlocks:** User cannot find the next logical step. *Fix: Mandatory "Next Steps" and "Back to README" links on every file.*

---

## 9. Appendix: Future "Adaptive Documentation"
*   **Persona-Driven Rendering:** Utilizing LLMs to re-render the same technical documentation for different audience levels (e.g., "Explain it to me like I'm 5" vs "Give me the raw API specs") dynamically.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Index Speed:** Target < 100ms for full-text search across 1,000 documents.
*   **Accuracy:** 100% agreement between documented API parameters and actual source code.

---
[Back to README](../../README.md)

---
name: storyteller-clil
description: CLIL Educational Screenwriting Technical Encyclopedia: 4Cs Framework, Leitner Integration, Vocabulary Tracking, and Implicit Pedagogy.
---

# Skill: CLIL Educational Screenwriting (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the generation of educational scripts utilizing the CLIL (Content and Language Integrated Learning) framework and Leitner Spaced Repetition systems. This document defines the standards for content-first pedagogy, vocabulary frequency tracking, and implicit language instruction.

---

## 1. The CLIL Framework (4Cs Architecture)
Standardizing the structure of educational content to integrate language learning with technical subject matter.

### 1.1 The 4Cs Protocol
*   **Content:** The technical subject matter (e.g., "Python Data Structures").
*   **Cognition:** The cognitive demand (e.g., "Analyze", "Evaluate", "Synthesize").
*   **Communication:** The language required to express the content (Target Vocabulary).
*   **Culture:** The professional context or "community of practice" (e.g., "Open Source contributor culture").

### 1.2 Cognitive Scaffolding Standard
Using "Low-to-High" Bloom's Taxonomy progression within a single 5-minute script.

---

## 2. Leitner System & Vocabulary Integration
Systematically tracking and reinforcing user knowledge through spaced repetition intervals.

### 2.1 Leitner Logic Protocols
*   **Box Levels (0-5):** New terms start in Box 0 and move up upon successful recall.
*   **Decay Math:** Calculating the "Forgetting Curve" to determine which terms must be re-injected into the next script.
*   **Implicit Reinforcement:** Placing target vocabulary in natural technical contexts rather than explicit "translation blocks."

### 2.2 Tracking Implementation Protocol
```sql
-- 2.2.1 Vocabulary State Table
CREATE TABLE vocab_state (
    term TEXT PRIMARY KEY,
    box_level INTEGER DEFAULT 0,
    last_seen DATETIME,
    next_review DATETIME,
    mastery_score FLOAT
);
```

---

## 3. Technical Screenwriting Standards
Converting pedagogical goals into engaging video scripts.

### 3.1 Retention-Driven Pacing
*   **The Hook (0-15s):** Identifying the specific technical problem.
*   **The Concept (15s-2m):** Explaining the core logic using target language.
*   **The Demonstration (2m-4m):** Code examples with verbal "Shadowing" cues.
*   **The Recap (4m-5m):** Leitner reinforcement of core terms.

### 3.2 Multilingual Integration (2025)
Protocols for "Code-Switching" scripts (e.g., Persian explanation of English code) to leverage the user's native language for complex concept grounding.

---

## 4. Technical Appendix: CLIL & Leitner Reference
| Component | Pedagogical Purpose | Technical Standard |
| :--- | :--- | :--- |
| **Cognitive Load** | Balances information density | Managed via 4Cs |
| **Spaced Repet.** | Maximizes long-term retention | SQLite Logic |
| **Active Recall** | Forces user to "produce" language | Interactive Cues |
| **Implicit Learn.** | Natural language acquisition | Context-First |

---

## 5. Industrial Case Study: Language Learning for Coders
**Objective:** Teaching French through React Native tutorials.
1.  **Keyword Selection:** Identify 5 French keywords (e.g., `Composant`, `État`, `Rendu`).
2.  **Script Layering:** Use the keywords in the code commentary.
3.  **Dialogue Injection:** Narrator uses keywords as functional technical terms.
4.  **Verification:** User must choose the correct term during a "debug" sequence.

---

## 6. Glossary of CLIL & Screenwriting Terms
*   **Scaffolding:** Temporary support provided to help a learner master a new concept.
*   **Comprehensible Input (i+1):** Providing language slightly above the user's current level.
*   **BICS vs CALP:** Basic Interpersonal Communication vs. Cognitive Academic Language Proficiency.
*   **Timeline Architecture:** The technical layout of a script (Action, Dialog, Visuals).

---

## 7. Mathematical Foundations: The Ebbinghaus Forgetting Curve
*   **Formula:** $R = e^{-t/S}$ (where $R$ is memory retention, $t$ is time, and $S$ is strength of memory).
*   **Optimization:** Determining the ideal Leitner window to interrupt the decay just before the probability of recall drops below 80%.

---

## 8. Troubleshooting & Performance Verification
*   **Cognitive Overload:** Script becomes too technical or too language-heavy. *Fix: Adjust the "4Cs Balance" slider.*
*   **Vocabulary Drift:** Using terms the user hasn't seen in 30+ days. *Fix: Mandatory Leitner Box-0 re-injection.*

---

## 9. Appendix: Future "Storyteller" Pedagogy
*   **Dynamic Difficulty Adjustment (DDA):** Shortening or lengthening segments based on user performance data in real-time.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Retention Rate:** Target > 70% recall of Box-1 terms after 3 scripts.
*   **Script Completion:** 100% alignment with the target Vocabulary Manifest.

---
[Back to README](../../README.md)

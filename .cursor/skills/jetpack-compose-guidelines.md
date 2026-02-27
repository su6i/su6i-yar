---
name: jetpack-compose-guidelines
description: Jetpack Compose Technical Encyclopedia: Unidirectional Data Flow (UDF), Stability Math, 'derivedStateOf' Optimization, and Kotlin Multiplatform integration.
---

# Skill: Jetpack Compose Guidelines (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design and construction of modern Android (and Multiplatform) user interfaces using Jetpack Compose in the 2025 ecosystem. This document defines the standards for Unidirectional Data Flow (UDF), Recomposition Stability math, and high-performance state management using `derivedStateOf`.

---

## 1. Unidirectional Data Flow (UDF) & State
Standardizing on the most predictable and testable UI architecture.

### 1.1 The UDF Cycle
*   **State flows Down:** The ViewModel (or parent) passes an immutable State object to the Composable.
*   **Events flow Up:** The Composable triggers callback events (e.g., `onItemClick`) that the ViewModel handles to update the State.
*   **Logic:** Ensuring that a Composable's primary purpose is to "Act as a function of its current state" without side-effects.

### 1.2 Implementation Protocol (Stateless Composable)
```kotlin
# 1.2.1 Mandatory State Hoisting Standard
@Composable
def MyButton(
    label: String,
    onClick: () -> Unit # 1.2.2 Event Callback
) {
    Button(onClick = onClick) {
        Text(text = label)
    }
}
```

---

## 2. Recomposition Stability & Performance Math
Minimizing unnecessary UI redraws through rigorous state isolation.

### 2.1 Stability Annotations
*   **`@Stable`:** A contract with the compiler that the object will notify when it changes.
*   **`@Immutable`:** A contract that the object WILL NEVER change, allowing the compiler to skip recomposition entirely if the reference is the same.
*   **The "Unstable Lists" Problem:** Standard Kotlin `List` is considered unstable by Compose. *Fix: Use `ImmutableList` (from kotlinx.collections.immutable) or wrap in a `@Stable` class.*

### 2.2 `derivedStateOf` Optimization
Utilizing `derivedStateOf` to prevent recompositions when a state changes frequently (e.g., a scroll position) but only triggers a change when a specific threshold is met.

---

## 3. Multi-modal Aesthetics & Motion
Creating premium Android experiences with 60fps animations.

### 3.1 Advanced Transition Orchestration
*   **`AnimatedVisibility`:** Standard for entry/exit animations.
*   **`updateTransition`:** For complex, multi-state transitions (e.g., expanding a card while changing colors).

### 3.2 Look & Feel Protocols
Mandatory use of Material Design 3 (M3) color-schemes and "Dynamic Color" (Material You) integration to match the user's system theme.

---

## 4. Technical Appendix: Jetpack Compose Reference
| Phase | Technical Tool | Purpose |
| :--- | :--- | :--- |
| **State** | `rememberSaveable` | Persistence |
| **Logic** | `LaunchedEffect` | Side-effects |
| **Layout** | `SubcomposeLayout` | Custom sizing |
| **Verify** | `Compose-Metrics` | Perf. Audit |

---

## 5. Industrial Case Study: A High-Performance Media Feed
**Objective:** Building a smooth-scrolling 4K video feed.
1.  **Architecture:** UDF with a `Paging3` mediated flow.
2.  **Stability:** Each feed item is wrapped in an `@Immutable` model.
3.  **Optimization:** Using `Modifier.graphicsLayer` for translations to bypass the layout phase.
4.  **Verification:** Automated "Jank-test" (Macrobenchmark) shows 0% skipped frames on Pixel 9 hardware.

---

## 6. Glossary of Compose Terms
*   **Composable:** A function that describes a part of the UI.
*   **Recomposition:** Re-running a Composable function when its inputs change.
*   **Slot API:** A Composable that takes another Composable as a parameter.
*   **Measure / Layout / Draw:** The three phases of the Compose rendering pipeline.

---

## 7. Mathematical Foundations: The Constraint Solver
*   **Logic:** Compose calculates the size of children before deciding the parent's size.
*   **Complexity:** Standard Box/Row/Column are $O(N)$ for measurement. Avoid deep nesting to prevent $O(N^2)$ layout spikes.

---

## 8. Troubleshooting & Performance Verification
*   **Jittery Scrolling:** Occurs when recomposition is triggered on every pixel of scroll. *Fix: Use `derivedStateOf` or `graphicsLayer`.*
*   **Leaking Subscriptions:** `Flow` or `LiveData` not being cleaned up. *Fix: Use `collectAsStateWithLifecycle()`.*

---

## 9. Appendix: Future "KMP" (Kotlin Multiplatform)
*   **Compose Multiplatform:** Utilizing the same codebase to deploy high-performance UIs on Android, iOS, Desktop using the Skia/Skiko rendering engine.

---

## 10. Benchmarks & Performance Standards (2025)
*   **First Frame:** Target < 200ms on mid-range devices.
*   **Frame Stability:** 100% 60fps adherence in standard UI scenarios.

---
[Back to README](../../README.md)

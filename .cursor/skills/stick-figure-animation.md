---
name: stick-figure-animation
description: Stick Figure Animation Technical Encyclopedia: Frame-by-Frame Physics, Easing Curves, Blender 2D Rigging, and Combat Choreography.
---

# Skill: Stick Figure Animation (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the animation of stick-figure characters, focusing on kinetic physics, dynamic easing, and procedural choreography in the 2025 ecosystem. This document defines the standards for Verlet integration, Bezier-based easing, and efficient keyframe interpolation.

---

## 1. Frame-by-Frame Physics (Kinetic Foundations)
Moving beyond "Positional" animation to "Force-Based" motion.

### 1.1 Verlet Integration Logic
*   **The Algorithm:** Calculating the current position based on the previous position and current acceleration, ensuring that momentum is preserved across frames.
*   **Constraint Satisfaction:** Technical rules for stick segments (Bones) that maintain a constant length while the joints (Nodes) move freely.

### 1.2 Impact & Recoil Math
*   **Momentum Transfer:** $P = m \cdot v$. When a stick figure "hits" an object, the visual recoil must reflect the mass of the limb and the velocity of the impact.
*   **Frame Padding:** Intentionally adding 1-2 frames of "Impact Freeze" to emphasize power.

---

## 2. Advanced Easing & Bezier Curves
Standardizing the curvature of motion to ensure "Organic" yet "Technical" feel.

### 2.1 Easing Protocol Table
| Type | Technical Math | Aesthetic Goal |
| :--- | :--- | :--- |
| **Ease-In-Out** | Cubic Bezier $(0.42, 0, 0.58, 1)$ | Standard natural motion |
| **Elastic** | Damped Sinusoidal Oscillation | Vibrational recovery |
| **Bounce** | Absolute Value Parabola | Floor collision |
| **Step** | Quantized Floor Function | Robotic/Stop-motion |

### 2.2 Keyframe Compression Standards
*   **Logic:** Utilizing "Constant" interpolation for rapid combat poses and "Bezier" for slow, weight-bearing movements.

---

## 3. Blender 2D Rigging (The "Armature" Standard)
Utilizing 3D tools for high-precision 2D stick animation.

### 3.1 Skeleton Architecture
*   **Bone Hierarchy:** Standardizing the Root (Pelvis) -> Spine -> Neck -> Head chain.
*   **Inverse Kinematics (IK):** Mandatory for legs to ensure feet "stick" to the floor without sliding (Contact Point Stability).

### 3.2 Procedural Modifiers
*   **Noise Modifier:** Adding subtle "Hand-drawn" vibration to lines.
*   **Build Modifier:** For procedural "Growing" or "Drawing" of the character paths.

---

## 4. Technical Appendix: Stick Figure Reference
| Component | Primary Utility | Tech Standard |
| :--- | :--- | :--- |
| **Joint (Node)** | Pivot point for rotation | Circle (Vector) |
| **Limb (Edge)** | Length-invariant segment | Line (Stroke) |
| **Weight** | Gravity influence | $9.81 m/s^2$ |
| **Friction** | Kinetic energy loss | $\mu = 0.5$ |

---

## 5. Industrial Case Study: The "Wall-Running" Sequence
**Objective:** Animating a high-velocity parkour move with 100% physical accuracy.
1.  **Path Planning:** Defining a "Spline" that the Pelvis follows.
2.  **IK Locking:** Locking the hands and feet to the wall surface for 2-3 frames per step.
3.  **Anticipation:** Using "Ease-In" to show energy building before the jump.
4.  **Follow-through:** Adding "Spring" motion to the head and arms upon landing.

---

## 6. Glossary of Animation Terms
*   **Anticipation:** The preparation for an action.
*   **Squash and Stretch:** Giving the illusion of weight and volume to a character as it moves.
*   **Follow-Through:** The part of the body that continues moving after the character has stopped.
*   **Smear Frame:** A distorted frame used to simulate high-speed motion.

---

## 7. Mathematical Foundations: The Pendulum Law
*   **Logic:** Stick-arm swings follow personal pendulum math. $T = 2\pi\sqrt{L/g}$.
*   **Implementation:** In 2025, animators use this formula to calculate the "Natural Frequency" of limb movement for stationary "Idles."

---

## 8. Troubleshooting & Performance Verification
*   **Limb Jitter:** Occurs when IK solvers fight over a position. *Fix: Adjust the Pole Target or decrease the IK chain length.*
*   **Weightlessness:** Character appears to "float." *Fix: Increase the "Gravity" parameter in the Dopesheet or decrease the easing duration at the peak of jumps.*

---

## 9. Appendix: Future "Stick" Proceduralism
*   **AI-Generated Keyframes:** Feeding a high-level text prompt (e.g., "Run up a wall") to a model that outputs the corresponding keyframe data for Blender.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Animation Fluidity:** Target 60fps for high-density combat; 24fps for cinematic segments.
*   **Constraint Integrity:** 0% limb-stretching artifacts during extreme poses.

---
[Back to README](../../README.md)

---
name: reinforcement-learning
description: Reinforcement Learning Technical Encyclopedia: Stable-Baselines3 (SB3), SBX (JAX), Reward Engineering, and Gymnasium 2025 Standards.
---

# Skill: Reinforcement Learning (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design, training, and deployment of Reinforcement Learning (RL) agents in the 2025 ecosystem. This document defines the standards for algorithmic selection, JAX-accelerated throughput (SBX), and complex reward signal calibration (RewArt).

## 1. Core Frameworks: Stable-Baselines3 (SB3) & Gymnasium (2025)
The industrial gold standard for reliable, reproducible RL implementations in PyTorch.

### 1.1 SB3 Algorithmic Hierarchy & Suitability
*   **PPO (Proximal Policy Optimization):**
    *   **Math Logic:** Prevents "policy collapse" by clipping the probability ratio: $r_t(\theta) = \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{\text{old}}}(a_t|s_t)}$. Objective becomes: $L^{CLIP}(\theta) = \hat{\mathbb{E}}_t [\min(r_t(\theta)\hat{A}_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)\hat{A}_t)]$.
    *   **Best For:** On-policy stable training, discrete/continuous spaces, and safe multi-threaded environments.
*   **SAC (Soft Actor-Critic):**
    *   **Math Logic:** Maximizes expected reward *plus* entropy: $J(\pi) = \sum_t \mathbb{E}_{(s_t, a_t) \sim \rho_\pi} [r(s_t, a_t) + \alpha \mathcal{H}(\pi(\cdot|s_t))]$.
    *   **Best For:** Sample-efficient off-policy learning, robotic continuous control, and maximum exploration.
*   **TD3 (Twin Delayed DDPG):**
    *   **Math Logic:** Addressing Q-value overestimation through "clipped double-Q learning" and delayed policy updates.

### 1.2 Gymnasium 2025 Environment Standards
*   **Standard Interface:** Mandatory use of `obs, reward, terminated, truncated, info = env.step(action)`.
*   **Observation Normalization:** Always wrap environments in `VecNormalize` to ensure features have zero mean and unit variance—critical for stable neural network convergence.
*   **Vectorization Protocols:** Utilizing `AsyncVectorEnv` for multiprocessing environments to maximize GPU utilization during episode rollouts.

---

## 2. JAX-Accelerated RL (SBX - Stable-Baselines-Jax)
Scaling training throughput via XLA (Accelerated Linear Algebra) and end-to-end GPU execution.

### 2.1 SBX Architecture & Protocols
*   **JIT Compilation:** SBX compiles the entire training step (actor, critic, and optimizer) into a single XLA kernel.
*   **Throughput Gains:** Achieving up to 10-15x faster iterations on NVIDIA H100 hardware compared to standard PyTorch implementations.
*   **Pure Functions:** All custom transition logic must be side-effect free and compatible with `jax.jit` and `jax.vmap`.

---

## 3. Advanced Reward Engineering (RewArt)
Converting sparse "success/fail" outcomes into dense, shapeable feedback signals that guide the agent reliably.

### 3.1 Potential-Based Reward Shaping (PBRS)
*   **Logic:** Adding a shaping function $F(s, s') = \gamma \Phi(s') - \Phi(s)$ where $\Phi$ is the potential of a state. This is mathematically proven not to change the optimal policy $\pi^*$.
*   **Shaping Goals:** Ensuring the agent receives intermediate signals for partial success (e.g., getting closer to a target) without creating "reward loops."

### 3.2 Complex Reward Function Design (Industrial Examples)
*   **Autonomous Driving:** 
    $R = \underbrace{v}_{\text{speed}} \cdot \underbrace{\cos(\theta)}_{\text{direction}} - \underbrace{0.5 \cdot \text{jerk}}_{\text{comfort}} - \underbrace{10.0 \cdot \text{offlane}}_{\text{safety}} - \underbrace{100.0 \cdot \text{collision}}_{\text{terminal}}$.
*   **Robotic Arm Manipulation:** 
    $R = - \text{dist}(\text{gripper}, \text{object}) + \text{closeness\_bonus} + \text{lift\_height\_multiplier} - \text{excessive\_torque\_penalty}$.

---

## 4. Exploration and Advantage Estimation
*   **GAE (Generalized Advantage Estimation):** Utilizing the $\lambda$ parameter ($0.92-0.98$) to control the bias-variance trade-off in advantage calculation.
*   **Intrinsic Motivation:** Implementing RND (Random Network Distillation) or ICM (Intrinsic Curiosity Module) to encourage exploration in large, sparse-reward environments.
*   **Active Learning:** Focusing training on "hard" states where the value function error is highest.

---

## 5. Formal Safety & Constrained RL
*   **Shielding:** Intercepting agent actions with a "Safety Monitor" composed of hard-coded logical rules to prevent hardware damage.
*   **Lagrangian Methods:** Converting safety constraints into penalties that are dynamically weighted during optimization.
*   **Safe Region Incentives:** Rewarding the agent for staying within "High-Confidence Safe Zones."

---

## 6. Real-World Deployment: Sim-to-Real
Techniques for transferring policies from idealized simulations to noisy real-world hardware.

### 6.1 Domain Randomization (DR)
*   **Parameter Randomization:** Varying mass, friction, motor torque, and gravity during simulation.
*   **Visual Randomization:** Changing textures, lighting, and camera positions to ensure the vision model is robust to background noise.
*   **Sensor Noise Modeling:** Injecting Gaussian or Salt-and-Pepper noise into observations to simulate real-world sensor drift.

---

## 7. Troubleshooting & Debugging RL Agents
*   **Value Function Divergence:** Diagnosing when the critic's loss explodes. *Fix: Reduce learning rate or increase batch size.*
*   **Policy Collapse:** When entropy drops to zero too early. *Fix: Increase entropy coefficient or use a larger buffer.*
*   **Episode Timeouts:** Handling `truncated` flags versus `terminated` flags correctly to preserve the Markov property.

---

## 8. Benchmarks: 2025 Ecosystem Performance
| Algorithm | HW | Env | Throughput (S/s) | Convergence |
| :--- | :--- | :--- | :--- | :--- |
| **PPO (SB3)** | 4090 | CartPole | ~2,500 | 20k steps |
| **PPO (SBX)** | 4090 | CartPole | ~22,000 | 18k steps |
| **SAC (SB3)** | 4090 | Ant-v4 | ~450 | 1M steps |
| **SAC (SBX)** | 4090 | Ant-v4 | ~3,800 | 900k steps |

---
[Back to README](../../README.md)

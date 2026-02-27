---
name: remotion-video
description: Remotion Video Technical Encyclopedia: React-based Video Generation, Time-Scaling Math, Parallel Rendering, and Canvas Integration.
---

# Skill: Remotion Video (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design and construction of programmatic video using the Remotion framework (React/TypeScript) in the 2025 ecosystem. This document defines the standards for composition architecture, sub-frame animation math, and high-performance parallel rendering using AWS Lambda.

---

## 1. Composition Architecture (React-Video)
Standardizing on the most modular and maintainable video components.

### 1.1 The "Time-as-State" Protocol
*   **Logic:** Utilizing the `useCurrentFrame()` and `useVideoConfig()` hooks to make the UI a deterministic function of the current frame number.
*   **Interpolate Standards:** Mandatory use of the `interpolate()` function for all visual transitions (Opacity, Scale, Position) to ensure mathematically smooth easing.

### 1.2 Implementation Protocol (Base Composition)
```typescript
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

# 1.2.1 Mandatory Animation Logic
export const MyScene = () => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    
    # 1.2.2 Easing Math (Bezier-style)
    const opacity = interpolate(frame, [0, 30], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
    });
    
    return <div style={{ opacity }}>Animated Scene</div>;
};
```

---

## 2. Advanced Motion & Time-Scaling Math
Implementing professional kinetic typography and transitions in code.

### 2.1 Sub-frame Precision Protocols
*   **Logic:** Remotion supports sub-frame interpolation, allowing for 60fps-smooth motion even when the composition itself is rendered at 24fps.
*   **Spring Physics:** Utilizing `spring()` for natural-feeling, weight-based movement (Bounce, Stiff, Damped) instead of primitive linear easing.

### 2.2 Sequence & Series Orchestration
Utilizing the `<Sequence>` and `<Series>` components to manage the global timeline without manual frame calculation, ensuring that moving one clip automatically shifts all subsequent clips.

---

## 3. High-Performance Parallel Rendering
Scaling video production using serverless infrastructure.

### 3.1 AWS Lambda (Remotion Lambda) Standards
*   **Logic:** Splitting a 10-minute video into 600 separate segments (1s each) and rendering them in parallel across 600 Lambda instances.
*   **Cost Optimization:** Utilizing "ARM64" (Graviton) instances for a 20%+ reduction in render costs.

### 3.2 Metadata-Driven Production
Generating thousands of unique videos (e.g., personalized ads or tutorials) by injecting different `props` into the same Remotion composition at runtime via the CLI.

---

## 4. Technical Appendix: Remotion Reference
| Hook / Tool | Technical Purpose | Standard |
| :--- | :--- | :--- |
| `useCurrentFrame` | The current time-index | Essential |
| `continueRender` | Handling async assets | Reactive |
| `StaticColor` | Avoiding prop-drilling | Optimized |
| `Audio` | Programmatic sound mapping| Sub-frame |

---

## 5. Industrial Case Study: Real-time Data Journalism
**Objective:** Automatically generating a video summary of a stock market crash within 60 seconds of the event.
1.  **Ingestion:** Python script fetches market data.
2.  **Mapping:** Data is passed to a Remotion Lambda instance as `inputProps`.
3.  **Visualization:** A React-based chart (using D3 or Recharts) animates based on the `frame` index.
4.  **Export:** The 1080p MP4 is pushed to S3 and shared via social media APIs.

---

## 6. Glossary of Remotion Terms
*   **Composition:** A container for a video sequence.
*   **FPS (Frames Per Second):** The temporal resolution of the video.
*   **Interpolation:** The process of estimating values between two known points.
*   **Prop-drilling:** Passing data through many layers of components (to be avoided).

---

## 7. Mathematical Foundations: The Bezier Curve in CSS
*   **Formula:** $B(t) = (1-t)^3P_0 + 3(1-t)^2tP_1 + 3(1-t)t^2P_2 + t^3P_3$.
*   **Implementation:** In 2025, Remotion developers use this math to create custom easing functions that match the "Brand Physics" of the project.

---

## 8. Troubleshooting & Performance Verification
*   **Flickering Video:** Occurs when async assets (e.g., images) are not pre-cached. *Fix: Use `delayRender()` and `continueRender()` to pause the engine until data is ready.*
*   **Memory Leaks:** Large DOM trees in compositions. *Fix: Use `Canvas` for complex particles or thousands of moving objects.*

---

## 9. Appendix: Future "Remotion-AI" Trends
*   **Latent Video Integration:** Utilizing Remotion as the "Control Layer" for Generative Video models—orchestrating AI video segments (Luma/Runway) together with programmatic overlays and audio in a single React tree.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Render Efficiency:** Target < 1s of render time per 1s of 1080fps60 video on modern local hardware.
*   **State Parity:** 100% deterministic output (the same frame number must ALWAYS produce the same pixel state).

---

## 11. Recommended Project Structure (2025)
Based on community best practices for scalable Remotion projects:

```text
remotion-project/
├── src/
│   ├── Root.tsx                    # Composition registry
│   ├── actions/                    # Reusable animation functions
│   │   ├── fadeIn.ts
│   │   └── slideUp.ts
│   ├── arrangements/               # Main movie files
│   │   └── MainVideo.tsx
│   ├── helpers/                    # Hooks and settings
│   │   ├── useResponsive.ts
│   │   └── constants.ts
│   ├── parts/                      # Reusable UI elements
│   │   ├── Title.tsx
│   │   └── Transition.tsx
│   └── segments/                   # Complete video moments
│       ├── Intro.tsx
│       └── Outro.tsx
├── public/                         # Assets (images, fonts, audio)
├── remotion.config.ts
└── package.json
```

---

## 12. Font Loading & Text Measurement Protocol
Critical for pixel-perfect typography:

### 12.1 Safe Font Loading
```typescript
import { useEffect, useState } from 'react';
import { continueRender, delayRender } from 'remotion';

export const useFontLoaded = (fontFamily: string) => {
  const [loaded, setLoaded] = useState(false);
  const [handle] = useState(() => delayRender());

  useEffect(() => {
    document.fonts.load(`16px ${fontFamily}`).then(() => {
      setLoaded(true);
      continueRender(handle);
    });
  }, [fontFamily, handle]);

  return loaded;
};
```

### 12.2 Text Measurement Best Practices
*   Match ALL font properties between measurement and render (fontFamily, fontSize, fontWeight, letterSpacing).
*   Use `white-space: pre` and `display: inline-block` for accurate measurements.
*   Avoid padding/borders on measurement elements (skews results).

---

## 13. React 19 Compatibility (2025)
For optimal performance with React 19:
```bash
npm install react@19.0.0 react-dom@19.0.0
npm install -D @types/react@19.0.0 @types/react-dom@19.0.0
```
*   Remotion 4.0.0+ required for React 19 support.
*   Leverage React Server Components for complex data fetching.

---

## 14. Responsive Video Design
Building videos that adapt to different aspect ratios:

```typescript
export const ResponsiveLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width, height } = useVideoConfig();
  const isPortrait = height > width;
  const isMobile = width < 720;

  return (
    <AbsoluteFill style={{
      flexDirection: isPortrait ? 'column' : 'row',
      padding: isMobile ? 20 : 40,
    }}>
      {children}
    </AbsoluteFill>
  );
};
```

---

## 15. AI Agent Integration (Official 2025 Feature)
Remotion now provides official "Agent Skills" for AI coding assistants:
*   Instruction sets that teach AI tools how to generate valid Remotion code.
*   Reduces hallucination in AI-generated video compositions.
*   Available at: `remotion.dev/docs/agent-skills`

---

## 16. Three.js & WebGL Integration
For 3D scenes using `@remotion/three`:

```typescript
import { ThreeCanvas } from '@remotion/three';
import { useCurrentFrame } from 'remotion';

export const Scene3D: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <ThreeCanvas>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <mesh rotation={[0, frame * 0.02, 0]}>
        <boxGeometry args={[2, 2, 2]} />
        <meshStandardMaterial color="#ff6b6b" />
      </mesh>
    </ThreeCanvas>
  );
};
```

---

## 17. Lottie Animation Integration
Embedding After Effects animations:

```typescript
import { Lottie } from '@remotion/lottie';
import animationData from './loading.json';

export const LottieAnimation: React.FC = () => (
  <Lottie
    animationData={animationData}
    playbackRate={1}
    loop
    style={{ width: 200, height: 200 }}
  />
);
```

---

## 18. CI/CD Pipeline for Video Production
GitHub Actions example for automated video rendering:

```yaml
name: Render Video
on:
  push:
    branches: [main]

jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npx remotion render src/index.ts MainVideo out/video.mp4 --codec=h264
      - uses: actions/upload-artifact@v4
        with:
          name: rendered-video
          path: out/video.mp4
```

---

[Back to README](../../README.md)

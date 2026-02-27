---
name: data-visualization
description: Data Visualization Technical Encyclopedia: Matplotlib/Seaborn Standards, Interactive Plotly/D3, Vector Graphics (SVG), and 'CIELAB' Color Accuracy.
---

# Skill: Data Visualization (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design and construction of publication-quality, interactive, and high-fidelity data visualizations in the 2025 ecosystem. This document defines the standards for Matplotlib/Seaborn scientific plots, Plotly-based interactive dashboards, and Unicode-saturated vector graphics.

---

## 1. Scientific Publication Standards (Matplotlib/Seaborn)
Standardizing on the most rigorous formats for peer-reviewed style visualizations.

### 1.1 Publication-Ready Formatting Protocols
*   **Resolution:** Mandatory 300 DPI for raster formats (PNG) or 100% vector (SVG/PDF/EPS).
*   **Typography:** Utilizing LaTeX integration (`plt.rcParams['text.usetex'] = True`) for mathematical notation in labels and legends.
*   **Color-Blind Accessibility:** Mandatory use of perceptually uniform color maps (e.g., `viridis`, `magma`, `cividis`).

### 1.2 Implementation Protocol (Scientific Plot)
```python
import matplotlib.pyplot as plt
import seaborn as sns

# 1.2.1 High-Resolution Setup
plt.style.use('seaborn-v0_8-paper')
fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
sns.lineplot(data=df, x='time', y='value', ax=ax)
ax.set_title(r"$\Delta$ Performance Over Time", fontsize=12)
plt.savefig("output.pdf", bbox_inches='tight')
```

---

## 2. Interactive Dashboarding (Plotly & D3)
Orchestrating complex, stateful visualizations for web and analysis environments.

### 2.1 Reactive State Management
*   **Logic:** Utilizing "Cross-filtering" where clicking on one chart (e.g., a Bar chart) automatically filters the data in another (e.g., a Map).
*   **Optimization:** Utilizing "WebGl" rendering for datasets > 100,000 points to ensure 60fps interaction speed.

### 2.2 Aesthetic Normalization
*   **Protocol:** Mandatory use of custom CSS templates for Plotly to match the "Enterprise Cyberpunk" or "Minimalist Science" brand appearance.

---

## 3. High-Fidelity Signal Processing & Colorspace (CIELAB)
Ensuring that color represents data with maximum accuracy.

### 3.1 Perceptual Uniformity Math
*   **Logic:** In the CIELAB colorspace, a change in color value is perceived as a proportional change in the data value, preventing the "Visual Distortion" common in RGB-based scales.
*   **Standard:** All heatmaps must use normalized CIELAB L* (Lightness) gradients to represent magnitude.

---

## 4. Technical Appendix: Data Visualization Reference
| Tool / Format | Technical Purpose | Performance Target |
| :--- | :--- | :--- |
| **SVG** | Scalable vector graphics | Inf. Res |
| **Seaborn** | High-level statistical plots | Medium |
| **Plotly** | Interactive web dashboards | High (WebGl) |
| **Graphviz** | Hierarchical graph data | Complex |

---

## 5. Industrial Case Study: Real-time Financial Anomaly Detection
**Objective:** Building a heatmap of 1,000 tickers across 24 hours.
1.  **Architecture:** Utilizing `FastAPI` to serve the data manifest.
2.  **Visualization:** A Plotly `Heatmap` using the `inferno` color-palette.
3.  **Interaction:** Hover-states reveal the exact Z-score and p-value for each anomaly.
4.  **Verification:** Automated 1-second refresh rate with zero UX lag.

---

## 6. Glossary of Data Viz Terms
*   **Aesthetics:** The mapping of data variables to visual properties (Color, Size, Shape).
*   **Gamut:** The range of colors that a specific device or colorspace can represent.
*   **Overplotting:** When data points are so dense they obscure each other. *Fix: Use Alpha-blending or Hexbinning.*
*   **Facet / Trellis:** Breaking a large chart into multiple smaller charts based on a category.

---

## 7. Mathematical Foundations: The Logarithmic Scale
*   **Problem:** Data spanning multiple orders of magnitude (e.g., population, stock prices).
*   **Formula:** $y' = \log_{10}(y)$.
*   **Implementation:** In 2025, Moltbot uses this to prevent "Floor Squashing" where low-value data disappears next to high-value peaks.

---

## 8. Troubleshooting & Performance Verification
*   **Jagged Lines:** Occurs with low-DPI raster exports. *Fix: Use Vector (PDF) or increase DPI to 600.*
*   **Informational Overload:** Too many labels on a single chart. *Fix: Use "Interactive Tooltips" rather than static labels for non-critical data.*

---

## 9. Appendix: Future "Generative Visualization"
*   **Natural Language to Chart:** Utilizing local LLMs to generate complex `matplotlib` or `plotly` code on-the-fly from high-level user queries (e.g., "Show me the correlation between X and Y as a 3D scatter plot").

---

## 10. Benchmarks & Performance Standards (2025)
*   **Render Speed:** Target < 500ms for static publication plots.
*   **Memory Efficiency:** Target < 100MB for interactive browser-based visualizations of datasets with 10k+ points.

---
[Back to README](../../README.md)

---
name: chrome-extension-best-practices
description: Chrome Extension Best Practices Technical Encyclopedia: Manifest v3, Service Worker Lifecycle, Message Passing Security, and Offscreen Documents.
---

# Skill: Chrome Extension Best Practices (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the design and construction of modern browser extensions utilizing the Manifest v3 (MV3) architecture in the 2025 ecosystem. This document defines the standards for Service Worker orchestration, secure message passing, and the utilization of Offscreen Documents for high-complexity AI or media processing.

---

## 1. Manifest v3 Architecture (2025)
Standardizing on the most secure and performant extension structure.

### 1.1 Service Worker Lifecycle
*   **Logic:** Replacing persistent background pages with ephemeral Service Workers that are terminated by the browser when idle.
*   **State Management:** Mandatory use of the `chrome.storage.local` or `chrome.storage.session` APIs to persist state between worker lifecycles.
*   **Event Handling:** Ensuring all listeners (e.g., `onInstalled`, `onMessage`) are registered at the top-level of the script to prevent missed events during cold-boot.

### 1.2 Declarative Net Request (DNR) Protocols
*   **Logic:** Shifting from `webRequest` (blocking) to `declarativeNetRequest` for privacy-first network filtering.
*   **Standard:** Utilizing static and dynamic rule sets to modify headers or block URLs without accessing user data directly.

---

## 2. Secure Message Passing & Interoperability
Standardizing the communication between Content Scripts, Popups, and Service Workers.

### 2.1 The "Port" Protocol
*   **Logic:** Utilizing `chrome.runtime.connect()` for persistent, two-way communication channels (e.g., during long-form data extraction).
*   **Message Validation:** Mandatory use of "Message Schemas" (e.g., Pydantic-style JS validation) to ensure that incoming messages from content scripts are not malicious.

### 2.2 Cross-Origin Isolation & Security
Configuring `content_security_policy` (CSP) to prevent the execution of untrusted remote code, ensuring the extension remains a "Closed, Secure System."

---

## 3. Offscreen Documents & Complex Processing
Bridging the limits of Service Workers for high-demand tasks.

### 3.1 Offscreen Document Standards
*   **Reasoning:** Since Service Workers lack access to the DOM and certain Web APIs (WebAudio, OffscreenCanvas), Offscreen Documents provide a temporary DOM environment for these tasks.
*   **Lifecycle:** Ensuring the document is opened ONLY when needed and closed immediately upon task completion to save system resources.

### 3.2 AI Integration (Side Panel & Local LLM)
Utilizing the `sidePanel` API for persistent tools that don't disappear when the user clicks away, combined with local AI models (via WebGPU) for privacy-conscious data analysis.

---

## 4. Technical Appendix: Chrome Extension Reference
| API | Technical Purpose | Performance Target |
| :--- | :--- | :--- |
| `chrome.storage` | State persistence | - |
| `chrome.tabs` | Tab orchestration | High-Latency |
| `chrome.scripting`| Dynamic execution | Secure |
| `chrome.proxy` | Traffic redirection | Complex |

---

## 5. Industrial Case Study: The "AI-Driven Researcher" Extension
**Objective:** An extension that summarizes and catalogs every technical paper the user reads.
1.  **Architecture:** A Service Worker listens for `onUpdated` events on PDF URLs.
2.  **Extraction:** A Content Script extracts the text and sends it to an Offscreen Document.
3.  **Processing:** The Offscreen Document runs a local WebGPU-based LLM to summarize the text.
4.  **Storage:** The summary is saved to `chrome.storage.local` and synced to the cloud via a gRPC bridge.

---

## 6. Glossary of Chrome Extension Terms
*   **Manifest v3:** The latest major version of the chrome extension architecture.
*   **Content Script:** JavaScript that runs in the context of a specific webpage.
*   **Shadow DOM:** Isolated CSS/HTML used by extensions to prevent style-bleed on the host page.
*   **Background Service Worker:** The extension's central event handler.

---

## 7. Mathematical Foundations: The Exponential Backoff
*   **Problem:** API calls or network requests failing due to rate limits.
*   **Formula:** $\text{delay} = \text{base} \cdot 2^n$.
*   **Implementation:** In 2025, extensions use this math to retry failed sync operations without overwhelming the browser or the server.

---

## 8. Troubleshooting & Performance Verification
*   **Zombie Service Workers:** Workers that fail to terminate, draining battery. *Fix: Ensure all async operations have clear timeouts.*
*   **Permission Bloat:** Requesting too many permissions during install. *Fix: Use `optional_permissions` and request them at runtime only when needed.*

---

## 9. Appendix: Future "Wasm" Extensions
*   **High-Speed Processing:** Utilizing WebAssembly (Wasm) inside the extension to handle tasks like video transcoding, spectral audio repair, or complex physics simulations with near-native performance.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Startup Latency:** Target < 100ms for Service Worker response.
*   **Memory Usage:** < 50MB for persistent storage and worker state.

---
[Back to README](../../README.md)

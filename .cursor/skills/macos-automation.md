---
name: macos-automation
description: macOS Automation Technical Encyclopedia: AppleScript, JXA, 'launchd', 'defaults' Domains, and 'osascript' Integration.
---

# Skill: macOS Automation (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for the automation of the macOS operating system and its native applications in the 2025 ecosystem. This document defines the standards for AppleScript/JXA (JavaScript for Automation), `launchd` service orchestration, and the manipulation of system `defaults`.

---

## 1. AppleScript & JXA Standards (Modern Interop)
Utilizing the Open Scripting Architecture (OSA) to control GUI-based applications.

### 1.1 AppleScript / JXA Protocols
*   **Targeting Applications:** Using the `tell application` (AppleScript) or `Application()` (JXA) constructors to access the application's scripting dictionary (sdef).
*   **GUI Scripting (Accessibility):** Utilizing "System Events" to interact with non-scriptable UI elements (buttons, menus) via their accessibility hierarchy.
*   **Error Handling:** Mandatory `try...on error` (AppleScript) or `try...catch` (JXA) blocks to manage application timeouts and state mismatches.

### 1.2 Implementation Protocol (`osascript` + Python)
```python
import subprocess

# 1.2.1 Calling AppleScript from Python
def run_applescript(script):
    subprocess.run(["osascript", "-e", script], capture_output=True, text=True)

# 1.2.2 Example: Toggling Dark Mode
run_applescript('tell application "System Events" to tell appearance preferences to set dark mode to not dark mode')
```

---

## 2. System Service Orchestration (`launchd`)
Standardizing on the native macOS init-system for persistent background tasks.

### 2.1 Plist Configuration Standards
*   **Labeling:** Domain-style naming (e.g., `com.user.project.service`).
*   **Intervals:** Utilizing `StartInterval` (fixed time) or `WatchPaths` (trigger on file change).
*   **Logging:** Mandatory routing of `StandardOutPath` and `StandardErrorPath` to persistent log files in `~/Library/Logs`.

### 2.2 Daemon vs. Agent Protocols
*   **LaunchAgents:** Running in the user context (GUI interaction allowed).
*   **LaunchDaemons:** Running in the system context (no GUI, high privilege).

---

## 3. System Configuration via `defaults`
Programmatic manipulation of the macOS preferences database.

### 3.1 Domain Targeting
*   **Global Domain:** `NSGlobalDomain` for system-wide settings (e.g., key repeat rate).
*   **Application Domains:** Individual bundles (e.g., `com.apple.finder`) for application-specific behaviors.

### 3.2 Technical Implementation Checklist
- [ ] Identifying the correct domain and key via `defaults read`.
- [ ] Verifying the data type (string, bool, int) before writing.
- [ ] Restarting the target application (e.g., `killall Finder`) to apply changes.

---

## 4. Technical Appendix: macOS Automation Reference
| Tool / Command | Primary Utility | Environment |
| :--- | :--- | :--- |
| `osascript` | Execute AppleScript/JXA | Shell |
| `launchctl` | Load/Unload/Start services | Shell |
| `defaults` | Preference database access | Shell |
| `scutil` | System configuration (Network) | Shell |
| `system_profiler` | Hardware/Software auditing | Shell |

---

## 5. Industrial Case Study: Automated Production Environment
**Objective:** Setting up a "Focus Mode" that closes distracting apps and starts development tools.
1.  **State Management:** An AppleScript checks which apps are currently running.
2.  **App Orchestration:** `tell application "Slack" to quit`.
3.  **Config Injection:** `defaults write com.apple.dock "autohide" -bool true`.
4.  **Service Launch:** Starting a `launchd` agent that monitors the `src/` directory for automated testing.

---

## 6. Glossary of macOS Automation Terms
*   **JXA (JavaScript for Automation):** A modern replacement for AppleScript based on JavaScript.
*   **Plist (Property List):** The standard XML/Binary format for configuration in macOS.
*   **SDEF (Scripting Definition):** The dictionary file that defines which commands an application supports.
*   **Kext (Kernel Extension):** A kernel-level plugin (largely deprecated in favor of System Extensions in 2025).

---

## 7. Mathematical Foundations: The Key Repeat Math
*   **Logic:** Calculating the optimal `InitialKeyRepeat` and `KeyRepeat` values to match a developer's typing speed.
*   **Optimization:** Mapping standard integer values to milliseconds of delay for precise UX tuning.

---

## 8. Troubleshooting & Performance Verification
*   **Sandbox Violations:** TCC (Transparency, Consent, and Control) blocking scripting. *Fix: Grant "Full Disk Access" or "Accessibility" to the terminal/app.*
*   **Zombie launchd Jobs:** Services failing to stop. *Fix: Use `launchctl bootout` or `launchctl list` to audit state.*

---

## 9. Appendix: Future "Apple Intelligence" Automation
*   **Siri Shortcuts (Intents):** Utilizing the Shortcuts app to bridge high-level user commands with low-level shell scripts and Python logic via the "Run Shell Script" action.

---

## 10. Benchmarks & Performance Standards (2025)
*   **Command Latency:** Target < 100ms for `defaults` reads/writes.
*   **Service Reliability:** 100% uptime for `launchd` agents in production environments.

---
[Back to README](../../README.md)

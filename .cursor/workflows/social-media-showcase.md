---
description: Workflow for generating World-Class Marketing Assets (LinkedIn, YouTube, X).
---

# Social Media & Showcase Workflow

[Back to README](../../README.md)

**Trigger:** Project Completion ("Gold Master" status).
**Goal:** Create premium content that showcases the engineering quality.

## 1. Visual Asset Production (The RAW Materials)
Before generating text, you MUST generate these assets:
*   **CLI:** SVG recording of a complex command (use `terminalizer` or `asciinema`).
*   **Web:** High-res screenshots of logical flows (Home -> Action -> Result).
*   **Bot:** GIF of a full conversation flow (Telegram/Discord).
*   **Code:** Carbon.sh images of the cleanest code snippets.

## 4. Prompt Strategy:
    *   **Master Template:** Use `prompts/template_linkedin_launch.txt` for high-impact announcements.
    *   **Constraint:** Content MUST be "Product-Led" (focus on problem/solution, not marketing fluff).
    *   **Tone:** "Engineer to Engineer" (Skeptical, Technical, Direct).

## 2. LinkedIn/X Viral Post Generator
**Action:** Use the "Architect" model to write the post.

**System Prompt for Model:**
```text
You are a Developer Advocate at Google/Meta. Write a LinkedIn post about this project.
Structure:
1.  **Hook:** A bold claim or relatable dev struggle. (e.g., "I fixed AI hallucinations forever.")
2.  **The Solution:** 2-3 bullet points on how [Project Name] solves it using [Tech Stack].
3.  **The "Wow":** Mention the coolest feature (e.g., "It uses a daily circuit breaker for API costs").
4.  **Call to Action:** "Check the repo 👇" or "Star it on GitHub".
5.  **Tags:** #OpenSource #[Language] #AI #Engineering
Tone: Professional, humble-brag, technical but accessible.
```

## 3. YouTube Video Production
**Action:** Generate a full script for a 3-5 minute showcase.

**Step A: Script Generation Prompt**
```text
Write a YouTube Video Script for [Project Name].
Role: Tech YouTuber (like Fireship or Hussein Nasser).
Structure:
1.  **Intro (0:00-0:30):** The Problem. Why does existing tooling suck?
2.  **The Reveal (0:30-1:00):** Introduce [Project Name]. High-energy montage.
3.  **The Demo (1:00-3:00):** Walkthrough of the CLI/Web App. Show, don't just tell.
    *   *Visual Note:* Show the user typing `install.sh`.
4.  **Under the Hood (3:00-4:30):** Explain the Architecture (Architect vs Executor, Daily Quota). Explain the `agent-constitution`.
5.  **Outro (4:30-5:00):** "Try it yourself."
```

**Step B: Thumbnail AI Prompt**
```text
(Use Midjourney/DALL-E 3)
Prompt: A futuristic 3D isometric dashboard floating in a void, glowing neon blue and orange lines, displaying "AI ARCHITECT" text, cyberpunk aesthetic, 8k resolution, highly detailed, tech-focused, cinematic lighting.
```

## 4. Final Polish
*   **Check:** Do the screenshots match the text?
*   **Check:** Is the GitHub link clearly visible?
*   **Check:** Did you credit the "Agent Constitution"?

## 5. Storage & Organization (Mandatory)
*   **Rule:** Drafts and generated assets MUST NOT clutter the root.
*   **Action:** Create a platform-specific folder in `.storage/`.
    *   Example: `.storage/LinkedIn/`, `.storage/YouTube/`.
*   **Move:** Place all `*_draft.md`, subtitles, and raw assets there.
    *   Only the **FINAL** approved asset moves to `assets/`.

---
[Back to README](../../README.md)

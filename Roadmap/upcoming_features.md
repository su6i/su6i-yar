# 🚀 Su6i Yar - Next Steps & Roadmap

This document serves as the official backlog for upcoming features and integrations.

## 🎵 Upcoming Features (High Priority)

### 1. Suno AI Integration (Birthday Songs)
**Objective:** Automatically generate personalized Happy Birthday songs using the **Suno AI API**.
- **Context:** We have a solid foundation in `src/features/birthday/handlers.py` and cron jobs in `jobs.py`.
- **Implementation:** 
  - Connect to a Suno API wrapper (or official endpoint).
  - Draft personalized "Happy Birthday [User]" lyrics dynamically using LLM.
  - Send the generated `.mp3`/`.mp4` directly to the birthday user.
- **Status:** Architecture drafted, waiting for API integration.

## 🧠 Brainstorming (Medium Priority)
- Voice Cloning for specific voices (using ElevenLabs interface).
- Automated Subtitle Generation (VTT/SRT embedded burning) for downloaded videos.

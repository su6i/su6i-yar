---
name: episode-structure-45min
description: 45-Minute Episode Structure Technical Encyclopedia: 3-Part Format, Cognitive Load Management, and Daily Content Production Pipeline.
---

# Skill: 45-Minute Episode Structure

[Back to README](../../README.md)

Technical protocols for producing 45 minutes of daily language learning content using the 3-part episode format. This document defines standards for cognitive pacing, vocabulary distribution, and production workflow optimization.

---

## 1. The 3-Part Episode Format

### 1.1 Episode Architecture
```
┌─────────────────────────────────────────────────┐
│         DAILY EPISODE (45 min total)            │
├─────────────────────────────────────────────────┤
│  Part 1: داستان اصلی (Main Story)     ~20 min  │
│  Part 2: تمرین ذهنی (Active Recall)   ~10 min  │
│  Part 3: دیپ دایو (Deep Dive)         ~15 min  │
└─────────────────────────────────────────────────┘
```

### 1.2 Part Breakdown

| Part | Purpose | Language Level | Audio | Visual |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Immersive storytelling | Target (100%) | Full dialogue | Full animation |
| **2** | Force active recall | Target (100%) | Silent/Music | Subtitle flash |
| **3** | Concept explanation | Lower (-1 level) | Clear narration | Diagrams |

---

## 2. Part 1: Main Story (20 min)

### 2.1 Story Structure
```
STORY ARC (Hero's Journey Compressed):
├── Hook (0-1 min) → Problem introduction
├── Setup (1-5 min) → Character & context
├── Rising Action (5-12 min) → Challenges
├── Climax (12-16 min) → Key realization
└── Resolution (16-20 min) → Lesson learned
```

### 2.2 Vocabulary Integration
*   **New words:** 15-20 introduced naturally.
*   **Review words:** 50-80 from Leitner system.
*   **Density:** 1 new word per 60-90 seconds.

### 2.3 Character Dialogue
```xml
<scene id="1" duration="180">
  <dialogue character="protagonist" emotion="curious">
    What does "automation" really mean?
  </dialogue>
  <dialogue character="mentor" emotion="calm">
    It means making the machine do the work for you.
  </dialogue>
  <action>Visual: Robot handling papers</action>
</scene>
```

---

## 3. Part 2: Active Recall (10 min)

### 3.1 The Minimal Subtitle Technique
*   **No audio** except ambient music.
*   Subtitles appear for **3 seconds**, then fade.
*   Viewer must recall pronunciation and meaning.

### 3.2 Implementation
```python
RECALL_SEQUENCE = {
    "display_time": 3.0,      # seconds
    "fade_time": 0.5,
    "pause_between": 2.0,     # thinking time
    "words_per_session": 30,  # subset of story
}
```

### 3.3 Visual Treatment
*   Same story scenes, stripped of audio.
*   Key vocabulary highlighted.
*   Progress bar showing completion.

---

## 4. Part 3: Deep Dive (15 min)

### 4.1 Feynman Technique Application
*   Explain technical concepts **simply**.
*   Use language **one level below** story level.
*   Break down complex sentences from Part 1.

### 4.2 Structure
```
DEEP DIVE SEGMENTS (3 min each):
├── Vocabulary Spotlight (5 words in depth)
├── Sentence Breakdown (grammar implicit)
├── Cultural Context (why this phrase?)
├── Pronunciation Focus (audio slowed)
└── Quick Quiz (multiple choice, visual)
```

### 4.3 Narrator Voice
*   Slower pace than story.
*   More pauses for processing.
*   Warmer, more supportive tone.

---

## 5. Daily Production Pipeline

### 5.1 Workflow
```
DAILY PRODUCTION (Target: 4-6 hours total)
├── Script Generation (Claude)     1 hr
├── Voice Synthesis (GPU batch)    2 hr
├── Animation (Blender/Template)   2 hr
├── Assembly (FFmpeg/Resolve)      1 hr
└── Quality Check                  0.5 hr
```

### 5.2 Parallel Processing
```python
async def produce_episode(script):
    # Run in parallel
    voice_task = synthesize_all_voices(script)
    visual_task = render_animations(script)
    
    audio = await voice_task
    video = await visual_task
    
    return assemble_final(audio, video)
```

---

## 6. Cognitive Load Management

### 6.1 Pomodoro Integration
```
VIEWER EXPERIENCE:
├── Part 1 (20 min) = Focus Block 1
├── [Suggested Break: 5 min]
├── Part 2 (10 min) = Recall Exercise
├── Part 3 (15 min) = Focus Block 2
└── Total Active: 45 min
```

### 6.2 Vocabulary Pacing
| Time Block | New Words | Review Words | Density |
| :--- | :--- | :--- | :--- |
| 0-10 min | 8 | 20 | Higher |
| 10-20 min | 7 | 30 | Medium |
| 20-30 min | 0 | 30 | Recall only |
| 30-45 min | 5 | 20 | Explanation |

---

## 7. File Naming Convention

```
episodes/
├── EN/
│   ├── S01E001_automation_basics/
│   │   ├── part1_story.mp4
│   │   ├── part2_recall.mp4
│   │   ├── part3_deepdive.mp4
│   │   ├── combined_45min.mp4
│   │   └── metadata.json
```

---

## 8. Benchmarks

| Metric | Target |
| :--- | :--- |
| Production time | <6 hrs/episode |
| Retention rate | >70% after 24hrs |
| Viewer completion | >60% of 45min |
| New vocab retained | >80% after review |

---

[Back to README](../../README.md)

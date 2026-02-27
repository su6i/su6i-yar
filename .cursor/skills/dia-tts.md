---
name: dia-tts
description: Dia TTS Technical Encyclopedia: Turn-Taking Dialogue, Multi-Speaker Conversations, and Real-Time Voice Switching.
---

# Skill: Dia TTS (Dialogue Synthesis)

[Back to README](../../README.md)

Technical protocols for implementing Nari Labs' Dia TTS model for natural turn-taking dialogue synthesis. This document defines standards for multi-speaker conversations, emotion injection, and integration with the Moltbot voice orchestration layer.

---

## 1. Dia Architecture Overview

### 1.1 Core Capabilities
*   **Turn-Taking:** Native support for conversational flow between speakers.
*   **Non-Verbal Sounds:** Laughs, sighs, coughs, gasps generated inline.
*   **Speed:** Real-time generation on consumer GPUs.

### 1.2 Model Specifications
| Spec | Value |
| :--- | :--- |
| Parameters | 1.6B |
| Speakers | 2 (native), expandable |
| Sample Rate | 44.1kHz |
| VRAM | 8GB minimum |
| Languages | English (primary), multilingual coming |

---

## 2. Script Format for Dia

### 2.1 Speaker Tags
```
[S1] Hello, how are you doing today?
[S2] I'm great! (laughs) What about you?
[S1] Pretty good. (sighs) Just tired from work.
```

### 2.2 Non-Verbal Annotations
| Tag | Sound |
| :--- | :--- |
| `(laughs)` | Natural laughter |
| `(sighs)` | Exhale/sigh |
| `(coughs)` | Cough |
| `(gasps)` | Surprised inhale |
| `(clears throat)` | Throat clear |

---

## 3. Python Integration

### 3.1 Basic Usage
```python
from dia import Dia

model = Dia.from_pretrained("nari-labs/Dia-1.6B")

dialogue = """
[S1] Welcome to today's lesson on automation.
[S2] (excited) Oh, I've been waiting for this!
[S1] Let's start with the basics.
"""

audio = model.generate(dialogue)
audio.save("dialogue.wav")
```

### 3.2 Voice Cloning with Dia
```python
# Clone specific voices for S1 and S2
model.set_speaker_reference(
    speaker="S1",
    reference="protagonist_30s.wav"
)
model.set_speaker_reference(
    speaker="S2", 
    reference="mentor_30s.wav"
)
```

---

## 4. Emotional Modulation

### 4.1 Inline Emotion Tags
```
[S1] <happy> That's exactly what I needed! </happy>
[S2] <sad> But what if it doesn't work? </sad>
[S1] <confident> Trust the process. </confident>
```

### 4.2 Prosody Control
```python
# Fine-grained control
audio = model.generate(
    dialogue,
    speed=1.1,          # Slightly faster
    pitch_shift=0,      # No pitch change
    energy=0.8          # Slightly calmer
)
```

---

## 5. Integration with Moltbot Pipeline

### 5.1 Voice Router Integration
```python
VOICE_ROUTER = {
    "dialogue_scene": {
        "model": "dia",
        "speakers": {
            "S1": "protagonist",
            "S2": "mentor"
        }
    },
    "narration_scene": {
        "model": "xtts-v2",
        "speaker": "narrator"
    }
}
```

### 5.2 Scene-Based Switching
```python
async def synthesize_scene(scene: dict):
    if scene["type"] == "dialogue":
        return await dia_generate(scene["script"])
    elif scene["type"] == "narration":
        return await xtts_generate(scene["text"])
```

---

## 6. Hardware Optimization

### 6.1 Mac Mini M4 (MLX)
*   Dia has community MLX port in development.
*   Current status: Experimental, slower than CUDA.
*   Fallback: Use API-based inference.

### 6.2 Cloud GPU (RTX 4090)
*   Full speed: ~10x real-time.
*   Batch processing: Queue full episode dialogues.

---

## 7. Troubleshooting

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| Robotic voice | Too short reference | Use 15-30s ref audio |
| Speaker bleed | Similar voices | More distinct refs |
| Timing issues | Long pauses | Adjust `pause_duration` |

---

## 8. Benchmarks

| Metric | Target |
| :--- | :--- |
| Real-time factor | >5x on RTX 4090 |
| MOS score | >4.0 |
| Turn latency | <100ms |

---

[Back to README](../../README.md)

---
name: emotional-voice-acting
description: Emotional Voice Acting Technical Encyclopedia: Multi-Emotion Reference Recording, GPT-SoVITS Fine-Tuning, and One-Person Multi-Character Production.
---

# Skill: Emotional Voice Acting (One Person → Many Characters)

[Back to README](../../README.md)

Technical protocols for producing commercial-quality emotional voice acting from a single performer. This document defines standards for reference recording, emotion cloning with GPT-SoVITS, and character voice differentiation.

---

## 1. The One-Person Studio Problem

### 1.1 Challenge
*   **Reality:** You are one person voicing multiple characters.
*   **Requirement:** Each character needs distinct voice + emotions.
*   **Solution:** Strategic reference recording + AI voice cloning.

### 1.2 Character Voice Matrix
| Character | Base Voice | Pitch Shift | Speed | Style |
| :--- | :--- | :--- | :--- | :--- |
| Protagonist | Natural | 0% | 1.0x | Curious |
| Mentor | Natural | -5% | 0.9x | Calm/Wise |
| Narrator | Natural | +3% | 1.1x | Professional |
| Temp Characters | Modified | Variable | Variable | Per story |

---

## 2. Reference Recording Protocol

### 2.1 Recording Requirements
| Spec | Value |
| :--- | :--- |
| Duration | 30 seconds per emotion |
| Quality | 44.1kHz / 24-bit |
| Environment | Quiet room, minimal reverb |
| Microphone | Condenser (SM7B, AT2020) |

### 2.2 Emotion Reference Checklist
```
RECORDING SESSION TEMPLATE:
□ Neutral (baseline, conversational)
□ Happy (genuine smile in voice)
□ Sad (subdued, slower)
□ Angry (controlled intensity)
□ Excited (elevated energy)
□ Whisper (intimate, quiet)
□ Tired (low energy, slower)
□ Surprised (quick inhale, raised pitch)
□ Laughing (genuine laugh mid-sentence)
□ Crying (emotional tremor)
```

### 2.3 Recording Script
```
# For each emotion, read this passage:

"I was walking through the park yesterday when I 
noticed something strange. The sky had turned purple, 
and all the birds were flying backwards. I couldn't 
believe what I was seeing. This was definitely not 
a normal Tuesday afternoon."

# 30 seconds at natural pace
```

---

## 3. GPT-SoVITS Emotion Cloning

### 3.1 Reference Organization
```
~/.moltbot/voices/
├── protagonist/
│   ├── neutral.wav
│   ├── happy.wav
│   ├── sad.wav
│   ├── angry.wav
│   ├── excited.wav
│   └── whisper.wav
├── mentor/
│   ├── calm.wav
│   └── mysterious.wav
└── narrator/
    ├── professional.wav
    └── warm.wav
```

### 3.2 Emotion Selection Logic
```python
def select_emotion_reference(character: str, emotion: str) -> str:
    """Select appropriate reference audio for synthesis."""
    
    EMOTION_MAP = {
        "protagonist": {
            "default": "neutral",
            "joy": "happy",
            "sadness": "sad",
            "anger": "angry",
            "excitement": "excited",
            "intimacy": "whisper",
        }
    }
    
    emotion_key = EMOTION_MAP.get(character, {}).get(emotion, "neutral")
    return f"~/.moltbot/voices/{character}/{emotion_key}.wav"
```

### 3.3 Script Emotion Tagging
```xml
<dialogue character="protagonist" emotion="excited">
    I finally figured it out! The automation works!
</dialogue>

<dialogue character="mentor" emotion="calm">
    I knew you could do it. Trust the process.
</dialogue>
```

---

## 4. Non-Verbal Sound Production

### 4.1 Recording Additional Sounds
```
SOUND EFFECTS TO RECORD:
□ Laugh (genuine, 3 variations)
□ Chuckle (soft laugh)
□ Sigh (relieved, frustrated, tired)
□ Gasp (surprised)
□ Hmm (thinking)
□ Uh-huh (agreement)
□ Clearing throat
□ Yawn
```

### 4.2 Insertion Points
```python
# Script with non-verbal markers
script = """
PROTAGONIST: [sigh] I've been working on this all day.
MENTOR: [hmm] Maybe try a different approach?
PROTAGONIST: [laugh] Why didn't I think of that!
"""
```

---

## 5. Character Differentiation Techniques

### 5.1 Voice Modification Stack
```python
CHARACTER_PROFILES = {
    "protagonist": {
        "pitch": 0,
        "formant": 0,
        "reverb": 0.05,
        "compression": "light"
    },
    "mentor": {
        "pitch": -3,           # Lower pitch
        "formant": -1,         # Deeper resonance  
        "reverb": 0.15,        # More ethereal
        "compression": "medium"
    },
    "narrator": {
        "pitch": +2,
        "formant": 0,
        "reverb": 0.02,        # Clean/close
        "compression": "heavy"  # Broadcast quality
    }
}
```

### 5.2 Post-Processing Pipeline
```python
def process_character_audio(audio, character: str):
    profile = CHARACTER_PROFILES[character]
    
    # Apply pitch shift
    audio = pitch_shift(audio, profile["pitch"])
    
    # Apply formant shift (timbre)
    audio = formant_shift(audio, profile["formant"])
    
    # Apply reverb
    audio = add_reverb(audio, profile["reverb"])
    
    # Apply compression
    audio = compress(audio, profile["compression"])
    
    return audio
```

---

## 6. Quality Assurance

### 6.1 Emotion Verification
*   Listen test: Does the emotion come through?
*   A/B test: Compare with professional voice actors.
*   Consistency: Same emotion sounds same across clips.

### 6.2 Character Distinction Test
*   Play clips without context.
*   Can listener identify which character?
*   Target: >90% correct identification.

---

## 7. Benchmarks

| Metric | Target |
| :--- | :--- |
| Emotion accuracy | >85% listener agreement |
| Character distinction | >90% identification |
| MOS score | >4.0 (commercial quality) |
| Reference recordings | 10 per character minimum |

---

[Back to README](../../README.md)

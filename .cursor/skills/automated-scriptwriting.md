---
name: automated-scriptwriting
description: Automated Scriptwriting Technical Encyclopedia: Moltbot Integration, Leitner-Driven Vocabulary, CLIL Story Generation, and Emotion Tagging.
---

# Skill: Automated Scriptwriting Pipeline

[Back to README](../../README.md)

Technical protocols for **100% automated** script generation using Claude/LLM orchestration, Leitner vocabulary integration, and CLIL methodology. This document defines the complete pipeline from topic selection to tagged screenplay.

---

## 1. What You Need for Full Automation

### 1.1 Required Components
| Component | Purpose | Tool |
| :--- | :--- | :--- |
| **Orchestrator** | Manages pipeline steps | Claude API / CrewAI |
| **Memory DB** | Tracks vocabulary + episodes | SQLite |
| **Vector DB** | Semantic search for stories | ChromaDB / Pinecone |
| **LLM** | Script generation | Claude 3.5 / GPT-4 |
| **Validator** | Quality checks | Custom Python |

### 1.2 Minimal Setup (M4 Mac Mini)
```bash
# Install dependencies
pip install anthropic chromadb sqlite-utils pydantic

# No GPU needed for scriptwriting!
# All processing is text-based
```

---

## 2. The Automated Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    MOLTBOT SCRIPTWRITER                      │
└─────────────────────────────────────────────────────────────┘
                              │
     ┌────────────────────────┼────────────────────────────┐
     ▼                        ▼                            ▼
┌──────────┐           ┌──────────────┐           ┌──────────────┐
│ STEP 1   │           │   STEP 2     │           │   STEP 3     │
│ Query    │ ──────▶   │   Generate   │ ──────▶   │   Validate   │
│ Memory   │           │   Script     │           │   & Tag      │
└──────────┘           └──────────────┘           └──────────────┘
     │                        │                            │
     ▼                        ▼                            ▼
  • Leitner terms          • CLIL story              • Emotion tags
  • Past episodes          • 3-part format           • Voice routing
  • Character profiles     • Dialogue                • Timing markers
```

---

## 3. Step 1: Query Memory (Leitner + RAG)

### 3.1 Get Vocabulary for Review
```python
import sqlite3
from datetime import datetime

def get_review_vocabulary(db_path: str, limit: int = 15) -> list:
    """Get vocabulary due for spaced repetition review."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT term, translation, box_level, mastery_score
    FROM leitner_vocab
    WHERE next_review <= ?
    ORDER BY box_level ASC, mastery_score ASC
    LIMIT ?
    """
    
    cursor.execute(query, (datetime.now().isoformat(), limit))
    return cursor.fetchall()
```

### 3.2 Get Related Past Episodes
```python
import chromadb

def get_related_episodes(topic: str, exclude_recent: int = 3) -> list:
    """Find similar past episodes to avoid repetition."""
    client = chromadb.Client()
    collection = client.get_collection("episodes")
    
    results = collection.query(
        query_texts=[topic],
        n_results=5
    )
    
    # Filter out recent episodes
    return [ep for ep in results if ep["days_ago"] > exclude_recent]
```

---

## 4. Step 2: Generate Script (Claude + CLIL)

### 4.1 The Master Prompt Template
```python
SCRIPT_PROMPT = """
You are a master storyteller for a Technical Educational Channel, creating immersive 
language learning content. Write a 15-minute episode script.

## CHARACTERS
- **Protagonist**: Main character, curious learner (emotion: varies)
- **Mentor**: Inner wisdom voice (emotion: calm, wise)
- **Narrator**: Professional AI narrator (emotion: neutral)

## VOCABULARY TO INCLUDE (MUST USE ALL)
{review_vocabulary}

## NEW VOCABULARY TO INTRODUCE (15-20 words)
Topic: {topic}
Target words: {new_vocabulary}

## AVOID (Already covered in recent episodes)
{excluded_themes}

## FORMAT REQUIREMENTS
- Part 1: Main story (8 min) - Full dialogue with emotions
- Part 2: Recall section (3 min markers) - Key sentences only
- Part 3: Deep dive (4 min) - Simple explanations

## OUTPUT FORMAT
```xml
<episode topic="{topic}" duration="15min" lang="en">
  <part id="1" name="story">
    <scene id="1">
      <dialogue character="protagonist" emotion="curious">
        [Text here]
      </dialogue>
      <action>Visual description for animators</action>
    </scene>
  </part>
  <part id="2" name="recall">
    <sentence id="1" vocab="workflow">
      [Key sentence with vocabulary]
    </sentence>
  </part>
  <part id="3" name="deepdive">
    <explanation vocab="workflow">
      [Simple explanation]
    </explanation>
  </part>
</episode>
```
"""
```

### 4.2 Generate with Claude API
```python
import anthropic

def generate_script(
    topic: str,
    review_vocab: list,
    new_vocab: list,
    excluded: list
) -> str:
    """Generate complete episode script."""
    
    client = anthropic.Anthropic()
    
    prompt = SCRIPT_PROMPT.format(
        topic=topic,
        review_vocabulary="\n".join(f"- {v}" for v in review_vocab),
        new_vocabulary="\n".join(f"- {v}" for v in new_vocab),
        excluded_themes="\n".join(f"- {e}" for e in excluded)
    )
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text
```

---

## 5. Step 3: Validate & Tag

### 5.1 Validation Checks
```python
from pydantic import BaseModel
from typing import List
import xml.etree.ElementTree as ET

class ScriptValidation(BaseModel):
    has_all_parts: bool
    vocabulary_coverage: float  # % of required vocab used
    emotion_tags_present: bool
    estimated_duration: float  # minutes
    character_balance: dict  # speaking time per character

def validate_script(script_xml: str, required_vocab: list) -> ScriptValidation:
    """Validate generated script meets requirements."""
    root = ET.fromstring(script_xml)
    
    # Check vocabulary coverage
    script_text = ET.tostring(root, encoding='unicode')
    used_vocab = [v for v in required_vocab if v.lower() in script_text.lower()]
    coverage = len(used_vocab) / len(required_vocab)
    
    # Check parts
    parts = root.findall(".//part")
    has_all_parts = len(parts) >= 3
    
    # Check emotions
    dialogues = root.findall(".//dialogue[@emotion]")
    emotion_tags_present = len(dialogues) > 0
    
    return ScriptValidation(
        has_all_parts=has_all_parts,
        vocabulary_coverage=coverage,
        emotion_tags_present=emotion_tags_present,
        estimated_duration=15.0,
        character_balance={}
    )
```

### 5.2 Re-generation Loop
```python
async def generate_validated_script(topic: str, max_attempts: int = 3):
    """Generate script with automatic retry if validation fails."""
    
    review_vocab = get_review_vocabulary("moltbot.db")
    new_vocab = suggest_new_vocabulary(topic, limit=20)
    excluded = get_related_episodes(topic)
    
    for attempt in range(max_attempts):
        script = generate_script(topic, review_vocab, new_vocab, excluded)
        validation = validate_script(script, review_vocab + new_vocab)
        
        if validation.vocabulary_coverage >= 0.9 and validation.has_all_parts:
            return script
        
        # Add feedback for next attempt
        print(f"Attempt {attempt+1} failed: {validation}")
    
    raise Exception("Failed to generate valid script after max attempts")
```

---

## 6. Output: Voice-Ready Script

### 6.1 Final Script Format
```xml
<episode topic="automation_basics" duration="15min" lang="en">
  <metadata>
    <new_vocabulary>workflow, pipeline, trigger, webhook, cron</new_vocabulary>
    <review_vocabulary>script, function, variable, loop, condition</review_vocabulary>
    <characters>protagonist, mentor, narrator</characters>
  </metadata>
  
  <part id="1" name="story" duration="8min">
    <scene id="1" location="office">
      <dialogue character="protagonist" emotion="frustrated" voice_model="gpt-sovits">
        I've been doing this same task every single day...
      </dialogue>
      <dialogue character="mentor" emotion="calm" voice_model="fish-speech">
        What if I told you there's a better way?
      </dialogue>
      <action>Camera zooms out to reveal mountain of papers</action>
    </scene>
  </part>
  
  <part id="2" name="recall" duration="3min">
    <sentence vocab="workflow" display_time="3s">
      A workflow automates your repetitive tasks.
    </sentence>
  </part>
  
  <part id="3" name="deepdive" duration="4min">
    <explanation vocab="workflow" level="beginner">
      Think of a workflow like a recipe. You write the steps once,
      and then the computer follows them every time.
    </explanation>
  </part>
</episode>
```

---

## 7. Full Automation Command

```python
# main.py - Run daily
async def daily_content_pipeline():
    """Generate one full episode per day."""
    
    # 1. Get today's topic from content calendar
    topic = get_next_topic()
    
    # 2. Generate script (automated)
    script = await generate_validated_script(topic)
    
    # 3. Save to database
    save_episode(script)
    
    # 4. Update Leitner (mark vocabulary as used)
    update_leitner_usage(script)
    
    # 5. Queue for voice synthesis (next step in pipeline)
    queue_for_synthesis(script)
    
    print(f"✅ Script generated for: {topic}")

# Run with: python main.py
```

---

## 8. Benchmarks

| Metric | Target |
| :--- | :--- |
| Generation time | <30 seconds |
| Vocabulary coverage | >90% |
| Validation pass rate | >80% first try |
| Human review | Optional (QA only) |

---

[Back to README](../../README.md)

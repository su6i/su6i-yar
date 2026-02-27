---
name: method-of-loci
description: Memory Palace Technical Encyclopedia: Spatial Memory Architecture, Visual Anchoring, and Animation-Based Loci Construction for Language Retention.
---

# Skill: Method of Loci (Memory Palace)

[Back to README](../../README.md)

Technical protocols for implementing the Method of Loci (Memory Palace) technique in animated educational content. This document defines standards for spatial memory encoding, visual anchor design, and integration with spaced repetition systems.

---

## 1. The Memory Palace Architecture

### 1.1 Core Principle
*   **Logic:** The brain remembers spatial locations better than abstract information.
*   **Application:** Placing vocabulary/concepts in memorable visual locations within animated scenes.

### 1.2 Palace Structure Standards
```
MEMORY PALACE HIERARCHY:
├── Palace (Series/Course)
│   ├── Room (Episode)
│   │   ├── Station (Scene)
│   │   │   ├── Object (Word/Concept)
│   │   │   └── Action (Meaning/Usage)
```

---

## 2. Visual Anchor Design

### 2.1 Anchor Types
| Type | Best For | Example |
| :--- | :--- | :--- |
| **Object** | Nouns | A glowing "automation" robot on desk |
| **Action** | Verbs | Character "running" through code |
| **Color** | Emotions | Red room for anger vocabulary |
| **Sound** | Pronunciation | Echo effect at each station |

### 2.2 Absurdity Principle
*   **Logic:** Bizarre/unusual images are remembered better.
*   **Implementation:** Exaggerated animations, impossible physics.
```python
# Example: Teaching "procrastinate"
anchor = {
    "word": "procrastinate",
    "location": "bedroom_clock",
    "visual": "Giant snail wearing clock as shell",
    "action": "Snail slowly eating TODO list",
    "absurdity_score": 0.9  # Higher = more memorable
}
```

---

## 3. Animation Integration

### 3.1 Camera Path = Memory Journey
```python
CAMERA_PATH = [
    {"station": "door", "word": "begin", "duration": 3},
    {"station": "desk", "word": "workflow", "duration": 4},
    {"station": "window", "word": "perspective", "duration": 3},
    {"station": "bookshelf", "word": "knowledge", "duration": 4},
]
# Camera follows consistent path every episode
# Viewer builds mental map over time
```

### 3.2 Consistent Room Layout
*   **Rule:** Same room layout across episodes of same series.
*   **Reason:** Allows cumulative spatial memory building.

---

## 4. Blender Implementation

### 4.1 Room Template Script
```python
import bpy

def create_memory_room():
    """Standard memory palace room with 8 stations."""
    stations = [
        ("door", (0, -5, 0)),
        ("desk", (3, -2, 0)),
        ("window", (5, 0, 1)),
        ("bookshelf", (3, 3, 0)),
        ("lamp", (0, 4, 1.5)),
        ("plant", (-3, 3, 0)),
        ("clock", (-5, 0, 2)),
        ("chair", (-3, -2, 0)),
    ]
    
    for name, loc in stations:
        bpy.ops.mesh.primitive_cube_add(location=loc)
        obj = bpy.context.active_object
        obj.name = f"station_{name}"
        obj["is_loci_station"] = True
    
    return stations
```

---

## 5. Integration with Leitner System

### 5.1 Station-Based Review
```sql
CREATE TABLE loci_stations (
    station_id TEXT PRIMARY KEY,
    room_id TEXT,
    position JSON,          -- {"x": 3, "y": -2, "z": 0}
    words_placed JSON,      -- ["workflow", "automation"]
    visit_count INTEGER,
    last_visited DATETIME
);
```

### 5.2 Review Animation
*   When word is due for review → Camera revisits that station.
*   Flash highlight effect on the object.
*   Reinforces spatial-vocabulary connection.

---

## 6. Episode Production Workflow

1. **Script Phase:** Tag vocabulary with target stations.
2. **Storyboard:** Map camera path through room.
3. **Animation:** Place visual anchors at stations.
4. **Review:** Generate "palace walkthrough" recap.

---

## 7. Benchmarks

| Metric | Target |
| :--- | :--- |
| Stations per room | 6-10 |
| Words per station | 1-2 |
| Camera dwell time | 3-5 sec |
| Retention boost | +40% vs baseline |

---

[Back to README](../../README.md)

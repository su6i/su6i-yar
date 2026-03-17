---
description: Prevent AI agents from writing duplicate functions or features that already exist in the codebase.
globs: *.py, *.js, *.ts, *.sh
---
# Strict DRY (Don't Repeat Yourself) Policy for AI Agents

**Critical Rule:** You MUST NOT write new code for a feature or utility if an implementation already exists in the project.

Before implementing ANY functional logic (especially utilities like downloaders, TTS, formatting, requests, database calls):
1. **Search the Codebase (`grep_search` or `codebase_search`):** Look for existing functions that do what you need. (e.g., if you need TTS, search for `text_to_speech`).
2. **Check the Legacy Monolith:** Specifically, check `su6i_yar.py`! Many functional features from the development bot may not have been fully migrated to `src/` modules yet. 
3. **Re-use, Don't Rebuild:** If a function exists, import it and use it. If it exists in a legacy file but belongs in a `src/` module, *migrate* the existing code entirely rather than writing a new version from scratch.
4. **Never Downgrade Features:** If an old implementation has more features (like supporting 2 models instead of 1), you MUST preserve all those features when refactoring or modularizing.

*Failure to follow this rule will result in fragmented, buggy, and bloated code which is strictly against the project architecture.*

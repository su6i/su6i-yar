import json
import os
import logging
from .config import DATA_DIR, logger

# File Paths
PERSISTENCE_FILE = os.path.join(DATA_DIR, "user_data.json")
BIRTHDAY_FILE = os.path.join(DATA_DIR, "birthdays.json")

# In-memory stores
USER_LANG = {}         # user_id -> "fa" | "en" | "fr" | "ko"
USER_DAILY_USAGE = {}  # user_id -> {"count": int, "date": str}
BIRTHDAYS = {}         # user_id -> {"month": int, "day": int, ...}
SEARCH_FILE_ID = None

def load_persistence():
    """Load user language/usage data."""
    global USER_LANG, USER_DAILY_USAGE, SEARCH_FILE_ID
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                USER_LANG = {int(k): v for k, v in data.get("user_lang", {}).items()}
                USER_DAILY_USAGE = {int(k): v for k, v in data.get("user_usage", {}).items()}
                SEARCH_FILE_ID = data.get("search_file_id")
                logger.info(f"📁 Loaded user data: {len(USER_LANG)} users")
        except Exception as e:
            logger.error(f"❌ User Data Load Error: {e}")

def load_birthdays():
    """Load birthday data."""
    global BIRTHDAYS
    if os.path.exists(BIRTHDAY_FILE):
        try:
            with open(BIRTHDAY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                BIRTHDAYS = {int(k): v for k, v in data.items()}
                logger.info(f"🎂 Loaded birthdays: {len(BIRTHDAYS)} entries")
        except Exception as e:
            logger.error(f"❌ Birthday Load Error: {e}")

def save_persistence():
    """Save user language/usage to JSON."""
    try:
        data = {
            "user_lang": USER_LANG,
            "user_usage": USER_DAILY_USAGE,
            "search_file_id": SEARCH_FILE_ID
        }
        with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"❌ User Data Save Error: {e}")

def save_birthdays():
    """Save birthdays to JSON."""
    try:
        with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
            json.dump(BIRTHDAYS, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"❌ Birthday Save Error: {e}")

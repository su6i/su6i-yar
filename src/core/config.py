import os
from dotenv import load_dotenv
from .logger import logger
import sys

# Load environment variables
load_dotenv()

# Detect Dev Mode
IS_DEV = "--dev" in sys.argv


# --- Constants & Config ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
FAL_API_KEY = os.getenv("FAL_KEY", "")

# Feature Flags
ENABLE_DOWNLOADS = True
ENABLE_FACT_CHECK = True

# Paths Standardized
DATA_DIR = os.path.expanduser("~/.su6i-yar")
STORAGE_DIR = os.path.join(DATA_DIR, "storage")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
TEMP_DIR = os.path.join(DATA_DIR, "temp")

# Amir CLI path — override with AMIR_PATH in .env
AMIR_PATH = os.getenv(
    "AMIR_PATH",
    str(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "amir-cli", "amir")))
)

# Ensure all directories exist
for d in [DATA_DIR, STORAGE_DIR, LOGS_DIR, TEMP_DIR]:
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

BIRTHDAYS_FILE = "birthdays.json"
user_context = {}  # In-memory user context

# Validation
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN is missing in .env")
    exit(1)
# Access Control
ALLOWED_USERS = {
    # Admin is always allowed
}
ALLOWED_GROUPS = set()

# Global Settings
SETTINGS = {
    "download": True,
    "fact_check": True,
    "min_fc_len": 200,
    "lang": "fa",
    "admin_id": ADMIN_ID,
    "public_mode": False,
    "default_daily_limit": 10,
    "free_trial_limit": 3
}


from datetime import date
from src.core.config import SETTINGS, ALLOWED_USERS, ALLOWED_GROUPS
from src.core.database import USER_DAILY_USAGE, save_persistence

def get_user_limit(user_id: int) -> int:
    """Return daily request limit for a user."""
    # 1. Admin
    if user_id == SETTINGS["admin_id"]:
        return 1000
    
    # 2. Whitelisted User (Custom Limit)
    if user_id in ALLOWED_USERS:
        return ALLOWED_USERS[user_id].get("daily_limit", SETTINGS["default_daily_limit"])
    
    # 3. Free Trial
    return SETTINGS["free_trial_limit"]

def check_access(user_id: int, chat_id: int = None) -> tuple[bool, str]:
    """Check if user has access to use the bot. Returns (allowed, reason)."""
    admin_id = SETTINGS["admin_id"]
    
    # Admin always has unlimited access
    if user_id == admin_id:
        return True, "admin"
    
    # Check if public mode
    if SETTINGS["public_mode"]:
        return True, "public"
    
    # Whitelisted users
    if user_id in ALLOWED_USERS:
        # Check group restriction (if in a group)
        if chat_id and chat_id < 0:  # Negative ID = group
            if ALLOWED_GROUPS and chat_id not in ALLOWED_GROUPS:
                return False, "group_not_allowed"
        return True, "whitelisted"
    
    # Non-whitelisted users get free trial (check if they still have quota)
    has_quota, remaining = check_daily_limit(user_id)
    if has_quota:
        return True, "free_trial"
    
    return False, "trial_expired"

def check_daily_limit(user_id: int) -> tuple[bool, int]:
    """Check if user has remaining daily requests. Returns (allowed, remaining)."""
    # Get user's limit
    user_limit = get_user_limit(user_id)
    
    # Admin has unlimited
    if user_limit >= 999:
        return True, 999
    
    # Get today's usage
    today = str(date.today())
    if user_id not in USER_DAILY_USAGE or USER_DAILY_USAGE[user_id]["date"] != today:
        USER_DAILY_USAGE[user_id] = {"count": 0, "date": today}
    
    current_count = USER_DAILY_USAGE[user_id]["count"]
    remaining = user_limit - current_count
    
    return remaining > 0, remaining

def increment_daily_usage(user_id: int) -> int:
    """Increment user's daily usage count. Returns remaining requests."""
    today = str(date.today())
    if user_id not in USER_DAILY_USAGE or USER_DAILY_USAGE[user_id]["date"] != today:
        USER_DAILY_USAGE[user_id] = {"count": 0, "date": today}
    USER_DAILY_USAGE[user_id]["count"] += 1
    save_persistence()
    
    # Return remaining
    user_limit = get_user_limit(user_id)
    return user_limit - USER_DAILY_USAGE[user_id]["count"]

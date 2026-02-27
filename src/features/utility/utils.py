from telegram import KeyboardButton, ReplyKeyboardMarkup
from src.core.config import SETTINGS, ALLOWED_USERS
from src.core.access import check_daily_limit, get_user_limit
from src.utils.text_tools import get_msg

def get_status_text(user_id: int) -> str:
    """Generate localized status message for a user."""
    dl_s = get_msg("dl_on", user_id) if SETTINGS["download"] else get_msg("dl_off", user_id)
    fc_s = get_msg("fc_on", user_id) if SETTINGS["fact_check"] else get_msg("fc_off", user_id)
    info = get_msg("status_fmt", user_id).format(dl=dl_s, fc=fc_s)
    
    # Add user quota info
    has_quota, remaining = check_daily_limit(user_id)
    limit = get_user_limit(user_id)
    
    # Localized User Type
    if user_id == SETTINGS["admin_id"]:
        user_type = get_msg("user_type_admin", user_id)
    elif user_id in ALLOWED_USERS:
        user_type = get_msg("user_type_member", user_id)
    else:
        user_type = get_msg("user_type_free", user_id)
        
    quota_info = (
        f"\n━━━━━━━━━━━━━━\n"
        f"👤 **{get_msg('status_label_user', user_id)}:** `{user_id}`\n"
        f"🏷️ **{get_msg('status_label_type', user_id)}:** {user_type}\n"
        f"📊 **{get_msg('status_label_quota', user_id)}:** {remaining}/{limit}"
    )
    return info + quota_info

def get_main_keyboard(user_id):
    """Generate a compact 3-row keyboard for all user types"""
    is_admin = user_id == SETTINGS["admin_id"]
    
    # Row 1: Core Features (Status, Help, Price)
    # Note: price button key might need check in MESSAGES
    # In su6i_yar.py it was get_msg("btn_price", user_id) - assumed to be there or added later? 
    # Let's assume it exists or use a fallback. 
    # Actually, looking at MESSAGES in text_tools.py earlier, I didn't see explicit "btn_price".
    # But usually get_msg returns key if not found.
    # In the original file logic, it was using "btn_price".
    
    row1 = [
        KeyboardButton(get_msg("btn_status", user_id)),
        KeyboardButton(get_msg("btn_help", user_id)),
        KeyboardButton(get_msg("btn_price", user_id) if get_msg("btn_price", user_id) != "btn_price" else "💰 Price") 
    ]
    
    # Row 2: Dynamic row (Voice + Admin)
    row2 = [KeyboardButton(get_msg("btn_voice", user_id))]
    if is_admin:
        # For admin, we mix Voice with the most critical toggle
        row2.append(KeyboardButton(get_msg("btn_dl", user_id)))
        row2.append(KeyboardButton(get_msg("btn_fc", user_id)))
        # Note: 'Stop Bot' is moved to row2 for admin to stay within 3 rows
        row2.append(KeyboardButton(get_msg("btn_stop", user_id)))
    
    # Row 3: Languages (Always at bottom)
    row3 = [
        KeyboardButton("🇮🇷 فارسی"), 
        KeyboardButton("🇺🇸 English"), 
        KeyboardButton("🇫🇷 Français"), 
        KeyboardButton("🇰🇷 한국어")
    ]
    
    kb = [row1, row2, row3]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

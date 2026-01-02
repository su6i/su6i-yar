import os
import re
import sys
import asyncio
import logging
import subprocess
import signal
import warnings
# Suppress Pydantic V1 warning on Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core._api.deprecation")

from pathlib import Path
from dotenv import load_dotenv
import argparse
import io
import json
import uuid
import urllib.parse
import urllib.request
import edge_tts
import html
import httpx
from bs4 import BeautifulSoup
import time

# Telegram Imports
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import AsyncCallbackHandler

# ==============================================================================
# CONFIGURATION & SETUP
# ==============================================================================

# 1. Logging Setup with Custom Formatter
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and clean output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Shorten format for cleaner output
        log_fmt = "%(levelname)s - %(name)s - %(message)s"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartBot")
logger.propagate = False  # Prevent logs from double-appearing in console

# Add colored formatter to console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())
logger.handlers = [console_handler]
logger.setLevel(logging.INFO)

# Suppress verbose logs from httpx and google_genai
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("google_genai._api_client").setLevel(logging.ERROR)


# 2. Argument Parsing for Environment
parser = argparse.ArgumentParser(description="Su6i Yar Bot")
parser.add_argument("--dev", action="store_true", help="Run in development mode")
args = parser.parse_args()
IS_DEV = args.dev

# 2. Environment Variables
load_dotenv()
if args.dev:
    logger.info("🛠️ Running in DEVELOPMENT MODE")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_DEV") or os.getenv("TELEGRAM_BOT_TOKEN")
else:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 3. Global Settings
SETTINGS = {
    "download": True,
    "fact_check": False,
    "min_fc_len": 200,
    "lang": "fa",
    "admin_id": int(TELEGRAM_CHAT_ID) if TELEGRAM_CHAT_ID else 0,
    "public_mode": False,  # If True, anyone can use. If False, only whitelist.
    "default_daily_limit": 10,  # Default daily AI requests for whitelisted users
    "free_trial_limit": 3,  # Free requests for non-whitelisted users
}

# Rate Limiting (per user)
RATE_LIMIT = {}  # user_id -> last_request_time

# Market Data Caching (tgju.org)
MARKET_DATA_CACHE = None
MARKET_DATA_TIMESTAMP = 0
MARKET_CACHE_TTL = 300  # 5 minutes
RATE_LIMIT_SECONDS = 5  # Minimum seconds between AI requests per user

# Access Control: Whitelist
# Format: user_id -> {"daily_limit": int, "requests_today": int, "last_reset": date}
ALLOWED_USERS = {
    # Admin is always allowed with unlimited access
}

# Access Control: Allowed Groups (empty = all groups if public_mode is True)
ALLOWED_GROUPS = set()  # Add group IDs here, e.g., {-1001234567890}

# Daily request tracking
from datetime import date
USER_DAILY_USAGE = {}  # user_id -> {"count": int, "date": str}
USER_LANG = {}         # user_id -> "fa" | "en" | "fr" | "ko"
SEARCH_FILE_ID = None  # Persistent telegram file_id for the status GIF

PERSISTENCE_FILE = "user_data.json"

def save_persistence():
    """Save user languages and daily usage to file."""
    try:
        data = {
            "user_lang": USER_LANG,
            "user_usage": USER_DAILY_USAGE,
            "search_file_id": SEARCH_FILE_ID
        }
        with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Persistence Save Error: {e}")

def load_persistence():
    """Load user languages and daily usage from file."""
    global USER_LANG, USER_DAILY_USAGE
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert string keys back to int if needed (JSON keys are always strings)
                USER_LANG = {int(k): v for k, v in data.get("user_lang", {}).items()}
                USER_DAILY_USAGE = {int(k): v for k, v in data.get("user_usage", {}).items()}
                global SEARCH_FILE_ID
                SEARCH_FILE_ID = data.get("search_file_id")
                logger.info(f"📁 Loaded persistence: {len(USER_LANG)} users, {len(USER_DAILY_USAGE)} usage, GIF: {'Exists' if SEARCH_FILE_ID else 'None'}")
        except Exception as e:
            logger.error(f"Persistence Load Error: {e}")

# Initial load
load_persistence()

def get_user_limit(user_id: int) -> int:
    """Get user's daily request limit."""
    admin_id = SETTINGS["admin_id"]
    if user_id == admin_id:
        return 999  # Unlimited for admin
    
    # Whitelisted users get their custom limit or default
    if user_id in ALLOWED_USERS:
        return ALLOWED_USERS[user_id].get("daily_limit", SETTINGS["default_daily_limit"])
    
    # Non-whitelisted users get free trial limit
    return SETTINGS["free_trial_limit"]

def extract_text(response) -> str:
    """Safely extract text from LangChain response, handling both string and list content."""
    if not response or not hasattr(response, 'content'):
        return ""
    
    content = response.content
    if isinstance(content, list):
        # Handle list-based content (Multimodal/Grounding parts from Gemini)
        return "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content]).strip()
    
    return str(content).strip()

def smart_split(text, header="", max_len=1024, overflow_prefix="... ادامه در پیام بعدی"):
    """
    Split text into two parts: a caption (max_len) and overflow_text.
    Uses HTML formatting for stability.
    Returns (final_caption_html, overflow_raw_text)
    """
    if not text:
        return header, ""
        
    # Split by paragraphs
    paragraphs = text.split('\n\n')
    current_caption_raw = ""
    overflow_text_raw = ""
    overflow_started = False
    
    for para in paragraphs:
        if overflow_started:
            overflow_text_raw += ("\n\n" if overflow_text_raw else "") + para
        else:
            potential = (current_caption_raw + "\n\n" if current_caption_raw else "") + para
            
            # Test length with HTML escaping
            test_caption_html = header + "\n\n" + html.escape(potential) + "\n\n<i>" + html.escape(overflow_prefix) + "</i>"
            
            if len(test_caption_html) <= max_len:
                current_caption_raw = potential
            else:
                if not current_caption_raw:
                    # Hard split if first paragraph is too long
                    allowed = max_len - len(header) - len(overflow_prefix) - 30
                    current_caption_raw = para[:allowed]
                    overflow_text_raw = para[allowed:]
                    overflow_started = True
                else:
                    overflow_started = True
                    overflow_text_raw = para
                    
    final_caption_html = header + (("\n\n" + html.escape(current_caption_raw)) if current_caption_raw else "")
    if overflow_text_raw:
        final_caption_html += "\n\n<i>" + html.escape(overflow_prefix) + "</i>"
        
    return final_caption_html, overflow_text_raw

async def detect_language(text: str) -> str:
    """Detect language of text. Prioritizes local regex for FA/KO, then AI."""
    if not text:
        return "fa"
        
    # Heuristic for Persian/Arabic
    if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
        return "fa"
    
    # Heuristic for Korean (Hangul)
    if re.search(r'[\uAC00-\uD7AF\u1100-\u11FF]', text):
        return "ko"
        
    # Use AI for EN vs FR or others
    try:
        # Use a very short, fast prompt
        chain = get_smart_chain(grounding=False)
        response = await chain.ainvoke(f"Return only the 2-letter ISO code for this text's language: {text[:100]}")
        content = extract_text(response)
        code = content.lower()[:2]
        return LANG_ALIASES.get(code, code) if code in LANG_ALIASES else code
    except:
        return "en"

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


# ==============================================================================
# CALLBACK HANDLER FOR LIVE STATUS UPDATES
# ==============================================================================

class StatusUpdateCallback(AsyncCallbackHandler):
    """Updates Telegram Status Message when AI model starts generating"""
    def __init__(self, status_msg, get_msg_func):
        self.status_msg = status_msg
        self.get_msg = get_msg_func
        self.last_model = None

    async def on_llm_start(self, serialized, prompts, **kwargs):
        """Called when LLM starts - update status with model name"""
        model_raw = "AI Model"
        
        # Extract model name from serialized data
        if "kwargs" in serialized and "model" in serialized["kwargs"]:
            model_raw = serialized["kwargs"]["model"]
        elif "name" in serialized:
            model_raw = serialized["name"]
        elif "id" in serialized:
            # Sometimes model is in id field as a list
            parts = serialized["id"]
            if isinstance(parts, list) and len(parts) > 0:
                # Last element is usually the model name
                model_raw = parts[-1]
        
        # Use exact model name (e.g., "gemini-2.5-flash")
        self.last_model = model_raw
        
        try:
            user_id = getattr(self.status_msg, 'chat_id', 0)
            text = get_msg("analyzing_model", user_id).format(model=model_raw)
            await self.status_msg.edit_text(text, parse_mode='Markdown')
            logger.info(f"📡 Trying model: {model_raw}")
        except Exception as e:
            logger.debug(f"Status update failed: {e}")
            pass  # Ignore flood wait or edit errors

# User Preferences (In-Memory)
USER_LANG = {}
LEARN_LOCK = asyncio.Lock()  # Prevent concurrent /learn requests to avoid API 429s
LEARN_WAITERS = []           # List of {user_id, status_msg, lang} for live queue updates
# Fallback Tenor Animation (Direct link)
SEARCH_GIF_FALLBACK = "https://media1.tenor.com/m/kI2WQAiG3KAAAAAC/waiting.gif"

# ... (Localization Dictionary MESSAGES is unchanged, skipping for brevity) ...


class FallbackErrorCallback(AsyncCallbackHandler):
    """Log errors when a model fails in the fallback chain"""
    async def on_llm_error(self, error: Exception, **kwargs):
        logger.warning(f"⚠️ Model Failure in Chain: {error}")

async def cmd_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ Command /check triggered")
    msg = update.message
    if not msg: return
    user_id = update.effective_user.id
    lang = USER_LANG.get(user_id, "fa")

    # Access Control Check
    allowed, reason = check_access(user_id, msg.chat_id)
    if not allowed:
        await msg.reply_text(get_msg("access_denied", user_id))
        return
    
    # Daily Limit Check
    has_quota, remaining = check_daily_limit(user_id)
    if not has_quota:
        limit = get_user_limit(user_id)
        await reply_and_delete(update, context, get_msg("limit_reached", user_id).format(remaining=0, limit=limit), delay=10)
        return

    # Check if reply or arguments
    target_text = ""
    reply_target_id = msg.message_id
    
    if msg.reply_to_message:
        # Check both text and caption (for media messages)
        target_text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
        reply_target_id = msg.reply_to_message.message_id
        
    if not target_text and context.args:
        target_text = " ".join(context.args)
    
    if not target_text:
        await reply_and_delete(update, context, "⛔ Reply to a message or provide text: `/check <text>`", delay=10)
        return

    status_msg = await msg.reply_text(
        get_msg("analyzing", user_id),
        reply_to_message_id=reply_target_id
    )
    
    # Delete the command message itself if in a group
    if msg.chat_id < 0:
        await safe_delete(msg)

    response = await analyze_text_gemini(target_text, status_msg, lang, user_id=user_id)
    
    # Increment usage and get remaining
    remaining = increment_daily_usage(user_id)
    
    await smart_reply(msg, status_msg, response, user_id, lang)
    
    # Show remaining requests (skip for admin)
    if user_id != SETTINGS["admin_id"]:
        limit = get_user_limit(user_id)
        # Use simple message for quota to avoid cluttering, or just log it
        await reply_and_delete(update, context, f"📊 {remaining}/{limit} {get_msg('limit_remaining_count', user_id)}", delay=15, reply_to_message_id=status_msg.message_id)

# ==============================================================================
# LOGIC: SMART CHAIN FACTORY (LANGCHAIN)
# ==============================================================================

def get_smart_chain(grounding=True):
    """Constructs the self-healing AI model chain (8-Layer Defense)"""
    logger.info(f"⛓️ Building Smart AI Chain (Grounding: {grounding})...")
    logger.info(f"🔑 Keys found: Gemini={'Yes' if GEMINI_API_KEY else 'No'}, DeepSeek={'Yes' if DEEPSEEK_API_KEY else 'No'}")
    
    defaults = {"google_api_key": GEMINI_API_KEY, "temperature": 0.3}

    # 1. Gemini 3 Flash Preview (Primary - Experimental/Fast)
    primary = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview", 
        **defaults
    )
    
    # Define Fallbacks in Order (Power > Speed)
    fallback_models = [
        "gemini-2.5-pro",                   # 2. Powerhouse
        "gemini-2.5-flash",                 # 3. Balanced
        "gemini-2.5-flash-test",            # 4. Preview variant
        "gemini-2.5-flash-lite",            # 5. Cost-effective
        "gemini-2.0-flash",                 # 6. Reliable Legacy
        "gemini-2.0-flash-lite",            # 7. Fast Legacy
        "gemini-1.5-flash"                  # 8. Ultimate Safety Net
    ]
    
    # Create Google Runnables
    runnables = [ChatGoogleGenerativeAI(model=m, **defaults) for m in fallback_models]
    
    # 8. DeepSeek (Ultimate Fallback)
    if DEEPSEEK_API_KEY:
        deepseek = ChatOpenAI(
            base_url="https://api.deepseek.com", 
            model="deepseek-chat", 
            api_key=DEEPSEEK_API_KEY,
            temperature=0.3
        )
        runnables.append(deepseek)
        
    return primary.with_fallbacks(runnables)

# Global Cache for Details (Simple Dict: user_id -> detail_text)
# In production, use a TTL cache or database.
LAST_ANALYSIS_CACHE = {}

import time

def check_rate_limit(user_id):
    """Check if user can make AI request. Returns True if allowed."""
    now = time.time()
    last_request = RATE_LIMIT.get(user_id, 0)
    if now - last_request < RATE_LIMIT_SECONDS:
        return False
    RATE_LIMIT[user_id] = now
    return True

async def refresh_learn_queue():
    """Update all waiting users about their position in the queue."""
    for index, waiter in enumerate(LEARN_WAITERS):
        try:
            user_id = waiter["user_id"]
            msg_obj = waiter["status_msg"]
            
            # Get the current slide progress if it's the active one
            prog = waiter.get("progress", "")
            base_text = get_msg("learn_designing", user_id)
            if prog:
                base_text = f"{base_text} ({prog})"
            
            # Position Label:
            # If index is 0, they are the 'active' one (Position 1 in queue)
            # but we only show the label to make it clear why it's not starting yet.
            pos_label = get_msg("learn_queue_pos", user_id).format(pos=index + 1)
            
            await msg_obj.edit_caption(
                caption=f"🪄 {base_text}{pos_label}",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass

async def cmd_learn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Educational tutor: 3 variations with images, definitions, and sentence audio."""
    msg = update.effective_message
    user_id = update.effective_user.id
    
    # Ensure User Lang is initialized immediately
    if user_id not in USER_LANG:
        USER_LANG[user_id] = "fa"
    user_lang = USER_LANG[user_id]
    
    # Check Daily Limit
    if not check_daily_limit(user_id):
        await msg.reply_text(get_msg("learn_quota_exceeded", user_id))
        return

    # Extract target text and language
    target_text = ""
    target_lang = user_lang # Default to user's app language
    
    if msg.reply_to_message:
        target_text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
        if context.args:
            lang_arg = context.args[0].lower()
            if lang_arg in LANG_ALIASES:
                target_lang = LANG_ALIASES[lang_arg]
    elif context.args:
        # Check if first arg is a language code/alias
        lang_arg = context.args[0].lower()
        if lang_arg in LANG_ALIASES:
            target_lang = LANG_ALIASES[lang_arg]
            target_text = " ".join(context.args[1:])
        else:
            target_text = " ".join(context.args)

    if not target_text:
        await msg.reply_text(get_msg("learn_no_text", user_id))
        return

    # 3. Queue Management & Status Message
    original_msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id
    
    global SEARCH_FILE_ID
    try:
        status_msg = await msg.reply_animation(
            animation=SEARCH_FILE_ID or SEARCH_GIF_FALLBACK,
            caption=f"🪄 {get_msg('learn_designing', user_id)}",
            reply_to_message_id=original_msg_id,
            parse_mode=ParseMode.MARKDOWN
        )
        # Capture file_id for next time
        if not SEARCH_FILE_ID and status_msg.animation:
            SEARCH_FILE_ID = status_msg.animation.file_id
            save_persistence()
            logger.info(f"🚀 Captured and cached Search GIF file_id: {SEARCH_FILE_ID}")
    except Exception as e:
        logger.error(f"GIF status failed: {e}")
        # Clear cache if it failed, maybe the file_id is invalid
        if SEARCH_FILE_ID:
            SEARCH_FILE_ID = None
            save_persistence()
        status_msg = await msg.reply_text(get_msg("learn_designing", user_id), reply_to_message_id=original_msg_id)
    
    # Add to waiters and refresh positions
    waiter_entry = {"user_id": user_id, "status_msg": status_msg, "lang": user_lang}
    LEARN_WAITERS.append(waiter_entry)
    await refresh_learn_queue()

    # 4. Wait for Global Lock
    async with LEARN_LOCK:
        try:
            await refresh_learn_queue()
        except: pass
            
        try:
            # 4. Educational AI Call
            logger.info(f"🤖 Step 1: Requesting deep educational content from AI in {target_lang}...")
            lang_name = LANG_NAMES.get(target_lang, target_lang)
            explanation_lang = "Persian" if user_lang == "fa" else ("English" if user_lang == "en" else ("French" if user_lang == "fr" else "Korean"))
            chain = get_smart_chain(grounding=False)
            
            educational_prompt = (
                f"SYSTEM ROLE: You are a linguistic tutor. Your student's interface language is '{explanation_lang}'.\n\n"
                f"CORE TASK: The student wants to learn about the concept: '{target_text}' in '{target_lang}'.\n\n"
                f"STRICT LANGUAGE MAPPING (FAILURE TO COMPLY IS UNACCEPTABLE):\n"
                f"1. 'word': MUST be the translation of '{target_text}' into '{target_lang}'.\n"
                f"2. 'sentence': MUST be a complete example sentence ONLY in '{target_lang}'.\n"
                f"3. 'meaning': MUST be a definition/explanation written ONLY in '{explanation_lang}'.\n"
                f"4. 'translation': MUST be the translation of the 'sentence' (field #2) ONLY into '{explanation_lang}'.\n\n"
                f"IMPORTANT: Even if the input '{target_text}' is in '{explanation_lang}' or any other language, you MUST provide ALL explanations (meaning/translation) in '{explanation_lang}'.\n\n"
                f"GRAMMAR RULES (CRITICAL):\n"
                f"- For ALL nouns in '{target_lang}', you MUST provide the word in EXACTLY THREE formats separated by slashes: Indefinite Singular / Definite Singular / Plural (e.g., 'un livre / le livre / des livres' for French, or 'a book / the book / books' for English).\n"
                f"- This 'Triple Format' MUST be used as the 'word' field in the JSON.\n"
                f"- Include phonetics for the '{target_lang}' word.\n\n"
                f"Return ONLY valid JSON in this structure:\n"
                f"{{\n"
                f"  \"valid\": true/false,\n"
                f"  \"lang\": \"detected language of '{target_text}'\",\n"
                f"  \"lang_code\": \"ISO code\",\n"
                f"  \"dict\": \"source dictionary\",\n"
                f"  \"is_correction\": true/false,\n"
                f"  \"suggestion\": \"corrected '{target_text}' if misspelled\",\n"
                f"  \"slides\": [\n"
                f"    {{\n"
                f"      \"word\": \"[{target_lang} terms]\",\n"
                f"      \"phonetic\": \"...\",\n"
                f"      \"meaning\": \"[Explanations ONLY in {explanation_lang}]\",\n"
                f"      \"sentence\": \"[{target_lang} sentence]\",\n"
                f"      \"translation\": \"[Translation ONLY in {explanation_lang}]\",\n"
                f"      \"prompt\": \"A highly detailed English visual description for an AI image generator...\",\n"
                f"      \"keywords\": \"3-4 simple English keywords representing the scene for image search\"\n"
                f"    }},\n"
                f"    ... (exactly 3 variant objects)\n"
                f"  ]\n"
                f"}}\n"
                f"REPLY ONLY WITH JSON."
            )
            
            response = await chain.ainvoke([HumanMessage(content=educational_prompt)])
            content = extract_text(response)
            
            # Clean JSON
            if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
                
            try:
                res = json.loads(content)
                if not res.get("valid"):
                    await status_msg.edit_caption(
                        caption=get_msg("learn_word_not_found_no_suggestion", user_id).format(word=target_text),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return

                det_lang = res.get("lang", "Unknown")
                det_lang_code = res.get("lang_code", target_lang)
                det_dict = res.get("dict", "General")
                
                if res.get("is_correction"):
                    suggestion = res.get("suggestion", target_text)
                    await status_msg.edit_caption(
                        caption=get_msg("learn_word_not_found", user_id).format(word=target_text, suggestion=suggestion, lang=det_lang, dict=det_dict),
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await status_msg.edit_caption(
                        caption=get_msg("learn_searching_stats", user_id).format(word=target_text, lang=det_lang, dict=det_dict),
                        parse_mode=ParseMode.MARKDOWN
                    )

                # Extract slides
                variations = res.get("slides")
                if not variations or not isinstance(variations, list): raise ValueError("Empty slides")
                variations = variations[:3]

            except Exception:
                # Basic fallback
                translated_text = await translate_text(target_text, target_lang)
                img_prompt = await generate_visual_prompt(target_text)
                variations = [{
                    "word": translated_text,
                    "phonetic": "",
                    "meaning": get_msg("learn_fallback_meaning", user_id),
                    "sentence": "Example sentence goes here.",
                    "translation": get_msg("learn_fallback_translation", user_id),
                    "prompt": img_prompt
                }]

            # 5. Sequential Delivery (Download & Send one-by-one)
            logger.info("🎬 Starting sequential delivery to avoid timeouts...")
            
            for i, var in enumerate(variations):
                # Update progress for queue visibility
                waiter_entry["progress"] = f"{i+1}/3"
                await refresh_learn_queue()

                # If this is the start of sending real content, remove the temporary status GIF
                if i == 0 and status_msg:
                    await safe_delete(status_msg)
                    status_msg = None # Clear to avoid trying to delete again later

                if i > 0: await asyncio.sleep(3.5)
                    
                word = var.get("word", "")
                phonetic = var.get("phonetic", "")
                meaning = var.get("meaning", "")
                sentence = var.get("sentence", "")
                translation = var.get("translation", "")
                img_prompt = var.get("prompt", target_text)
                keywords = var.get("keywords", target_text)
                
                # --- Per-Slide Image Download (Pollinations -> Unsplash Fallback) ---
                image_bytes = None
                max_retries = 3 # Increased retries
                for attempt in range(max_retries + 1):
                    try:
                        if attempt > 0: await asyncio.sleep(attempt * 1.5)
                        encoded = urllib.parse.quote(img_prompt)
                        seed = int(asyncio.get_event_loop().time()) + i + (attempt * 15)
                        url = f"https://pollinations.ai/p/{encoded}?width=1024&height=1024&seed={seed}&nologo=true"
                        
                        def dl():
                            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                            # Increased timeout to 90s for reliability
                            with urllib.request.urlopen(req, timeout=90) as r: return r.read()
                        
                        image_bytes = await asyncio.to_thread(dl)
                        if image_bytes and len(image_bytes) > 5000: break # Success
                        
                        # If pollination fails on last attempt, try Unsplash
                        if attempt == max_retries:
                            logger.info(f"🛡️ Pollinations failed. Trying Unsplash Fallback for slide {i+1}...")
                            clean_keywords = urllib.parse.quote(keywords.replace(",", " "))
                            unsplash_url = f"https://source.unsplash.com/featured/1024x1024/?{clean_keywords}"
                            
                            def dl_unsplash():
                                req = urllib.request.Request(unsplash_url, headers={'User-Agent': 'Mozilla/5.0'})
                                with urllib.request.urlopen(req, timeout=30) as r: return r.read()
                            
                            image_bytes = await asyncio.to_thread(dl_unsplash)
                            if image_bytes and len(image_bytes) > 5000: break

                    except Exception as e:
                        logger.warning(f"Image {i} attempt {attempt+1} failed: {e}")
                        # Fallback to Unsplash immediately if it's a connection error from Pollinations
                        if "pollinations.ai" in str(e):
                            try:
                                logger.info(f"🛡️ Immediate Fallback to Unsplash for slide {i+1}...")
                                clean_keywords = urllib.parse.quote(keywords.replace(",", " "))
                                unsplash_url = f"https://source.unsplash.com/featured/1024x1024/?{clean_keywords}"
                                image_bytes = await asyncio.to_thread(lambda: urllib.request.urlopen(unsplash_url, timeout=30).read())
                                if image_bytes and len(image_bytes) > 5000: break
                            except: pass

                        if attempt == max_retries:
                            logger.error(f"Image {i} permanently failed after {max_retries+1} attempts.")

                try:
                    target_flag = LANG_FLAGS.get(target_lang, "🌐")
                    user_flag = LANG_FLAGS.get(user_lang, "🇮🇷")
                    
                    caption = (
                        f"💡 **{word}** {phonetic}\n"
                        f"📝 {meaning}\n\n"
                        f"{get_msg('learn_example_sentence', user_id)}\n"
                        f"{target_flag} `{sentence}`\n"
                        f"{user_flag} {translation}\n\n"
                        f"━━━━━━━━━━━━━━\n{get_msg('learn_slide_footer', user_id).format(index=i+1)}"
                    )

                    current_slide_msg = None
                    if image_bytes:
                        # Basic image validation (check for JPEG/PNG magic numbers)
                        is_valid_image = image_bytes.startswith(b'\xff\xd8') or image_bytes.startswith(b'\x89PNG')
                        
                        if is_valid_image:
                            try:
                                photo_buffer = io.BytesIO(image_bytes)
                                photo_buffer.name = f"learn_{i}.jpg"
                                current_slide_msg = await context.bot.send_photo(
                                    chat_id=msg.chat_id,
                                    photo=photo_buffer,
                                    caption=caption,
                                    parse_mode='Markdown',
                                    reply_to_message_id=original_msg_id,
                                    read_timeout=150
                                )
                            except Exception as photo_e:
                                logger.warning(f"📸 Photo send failed, falling back to message: {photo_e}")
                                # Fallback if Telegram rejects the valid-looking photo
                                current_slide_msg = await context.bot.send_message(
                                    chat_id=msg.chat_id,
                                    text=caption,
                                    parse_mode='Markdown',
                                    reply_to_message_id=original_msg_id
                                )
                        else:
                            logger.warning(f"🚫 Downloaded bytes for slide {i+1} are not a valid image. Sending text only.")
                            current_slide_msg = await context.bot.send_message(
                                chat_id=msg.chat_id,
                                text=caption,
                                parse_mode='Markdown',
                                reply_to_message_id=original_msg_id
                            )
                    else:
                        current_slide_msg = await context.bot.send_message(
                            chat_id=msg.chat_id,
                            text=caption,
                            parse_mode='Markdown',
                            reply_to_message_id=original_msg_id
                        )
                    
                    # Audio (linked to the SLIDE)
                    # 1. Target Language (Word + Sentence)
                    target_tts = f"{word}. {sentence}"
                    target_audio_buf = await text_to_speech(target_tts, target_lang)
                    
                    # 2. Interface Language (Translation)
                    trans_audio_buf = await text_to_speech(translation, user_lang)
                    
                    # 3. Merge them (Podcast Style)
                    final_audio_buf = await merge_bilingual_audio(target_audio_buf, trans_audio_buf)
                    
                    if final_audio_buf and current_slide_msg:
                        await context.bot.send_voice(
                            chat_id=msg.chat_id,
                            voice=final_audio_buf,
                            caption=f"🔊 {word}",
                            reply_to_message_id=current_slide_msg.message_id, # Link audio to its slide
                            read_timeout=120
                        )

                except Exception as item_e:
                    logger.info(f"❌ Error sending item {i+1}: {item_e}")
                    try:
                        await context.bot.send_message(
                            chat_id=msg.chat_id,
                            text=f"❌ **{word}**\nError: {item_e}",
                            reply_to_message_id=original_msg_id
                        )
                    except: pass

            if not IS_DEV:
                await safe_delete(status_msg)
            
            # FINISHED: Remove from waiters and refresh positions for others
            if waiter_entry in LEARN_WAITERS:
                LEARN_WAITERS.remove(waiter_entry)
            await refresh_learn_queue()
            
            increment_daily_usage(user_id)
            
        except Exception as e:
            logger.error(f"Learn Loop Error: {e}")
            try:
                await status_msg.edit_text(get_msg("learn_error", user_id))
            except: pass


async def analyze_text_gemini(text, status_msg=None, lang_code="fa", user_id=None):
    """Analyze text using Smart Chain Fallback"""
    # Fix: Allow analysis even if disabled in settings (controlled by caller)
    # if not SETTINGS["fact_check"]: return None


    # Map lang_code to English name for Prompt
    lang_map = {"fa": "Persian (Farsi)", "en": "English", "fr": "French"}
    target_lang = lang_map.get(lang_code, "Persian")

    try:
        logger.info(f"🧠 STARTING AI ANALYSIS ({target_lang}) for text: {text[:20]}...")
        # Language-specific labels for comparison table
        if lang_code == "fa":
            overall_status_label = "**وضعیت کلی:**"
            comparison_table_label = "**جدول مقایسه:**"
            text_claim_label = "▫️ **ادعای متن:**"
            research_label = "▫️ **مقالات:**"
            conclusion_label = "▫️ **نتیجه تحقیقات:**"
            status_label = "▫️ **وضعیت:**"
            result_label = "**نتیجه:**"
            example_conclusion1 = "تحقیقات این میزان خستگی را تأیید می‌کند"
            example_conclusion2 = "تحقیقات کاهش تمرکز را نشان می‌دهد اما درصد دقیق متفاوت است"
            example_not_specified = "در تحقیقات مشخص نشده"
        elif lang_code == "en":
            overall_status_label = "**Overall Status:**"
            comparison_table_label = "**Comparison Table:**"
            text_claim_label = "▫️ **Text Claim:**"
            research_label = "▫️ **Research Papers:**"
            conclusion_label = "▫️ **Research Findings:**"
            status_label = "▫️ **Status:**"
            result_label = "**Conclusion:**"
            example_conclusion1 = "Research confirms fatigue increases by this amount"
            example_conclusion2 = "Research shows concentration decreases but exact percentage varies"
            example_not_specified = "Not specified in research"
        else:  # French
            overall_status_label = "**Statut Global:**"
            comparison_table_label = "**Tableau de Comparaison:**"
            text_claim_label = "▫️ **Affirmation du Texte:**"
            research_label = "▫️ **Articles:**"
            conclusion_label = "▫️ **Résultats de Recherche:**"
            status_label = "▫️ **Statut:**"
            result_label = "**Conclusion:**"
            example_conclusion1 = "La recherche confirme cette augmentation de fatigue"
            example_conclusion2 = "La recherche montre une diminution de concentration mais le pourcentage exact varie"
            example_not_specified = "Non spécifié dans la recherche"
        
        prompt_text = (
            f"You are a professional Fact-Check Assistant. Answer STRICTLY in **{target_lang}** language.\n\n"
            f"Analyze the following text and provide your response in {target_lang}.\n\n"
            "CRITICAL FORMATTING RULES:\n"
            "1. Your response MUST be split into TWO parts using: |||SPLIT|||\n"
            "2. Use ✅ emoji ONLY for TRUE/VERIFIED claims\n"
            "3. Use ❌ emoji ONLY for FALSE/INCORRECT claims\n"
            "4. Use ⚠️ emoji for PARTIALLY TRUE/MISLEADING claims\n"
            "5. DO NOT use bullet points (•) or asterisks (*) - Telegram doesn't support them well\n"
            "6. Add blank lines between paragraphs for readability\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "PART 1: SUMMARY (VERY SHORT - Mobile Display)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "IMPORTANT: Keep this section VERY SHORT (max 500 words)\n"
            "RULE: If the text contains only ONE simple claim, analyze ONLY that claim. DO NOT invent 'implied' claims unless they are dangerous or misleading.\n"
            f"Format EXACTLY like this:\n\n"
            f"{overall_status_label} [✅/⚠️/❌]\n\n"
            f"{comparison_table_label}\n"
            "━━━━━━━━━━━━━━\n"
            f"{text_claim_label} 17%\n"
            f"{research_label} 17.1%\n"
            f"{conclusion_label} {example_conclusion1}\n"
            f"{status_label} ✅\n"
            "━━━━━━━━━━━━━━\n"
            f"{text_claim_label} 45%\n"
            f"{research_label} {example_not_specified}\n"
            f"{conclusion_label} {example_conclusion2}\n"
            f"{status_label} ⚠️\n"
            "━━━━━━━━━━━━━━\n"
            "(Continue for MAX 3-4 claims - each claim MUST be different!)\n\n"
            f"{result_label}\n"
            "[2-3 sentences ONLY]\n\n"
            "|||SPLIT|||\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "PART 2: DETAILED ANALYSIS (Complete)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "CRITICAL: Add blank line between EVERY paragraph for readability!\n"
            "DO NOT use bullet points (•) or asterisks (*)\n"
            "Use simple numbered lists or plain paragraphs\n\n"
            "For each claim:\n"
            "- Full scientific explanation\n"
            "- Exact references with titles and links\n"
            "- Biological/technical mechanisms\n"
            "- Detailed comparison of ALL claimed vs actual data\n"
            "- Academic sources with DOI/URLs\n\n"
            f"Text to analyze:\n{text}"
        )
        
        chain = get_smart_chain()
        logger.info(f"🚀 Invoking LangChain with 8-Layer Defense for user {user_id}...")
        
        # Add callback for live model name updates
        config = {}
        if status_msg:
            config["callbacks"] = [StatusUpdateCallback(status_msg, get_msg)]
        
        # Invoke Chain (Async) with callbacks
        try:
            # Add error logging callback (Ensure correct instantiation)
            run_config = config.copy() if config else {}
            run_config["callbacks"] = run_config.get("callbacks", []) + [FallbackErrorCallback()]
            
            response = await chain.ainvoke([HumanMessage(content=prompt_text)], config=run_config)

        except Exception as chain_error:
            logger.error(f"🚨 CRITICAL CHAIN FAILURE: Type={type(chain_error).__name__} | Msg={chain_error}")
            # Log the full traceback for deep debugging
            import traceback
            logger.error(traceback.format_exc())
            raise # Re-raise to be caught by the outer block which sends 'price_error'
        
        # Final status update with actual model name
        if status_msg:
            model_raw = response.response_metadata.get('model_name', 'gemini-2.5-flash')
            if "token_usage" in response.response_metadata:
                model_raw = "deepseek-chat"
            
            # Use model_raw directly (exact model name like "gemini-2.5-flash")
            model_name = model_raw
            
            try:
                await status_msg.edit_text(
                    get_msg("analysis_complete", user_id).format(model=model_name),
                    parse_mode='Markdown'
                )
            except Exception:
                pass
        
        logger.info(f"✅ Response from {model_name}")
        return response

    except Exception as e:
        logger.error(f"❌ SmartChain Error: {e}", exc_info=True)
        return None

# 4. Localization Dictionary
# 4. Localization Dictionary
MESSAGES = {
    "fa": {
        "welcome": (
            "👋 **سلام {name}!**\n"
            "به **Su6i Yar**، دستیار هوشمند خوش آمدید.\n\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 از منوی پایین استفاده کنید یا لینک اینستاگرام جهت دانلود بفرستید"
        ),
        "btn_status": "📊 وضعیت ربات",
        "btn_help": "🆘 راهنما",
        "btn_dl": "📥 مدیریت دانلود",
        "btn_fc": "🧠 راستی‌آزمایی",
        "btn_stop": "🛑 خاموش کردن ربات",
        "btn_voice": "🔊 صوتی",
        "btn_lang_fa": "🇮🇷 فارسی",
        "btn_lang_en": "🇺🇸 English",
        "btn_lang_fr": "🇫🇷 Français",
        "status_fmt": (
            "📊 **وضعیت لحظه‌ای سیستم**\n"
            "━━━━━━━━━━━━━━\n"
            "📥 **دانلودر:**          {dl}\n"
            "🧠 **راستی‌آزمایی:**      {fc}\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 برای تغییر از دکمه‌های زیر استفاده کنید"
        ),
        "help_msg": (
            "📚 **راهنمای کامل قابلیت‌های ربات**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **دانلودر اینستاگرام**\n"
            "لینک پست یا ریلز را بفرستید تا خودکار دانلود شود.\n"
            "▫️ اگر دانلود خودکار خاموش بود:\n"
            "`/dl [لینک]`\n\n"
            "🧠 **راستی‌آزمایی هوشمند** (`/check`)\n"
            "بررسی درستی ادعا یا تحلیل متن:\n"
            "▫️ ریپلای به پیام:\n"
            "`/check`\n"
            "▫️ یا مستقیم:\n"
            "`/check [متن شما]`\n\n"
            "🎓 **آموزش زبان** (`/learn`)\n"
            "یادگیری کلمات با تصویر و تلفظ:\n"
            "▫️ مستقیم:\n"
            "`/learn [کلمه یا جمله]`\n"
            "▫️ ریپلای روی کلمه:\n"
            "`/learn`\n\n"
            "🔊 **تبدیل متن به صوت** (`/voice`)\n"
            "▫️ خواندن متن پیام (ریپلای):\n"
            "`/voice`\n"
            "▫️ خواندن متن دلخواه:\n"
            "`/voice [متن]`\n"
            "▫️ ترجمه و خواندن (مثلاً به انگلیسی):\n"
            "`/voice en [متن]`\n"
            "*(زبان‌ها: fa, en, fr, ko)*\n\n"
            "📊 **وضعیت و سهمیه**\n"
            "مشاهده اعتبار باقی‌مانده:\n"
            "`/status`\n\n"
            "💰 **نرخ ارز و طلا**\n"
            "قیمت لحظه‌ای دلار، یورو و طلا:\n"
            "`/price`\n\n"
            "📄 **جزئیات تحلیل**\n"
            "اگر توضیحات بیشتر خواستید، روی نتیجه تحلیل ریپلای کنید:\n"
            "`/detail`\n\n"
            "━━━━━━━━━━━━━━"
        ),
        "help_msg_mono": (
            "📚 **راهنمای نسخه مونو (تست)**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **دانلودر اینستاگرام**\n"
            "```\n"
            "Link       -> Auto Download\n"
            "/dl [Link] -> Force Download\n"
            "```\n"
            "🧠 **راستی‌آزمایی**\n"
            "```\n"
            "/check        -> (Reply)\n"
            "/check [Text] -> Direct\n"
            "```\n"
            "🎓 **آموزش زبان**\n"
            "```\n"
            "/learn        -> (Reply)\n"
            "/learn [Word] -> Direct\n"
            "```\n"
            "🔊 **تبدیل متن به صوت**\n"
            "```\n"
            "/voice        -> (Reply)\n"
            "/voice [Text] -> Direct\n"
            "/voice en ... -> Translate\n"
            "```\n"
            "💰 **قیمت‌ها**\n"
            "```\n"
            "/price        -> Live Rates\n"
            "```\n"
            "📄 **جزئیات**\n"
            "```\n"
            "/detail       -> (Reply)\n"
            "```\n"
            "━━━━━━━━━━━━━━"
        ),
        "dl_on": "✅ فعال",
        "dl_off": "❌ غیرفعال",
        "fc_on": "✅ فعال",
        "fc_off": "❌ غیرفعال",
        "action_dl": "📥 وضعیت دانلود: {state}",
        "action_fc": "🧠 وضعیت راستی‌آزمایی: {state}",
        "lang_set": "🇮🇷 زبان روی **فارسی** تنظیم شد",
        "menu_closed": "❌ منو بسته شد. برای باز کردن /start بزنید",
        "only_admin": "⛔ فقط ادمین می‌تواند این کار را انجام دهد",
        "bot_stop": "🛑 ربات در حال خاموش شدن...",
        "analyzing": "🧠 در حال راستی‌آزمایی...",
        "too_short": "⚠️ متن برای تحلیل خیلی کوتاه است",
        "downloading": "📥 در حال دانلود... لطفاً صبر کنید",
        "uploading": "📤 در حال آپلود به تلگرام...",
        "err_dl": "❌ خطا در دانلود. لینک را بررسی کنید",
        "err_too_large": "🚫 فایل بزرگتر از ۵۰ مگابایت است و تلگرام اجازه ارسال آن را نمی‌دهد.",
        "err_api": "❌ خطا در ارتباط با سرور تحلیل. بعداً تلاش کنید",
        "voice_generating": "🔊 در حال ساخت فایل صوتی...",
        "voice_translating": "🌐 در حال ترجمه به {lang}...",
        "voice_caption": "🔊 نسخه صوتی",
        "voice_caption_lang": "🔊 نسخه صوتی ({lang})",
        "voice_error": "❌ خطا در ساخت فایل صوتی",
        "voice_no_text": "⛔ به یک پیام ریپلای بزنید یا ابتدا یک متن را تحلیل کنید.",
        "voice_invalid_lang": "⛔ زبان نامعتبر. زبان‌های پشتیبانی: fa, en, fr, ko",
        "access_denied": "⛔ شما دسترسی به این ربات ندارید.",
        "limit_reached": "⛔ سقف درخواست روزانه شما تمام شد ({remaining} از {limit}).",
        "remaining_requests": "📊 درخواست‌های باقی‌مانده امروز: {remaining}",
        "learn_designing": "🪄 در حال طراحی...",
        "learn_quota_exceeded": "❌ سهمیه روزانه شما تمام شده است.",
        "learn_no_text": "❌ لطفاً متن یا کلمه‌ای برای یادگیری بفرستید (مثال: /learn apple یا در پاسخ به یک پیام).",
        "learn_example_sentence": "📖 **جمله نمونه:**",
        "learn_slide_footer": "🎓 *آموزش ({index}/3)*",
        "learn_queue_pos": " (نفر {pos} در صف...)",
        "learn_word_not_found": "❌ کلمه **{word}** پیدا نشد.\nآیا منظورتان **{suggestion}** بود؟\n(منبع: {lang} - {dict})",
        "learn_word_not_found_no_suggestion": "❌ کلمه **{word}** در هیچ دیکشنری معتبری پیدا نشد. لطفاً املای آن را بررسی کنید.",
        "learn_error": "❌ خطایی در فرآیند آموزش رخ داد.",
        "learn_fallback_meaning": "ترجمه مستقیم",
        "learn_fallback_translation": "ترجمه جمله نمونه",
        "status_label_user": "کاربر",
        "status_label_type": "نوع",
        "status_label_quota": "سهمیه امروز",
        "user_type_admin": "👑 ادمین",
        "user_type_member": "✅ عضو",
        "user_type_free": "🆓 رایگان",
        "status_private_sent": "✅ وضعیت شما به صورت خصوصی ارسال شد.",
        "status_private_error": "⛔ ابتدا یک بار به @su6i\\_yar\\_bot پیام خصوصی بدهید.",
        "analyzing_model": "🧠 در حال راستی‌آزمایی با {model}...",
        "analysis_complete": "✅ راستی‌آزمایی توسط {model} تمام شد\n(در حال نهایی کردن...)",
        "analysis_header": "🧠 **راستی‌آزمایی توسط {model}**",
        "analysis_footer_note": "\n\n━━━━━━━━━━━━━━\n💡 **برای مشاهده جزئیات:**\nبه این پیام ریپلای بزنید و `/detail` بنویسید",
        "btn_price": "💰 قیمت ارز و طلا",
        "price_loading": "⏳ در حال دریافت قیمت‌های لحظه‌ای از tgju.org...",
        "price_error": "❌ خطا در دریافت قیمت‌ها از tgju.org. لطفاً دوباره تلاش کنید.",
        "price_msg": (
            "💰 **قیمت لحظه‌ای بازار (tgju.org)**\n"
            "━━━━━━━━━━━━━━\n"
            "🇺🇸 **دلار:** `{usd_tm}` تومان\n"
            "🇪🇺 **یورو:** `{eur_tm}` تومان\n"
            "🟡 **طلا ۱۸ عیار:** `{gold18_tm}` تومان\n"
            "**حباب طلای ۱۸:** `{diff_tm}`\n"
            "━━━━━━━━━━━━━━\n"
            "🌐 **انس جهانی:** `{ons}`$\n\n"
            "**طلای ۱۸ جهانی:**\n"
            "`{theoretical_tm}` تومان"
        ),
        "dl_usage_error": "⛔ لطفاً لینک اینستاگرام را بفرستید یا روی آن ریپلای کنید."
    },
    "en": {
        "welcome": (
            "👋 **Hello {name}!**\n"
            "Welcome to **Su6i Yar**, your AI assistant.\n\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 Use the menu below or send a link"
        ),
        "btn_status": "📊 Status",
        "btn_help": "🆘 Help",
        "btn_dl": "📥 Toggle Download",
        "btn_fc": "🧠 Toggle AI",
        "btn_stop": "🛑 Stop Bot",
        "btn_voice": "🔊 Voice",
        "btn_lang_fa": "🇮🇷 فارسی",
        "btn_lang_en": "🇺🇸 English",
        "btn_lang_fr": "🇫🇷 Français",
        "status_fmt": (
            "📊 **Live System Status**\n"
            "━━━━━━━━━━━━━━\n"
            "📥 **Downloader:**       {dl}\n"
            "🧠 **AI Fact-Check:**    {fc}\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 Use buttons below to toggle"
        ),
        "help_msg": (
            "📚 **Complete Bot Guide**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **Instagram Downloader:**\n"
            "   • Send Post/Reels link\n"
            "   • Auto-download in highest quality\n"
            "   • Force download: `/dl [link]`\n\n"
            "🧠 **Text Analysis (/check):**\n"
            "   • Reply to a message: /check\n"
            "   • Or directly: /check your text\n"
            "   • AI analysis + Google search\n\n"
            "🔊 **Voice Conversion (/voice):**\n"
            "   • Reply to message: /voice\n"
            "   • Or directly: /voice text\n"
            "   • Translate + speak: /voice fa text\n"
            "   • Languages: fa, en, fr, ko (kr)\n\n"
            "📄 **Analysis Details:**\n"
            "   • /detail - Get full analysis\n\n"
            "💰 **Currency & Gold (/price):**\n"
            "   • Live USD, EUR, Gold 18k rates\n"
            "   • Gold parity & market gap analysis\n\n"
            "━━━━━━━━━━━━━━"
        ),
        "help_msg_mono": (
            "📚 **Complete Bot Guide (Mono)**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **Instagram Downloader**\n"
            "```\n"
            "Link       -> Auto Download\n"
            "/dl [Link] -> Force Download\n"
            "```\n"
            "🧠 **Fact-Checking**\n"
            "```\n"
            "/check        -> (Reply)\n"
            "/check [Text] -> Direct\n"
            "```\n"
            "🎓 **Language Learning**\n"
            "```\n"
            "/learn        -> (Reply)\n"
            "/learn [Word] -> Direct\n"
            "```\n"
            "🔊 **Text to Speech**\n"
            "```\n"
            "/voice        -> (Reply)\n"
            "/voice [Text] -> Direct\n"
            "/voice en ... -> Translate\n"
            "```\n"
            "💰 **Prices**\n"
            "```\n"
            "/price        -> Live Rates\n"
            "```\n"
            "📄 **Details**\n"
            "```\n"
            "/detail       -> (Reply)\n"
            "```\n"
            "━━━━━━━━━━━━━━"
        ),
        "dl_on": "✅ Active",
        "dl_off": "❌ Inactive",
        "fc_on": "✅ Active",
        "fc_off": "❌ Inactive",
        "action_dl": "📥 Download status: {state}",
        "action_fc": "🧠 AI status: {state}",
        "lang_set": "🇺🇸 Language set to **English**",
        "menu_closed": "❌ Menu closed. Type /start to reopen",
        "only_admin": "⛔ Admin only",
        "bot_stop": "🛑 Bot is shutting down...",
        "analyzing": "🧠 Analyzing...",
        "too_short": "⚠️ Text is too short to analyze",
        "downloading": "📥 Downloading... Please wait",
        "uploading": "📤 Uploading to Telegram...",
        "err_dl": "❌ Download failed. Check the link",
        "err_too_large": "🚫 File is larger than 50MB. Telegram doesn't allow sending it via bot.",
        "err_api": "❌ AI API error. Try again later",
        "voice_generating": "🔊 Generating audio...",
        "voice_translating": "🌐 Translating to {lang}...",
        "voice_caption": "🔊 Voice version",
        "voice_caption_lang": "🔊 Voice version ({lang})",
        "voice_error": "❌ Error generating audio",
        "voice_no_text": "⛔ Reply to a message or analyze text first.",
        "voice_invalid_lang": "⛔ Invalid language. Supported: fa, en, fr, ko",
        "access_denied": "⛔ You don't have access to this bot.",
        "limit_reached": "⛔ Daily limit reached ({remaining} of {limit}).",
        "remaining_requests": "📊 Remaining requests today: {remaining}",
        "learn_designing": "🪄 Designing...",
        "learn_quota_exceeded": "❌ Daily limit reached.",
        "learn_no_text": "❌ Please provide a word or phrase (e.g., /learn apple).",
        "learn_example_sentence": "📖 **Example Sentence:**",
        "learn_slide_footer": "🎓 *Education ({index}/3)*",
        "learn_queue_pos": " (Position {pos} in queue...)",
        "learn_word_not_found": "❌ **{word}** not found.\nDid you mean **{suggestion}**?\n(Source: {lang} - {dict})",
        "learn_word_not_found_no_suggestion": "❌ Word '**{word}**' was not found in any reliable dictionary. Please check your spelling.",
        "learn_error": "❌ An error occurred during the educational process.",
        "learn_fallback_meaning": "Direct translation",
        "learn_fallback_translation": "Example sentence translation",
        "status_label_user": "User",
        "status_label_type": "Type",
        "status_label_quota": "Daily Quota",
        "user_type_admin": "👑 Admin",
        "user_type_member": "✅ Member",
        "user_type_free": "🆓 Free",
        "status_private_sent": "✅ Your status was sent privately.",
        "status_private_error": "⛔ Please send a private message to @su6i\\_yar\\_bot first.",
        "analyzing_model": "🧠 Analyzing claims with {model}...",
        "analysis_complete": "✅ Analysis by {model} completed\n(Finalizing response...)",
        "analysis_header": "🧠 **Analysis by {model}**",
        "analysis_footer_note": "\n\n━━━━━━━━━━━━━━\n💡 **For full analysis details:**\nReply to this message with `/detail`",
        "btn_price": "💰 Currency & Gold",
        "price_loading": "⏳ Fetching live rates from tgju.org...",
        "price_error": "❌ Error fetching rates from tgju.org. Please try again.",
        "price_msg": (
            "💰 **Live Market Rates (tgju.org)**\n"
            "━━━━━━━━━━━━━━\n"
            "🇺🇸 **USD:** `{usd}` Rial\n"
            "🇪🇺 **EUR:** `{eur}` Rial\n"
            "🟡 **Gold 18k:** `{gold18}` Rial\n"
            "🌐 **Global Ounce:** `{ons}`$\n"
            "━━━━━━━━━━━━━━\n"
            "⚖️ **Gold Parity Analysis:**\n"
            "Calculated Price (Ounce to 18k):\n"
            "`{theoretical}` Rial\n"
            "Market Gap: `{diff}` Rial"
        ),
        "dl_usage_error": "⛔ Please provide an Instagram link or reply to one."
    },
    "fr": {
        "welcome": (
            "👋 **Bonjour {name}!**\n"
            "Bienvenue sur **Su6i Yar**, votre assistant IA.\n\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 Utilisez le menu ou envoyez un lien"
        ),
        "btn_status": "📊 État",
        "btn_help": "🆘 Aide",
        "btn_dl": "📥 Téléchargement",
        "btn_fc": "🧠 IA",
        "btn_stop": "🛑 Arrêter",
        "btn_voice": "🔊 Voix",
        "btn_lang_fa": "🇮🇷 فارسی",
        "btn_lang_en": "🇺🇸 English",
        "btn_lang_fr": "🇫🇷 Français",
        "status_fmt": (
            "📊 **État du Système**\n"
            "━━━━━━━━━━━━━━\n"
            "📥 **Téléchargeur:**     {dl}\n"
            "🧠 **IA Fact-Check:**    {fc}\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 Utilisez les boutons pour changer"
        ),
        "help_msg": (
            "📚 **Guide Complet du Bot**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **Téléchargeur Instagram:**\n"
            "   • Envoyez un lien Post/Reels\n"
            "   • Téléchargement auto en HD\n"
            "   • Téléchargement forcé: `/dl [lien]`\n\n"
            "🧠 **Analyse Texte (/check):**\n"
            "   • Répondez à un message: /check\n"
            "   • Ou directement: /check texte\n"
            "   • Analyse IA + recherche Google\n\n"
            "🔊 **Conversion Audio (/voice):**\n"
            "   • Répondez au message: /voice\n"
            "   • Ou directement: /voice texte\n"
            "   • Traduire + parler: /voice fa texte\n"
            "   • Langues: fa, en, fr, ko (kr)\n\n"
            "📄 **Détails Analyse:**\n"
            "   • /detail - Analyse complète\n\n"
            "💰 **Devises & Or (/price):**\n"
            "   • Taux USD, EUR, Or 18k en direct\n"
            "   • Analyse de parité et écart du marché\n\n"
            "━━━━━━━━━━━━━━"
        ),
        "help_msg_mono": (
            "📚 **Guide Complet du Bot (Mono)**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **Téléchargeur Instagram**\n"
            "```\n"
            "Lien       -> Téléchargement Auto\n"
            "/dl [Lien] -> Téléchargement Forcé\n"
            "```\n"
            "🧠 **Vérification**\n"
            "```\n"
            "/check        -> (Répondre)\n"
            "/check [Text] -> Direct\n"
            "```\n"
            "🎓 **Apprentissage**\n"
            "```\n"
            "/learn        -> (Répondre)\n"
            "/learn [Mot]  -> Direct\n"
            "```\n"
            "🔊 **Synthèse Vocale**\n"
            "```\n"
            "/voice        -> (Répondre)\n"
            "/voice [Text] -> Direct\n"
            "/voice en ... -> Traduire\n"
            "```\n"
            "💰 **Prix**\n"
            "```\n"
            "/price        -> Taux en Direct\n"
            "```\n"
            "📄 **Détails**\n"
            "```\n"
            "/detail       -> (Répondre)\n"
            "```\n"
            "━━━━━━━━━━━━━━"
        ),
        "dl_on": "✅ Actif",
        "dl_off": "❌ Inactif",
        "fc_on": "✅ Actif",
        "fc_off": "❌ Inactif",
        "action_dl": "📥 Téléchargement: {state}",
        "action_fc": "🧠 IA: {state}",
        "lang_set": "🇫🇷 Langue définie sur **Français**",
        "menu_closed": "❌ Menu fermé. Tapez /start",
        "only_admin": "⛔ Admin seulement",
        "bot_stop": "🛑 Arrêt du bot...",
        "analyzing": "🧠 Analyse...",
        "too_short": "⚠️ Texte trop court pour analyser",
        "downloading": "📥 Téléchargement... Patientez",
        "uploading": "📤 Envoi vers Telegram...",
        "err_dl": "❌ Échec du téléchargement. Vérifiez le lien",
        "err_too_large": "🚫 Le fichier dépasse 50 Mo. Telegram ne permet pas l'envoi via bot.",
        "err_api": "❌ Erreur API IA. Réessayez plus tard",
        "voice_generating": "🔊 Génération audio...",
        "voice_translating": "🌐 Traduction en {lang}...",
        "voice_caption": "🔊 Version audio",
        "voice_caption_lang": "🔊 Version audio ({lang})",
        "voice_error": "❌ Erreur de génération audio",
        "voice_no_text": "⛔ Répondez à un message ou analysez d'abord.",
        "voice_invalid_lang": "⛔ Langue invalide. Supportées: fa, en, fr, ko",
        "access_denied": "⛔ Vous n'avez pas accès à ce bot.",
        "limit_reached": "⛔ Limite quotidienne atteinte ({remaining} sur {limit}).",
        "remaining_requests": "📊 Requêtes restantes aujourd'hui: {remaining}",
        "learn_designing": "🪄 Conception...",
        "learn_quota_exceeded": "❌ Limite quotidienne atteinte.",
        "learn_no_text": "❌ Veuillez fournir un mot ou une phrase (ex: /learn apple).",
        "learn_example_sentence": "📖 **Exemple de phrase:**",
        "learn_slide_footer": "🎓 **Éducation ({index}/3)**",
        "learn_searching_stats": "🔍 Recherche de **{word}** en {lang} (Source : {dict})...",
        "learn_word_not_found": "⚠️ Mot '**{word}**' introuvable. Affichage des résultats pour '**{suggestion}**' trouvé en {lang} ({dict}) à la place...",
        "learn_word_not_found_no_suggestion": "❌ Le mot '**{word}**' n'a été trouvé dans aucun dictionnaire fiable. Veuillez vérifier l'orthographe.",
        "learn_error": "❌ Une erreur est survenue pendant le processus éducatif.",
        "learn_fallback_meaning": "Traduction directe",
        "learn_fallback_translation": "Traduction de la phrase d'exemple",
        "status_label_user": "Utilisateur",
        "status_label_type": "Type",
        "status_label_quota": "Quota Journalier",
        "user_type_admin": "👑 Admin",
        "user_type_member": "✅ Membre",
        "user_type_free": "🆓 Gratuit",
        "status_private_sent": "✅ Votre état a été envoyé en privé.",
        "status_private_error": "⛔ Veuillez d'abord envoyer un message privé à @su6i\\_yar\\_bot.",
        "analyzing_model": "🧠 Analyse des affirmations avec {model}...",
        "analysis_complete": "✅ Analyse par {model} terminée\n(Finalisation de la réponse...)",
        "analysis_header": "🧠 **Analyse par {model}**",
        "analysis_footer_note": "\n\n━━━━━━━━━━━━━━\n💡 **Pour les détails de l'analyse:**\nRépondez à ce message avec `/detail`",
        "btn_price": "💰 Devises & Or",
        "price_loading": "⏳ Récupération des taux en direct de tgju.org...",
        "price_error": "❌ Erreur lors de la récupération des taux de tgju.org. Veuillez réessayer.",
        "price_msg": (
            "💰 **Taux du Marché en Direct (tgju.org)**\n"
            "━━━━━━━━━━━━━━\n"
            "🇺🇸 **USD:** `{usd}` Rial\n"
            "🇪🇺 **EUR:** `{eur}` Rial\n"
            "🟡 **Or 18k:** `{gold18}` Rial\n"
            "🌐 **Once Mondiale:** `{ons}`$\n"
            "━━━━━━━━━━━━━━\n"
            "⚖️ **Analyse de la Parité de l'Or:**\n"
            "Prix calculé (Once à 18k):\n"
            "`{theoretical}` Rial\n"
            "Écart du Marché: `{diff}` Rial"
        ),
        "dl_usage_error": "⛔ Veuillez fournir un lien Instagram ou y répondre."
    },
    "ko": {
        "welcome": (
            "👋 **안녕하세요 {name}!**\n"
            "**Su6i Yar**, AI 비서에 오신 것을 환영합니다.\n\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 아래 메뉴를 사용하거나 링크를 보내세요"
        ),
        "btn_status": "📊 상태",
        "btn_help": "🆘 도움말",
        "btn_dl": "📥 다운로드",
        "btn_fc": "🧠 AI",
        "btn_stop": "🛑 중지",
        "btn_voice": "🔊 음성",
        "btn_lang_fa": "🇮🇷 فارسی",
        "btn_lang_en": "🇺🇸 English",
        "btn_lang_fr": "🇫🇷 Français",
        "btn_lang_ko": "🇰🇷 한국어",
        "status_fmt": (
            "📊 **시스템 상태**\n"
            "━━━━━━━━━━━━━━\n"
            "📥 **다운로더:**     {dl}\n"
            "🧠 **AI 팩트체크:**  {fc}\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 버튼을 눌러 변경하세요"
        ),
        "help_msg": (
            "📚 **봇 가이드**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **인스타그램 다운로더:**\n"
            "   • 포스트/릴스 링크 전송\n"
            "   • 최고 화질 자동 다운로드\n"
            "   • 강제 다운로드: `/dl [링크]`\n\n"
            "🧠 **텍스트 분석 (/check):**\n"
            "   • 메시지에 답장: /check\n"
            "   • 또는 직접: /check 텍스트\n"
            "   • AI 분석 + 구글 검색\n\n"
            "🔊 **음성 변환 (/voice):**\n"
            "   • 메시지에 답장: /voice\n"
            "   • 또는 직접: /voice 텍스트\n"
            "   • 번역 + 말하기: /voice fa 텍스트\n"
            "   • 언어: fa, en, fr, ko (kr)\n\n"
            "📄 **분석 상세:**\n"
            "   • /detail - 전체 분석\n\n"
            "━━━━━━━━━━━━━━"
        ),
        "help_msg_mono": (
            "📚 **봇 가이드 (Mono)**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **인스타그램 다운로더**\n"
            "```\n"
            "링크       -> 자동 다운로드\n"
            "/dl [링크] -> 강제 다운로드\n"
            "```\n"
            "🧠 **팩트체크**\n"
            "```\n"
            "/check        -> (답장)\n"
            "/check [텍스트] -> 직접\n"
            "```\n"
            "🎓 **언어 학습**\n"
            "```\n"
            "/learn        -> (답장)\n"
            "/learn [단어] -> 직접\n"
            "```\n"
            "🔊 **텍스트 음성 변환**\n"
            "```\n"
            "/voice        -> (답장)\n"
            "/voice [텍스트] -> 직접\n"
            "/voice en ... -> 번역\n"
            "```\n"
            "💰 **가격**\n"
            "```\n"
            "/price        -> 실시간 환율\n"
            "```\n"
            "📄 **상세정보**\n"
            "```\n"
            "/detail       -> (답장)\n"
            "```\n"
            "━━━━━━━━━━━━━━"
        ),
        "dl_on": "✅ 활성화",
        "dl_off": "❌ 비활성화",
        "fc_on": "✅ 활성화",
        "fc_off": "❌ 비활성화",
        "action_dl": "📥 다운로드 상태: {state}",
        "action_fc": "🧠 AI 상태: {state}",
        "lang_set": "🇰🇷 **한국어**로 설정되었습니다",
        "menu_closed": "❌ 메뉴가 닫혔습니다. /start를 입력하세요",
        "only_admin": "⛔ 관리자 전용",
        "bot_stop": "🛑 봇을 중지합니다...",
        "analyzing": "🧠 분석 중...",
        "too_short": "⚠️ 분석하기에 텍스트가 너무 짧습니다",
        "downloading": "📥 다운로드 중... 잠시만 기다려주세요",
        "uploading": "📤 텔레그램에 업로드 중...",
        "err_dl": "❌ 다운로드 실패. 링크를 확인하세요",
        "err_too_large": "🚫 파일이 50MB를 초과합니다. 텔레그램 봇은 50MB 이상의 파일을 보낼 수 없습니다.",
        "err_api": "❌ AI API 오류. 나중에 다시 시도하세요",
        "voice_generating": "🔊 오디오 생성 중...",
        "voice_translating": "🌐 {lang}에 번역 중...",
        "voice_caption": "🔊 음성 버전",
        "voice_caption_lang": "🔊 음성 버전 ({lang})",
        "voice_error": "❌ 오디오 생성 오류",
        "voice_no_text": "⛔ 메시지에 답장하거나 먼저 텍스트를 분석하세요.",
        "voice_invalid_lang": "⛔ 지원되는 언어: fa, en, fr, ko",
        "access_denied": "⛔ 이 봇에 접근 권한이 없습니다.",
        "limit_reached": "⛔ 일일 한도에 도달했습니다 ({remaining}/{limit}).",
        "remaining_requests": "📊 오늘 남은 요청: {remaining}",
        "learn_designing": "🪄 디자인 중...",
        "learn_quota_exceeded": "❌ 일일 한도에 도달했습니다.",
        "learn_no_text": "❌ 단어나 문장을 입력해주세요 (예: /learn apple).",
        "learn_example_sentence": "📖 **예문:**",
        "learn_slide_footer": "🎓 *학습 ({index}/3)*",
        "learn_queue_pos": " (대기 순서 {pos}번...)",
        "learn_word_not_found": "❌ **{word}** 을(를) 찾을 수 없습니다.\n혹시 **{suggestion}** 을(를) 찾으시나요?\n(출처: {lang} - {dict})",
        "learn_word_not_found_no_suggestion": "❌ **{word}** 단어를 신뢰할 수 있는 사전에서 찾을 수 없습니다. 철자를 확인해 주세요.",
        "learn_error": "❌ 교육 과정 중 오류가 발생했습니다.",
        "learn_fallback_meaning": "직역",
        "learn_fallback_translation": "예문 번역",
        "status_label_user": "사용자",
        "status_label_type": "유형",
        "status_label_quota": "일일 사용량",
        "user_type_admin": "👑 관리자",
        "user_type_member": "✅ 멤버",
        "user_type_free": "🆓 무료",
        "status_private_sent": "✅ 상태가 비공개로 전송되었습니다.",
        "status_private_error": "⛔ 먼저 @su6i\\_yar\\_bot으로 개인 메시지를 보내주세요.",
        "analyzing_model": "🧠 {model}(으)로 분석 중...",
        "analysis_complete": "✅ {model} 분석 완료\n(응답 준비 중...)",
        "analysis_header": "🧠 **{model}의 분석 결과**",
        "analysis_footer_note": "\n\n━━━━━━━━━━━━━━\n💡 **전체 분석 상세 정보:**\n이 메시지에 `/detail`로 답장하세요",
        "btn_price": "💰 환율 및 금 시세",
        "price_loading": "⏳ tgju.org에서 실시간 시세를 가져오는 중...",
        "price_error": "❌ tgju.org에서 시세를 가져오는 중 오류가 발생했습니다. 다시 시도해 주세요.",
        "price_msg": (
            "💰 **실시간 시장 시세 (tgju.org)**\n"
            "━━━━━━━━━━━━━━\n"
            "🇺🇸 **미국 달러 (USD):** `{usd}` 리알\n"
            "🇪🇺 **유로 (EUR):** `{eur}` 리알\n"
            "🟡 **18k 금:** `{gold18}` 리알\n"
            "🌐 **국제 금 온스:** `{ons}`$\n"
            "━━━━━━━━━━━━━━\n"
            "⚖️ **금 시세 분석:**\n"
            "계산된 가격 (온스 당 18k):\n"
            "`{theoretical}` 리알\n"
            "시장 차이: `{diff}` 리알"
        ),
        "dl_usage_error": "⛔ 인스타그램 링크를 보내거나 답장하세요."
    }
}

def get_msg(key, user_id=None):
    """Retrieve localized message based on User ID or Global Settings"""
    # 1. Determine user's current language
    lang = "fa"
    if user_id:
        if user_id in USER_LANG:
            lang = USER_LANG[user_id]
        else:
            # First interaction via command? Initialize default
            USER_LANG[user_id] = "fa"
            lang = "fa"
    else:
        lang = SETTINGS.get("lang", "fa")
    
    # 2. Validation & Fallback Logic
    if lang not in MESSAGES: 
        lang = "fa"
    
    # Priority: User Lang Key -> English Key -> Farsi Key -> Empty String
    target_dict = MESSAGES.get(lang, MESSAGES["fa"])
    if key in target_dict:
        return target_dict[key]
    
    # Fallback to English if key missing in target lang
    if key in MESSAGES["en"]:
        return MESSAGES["en"][key]
        
    # Fallback to Farsi as ultimate default
    return MESSAGES["fa"].get(key, "")

# ==============================================================================
# HELPERS: CLEANUP & ERROR REPORTING
# ==============================================================================

async def schedule_countdown_delete(context, chat_id: int, message_id: int, user_message_id: int, 
                                   original_text: str, total_seconds: int = 60, parse_mode: str = 'Markdown'):
    """
    Updates message with countdown timer and deletes after time expires.
    Shows countdown every 10 seconds.
    """
    intervals = [50, 40, 30, 20, 10]  # Show countdown at these seconds remaining
    
    elapsed = 0
    for remaining in intervals:
        if remaining < total_seconds:
            # Calculate how long to sleep until this interval
            sleep_time = (total_seconds - remaining) - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                elapsed += sleep_time
            
            try:
                countdown_text = f"⏱️ {remaining}s\n\n{original_text}"
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=countdown_text,
                    parse_mode=parse_mode
                )
            except Exception as e:
                pass  # Message might be already deleted or edited
    
    # Final sleep before deletion
    await asyncio.sleep(10)
    
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
    
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=user_message_id)
    except Exception:
        pass

async def safe_delete(message):
    """Safely delete a message without crashing on BadRequest"""
    if not message: return
    try:
        await message.delete()
    except Exception:
        pass

async def reply_with_countdown(update: Update, context, text: str, delay: int = 60, **kwargs):
    """
    Reply to message with countdown timer (only in groups).
    Returns the reply message object.
    """
    msg = update.message
    if not msg:
        return None
    
    reply_msg = await msg.reply_text(text, **kwargs)
    
    # Only countdown in groups
    if msg.chat_id < 0:
        asyncio.create_task(
            schedule_countdown_delete(
                context=context,
                chat_id=msg.chat_id,
                message_id=reply_msg.message_id,
                user_message_id=msg.message_id,
                original_text=text,
                total_seconds=delay,
                parse_mode=kwargs.get('parse_mode', 'Markdown')
            )
        )
    
    return reply_msg

async def reply_and_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, delay: int = 15, **kwargs):
    """
    Sends a reply and schedules its deletion if sent in a group.
    """
    msg = update.message
    if not msg: return
    
    reply_msg = await msg.reply_text(text, **kwargs)
    
    # Disable auto-delete in DEV mode
    if IS_DEV:
        logger.info(f"🧪 [DEV] Skipping auto-deletion for msg at {reply_msg.message_id}")
        return reply_msg

    # Only auto-delete in groups (negative chat_id)
    if msg.chat_id < 0:
        # Delete Bot's Reply
        context.job_queue.run_once(
            lambda ctx: ctx.bot.delete_message(chat_id=msg.chat_id, message_id=reply_msg.message_id),
            delay
        )
        # Delete User's Command Message
        context.job_queue.run_once(
            lambda ctx: ctx.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id),
            delay
        )
    return reply_msg

async def report_error_to_admin(context: ContextTypes.DEFAULT_TYPE, user_id: int, command: str, error_msg: str):
    """
    Silently reports an error to the admin instead of spamming the group.
    """
    admin_id = SETTINGS["admin_id"]
    if not admin_id: return

    try:
        report = (
            f"❌ **Error Report**\n"
            f"👤 User: `{user_id}`\n"
            f"💻 Command: `{command}`\n"
            f"⚠️ Error: `{error_msg}`"
        )
        await context.bot.send_message(chat_id=admin_id, text=report, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to send error report to admin: {e}")

# ==============================================================================
# LOGIC: MENU & KEYBOARDS
# ==============================================================================

def get_main_keyboard(user_id):
    """Generate a compact 3-row keyboard for all user types"""
    is_admin = user_id == SETTINGS["admin_id"]
    
    # Row 1: Core Features (Status, Help, Price)
    row1 = [
        KeyboardButton(get_msg("btn_status", user_id)),
        KeyboardButton(get_msg("btn_help", user_id)),
        KeyboardButton(get_msg("btn_price", user_id))
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

async def send_welcome(update: Update):
    """Send welcome message with menu"""
    user = update.effective_user
    text = get_msg("welcome", user.id).format(name=user.first_name)
    await update.message.reply_text(
        text, 
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user.id)
    )





# ==============================================================================
# LOGIC: MARKET RATES (tgju.org)
# ==============================================================================

async def fetch_market_data():
    """Scrape USD, EUR, Gold 18k, and Ons from tgju.org with caching"""
    global MARKET_DATA_CACHE, MARKET_DATA_TIMESTAMP
    
    now = time.time()
    if MARKET_DATA_CACHE and (now - MARKET_DATA_TIMESTAMP) < MARKET_CACHE_TTL:
        logger.info("📡 Using cached market data")
        return MARKET_DATA_CACHE

    logger.info("🌐 Fetching live market data from tgju.org")
    url = "https://www.tgju.org/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Scrape data using verified selectors with fallbacks
        def get_val(selectors):
            if isinstance(selectors, str):
                selectors = [selectors]
            
            for selector in selectors:
                el = soup.select_one(selector)
                if el:
                    # Remove commas and non-numeric chars for calculation, but keep raw for display
                    raw = el.get_text(strip=True)
                    # For Euro particularly, sometimes the text has extra labels, clean it
                    if "یورو" in raw: raw = raw.replace("یورو", "").strip()
                    val = re.sub(r'[^\d.]', '', raw)
                    if val:
                        return raw, float(val)
            return "N/A", 0.0

        usd_raw, usd_val = get_val(["li#l-price_dollar_rl span span", "tr[data-market-nameslug='price_dollar_rl'] td.market-price"])
        eur_raw, eur_val = get_val([
            "li#l-price_eur span span", 
            "tr[data-market-nameslug='price_eur'] td.market-price",
            "tr[data-market-row='price_eur'] td.market-price"
        ])
        gold18_raw, gold18_val = get_val(["li#l-geram18 span span", "tr[data-market-nameslug='geram18'] td.market-price"])
        ons_raw, ons_val = get_val(["li#l-ons span span", "tr[data-market-nameslug='ons'] td.market-price"])

        if usd_val == 0 or ons_val == 0:
            logger.warning("⚠️ Scraper returned zero for critical values. Check selectors.")
            return None

        # Calculate Theoretical Gold (18k)
        # Formula: (Ons * Dollar) / 31.1034768 * 0.750
        theoretical_val = (ons_val * usd_val) / 31.1034768 * 0.750
        diff_val = gold18_val - theoretical_val
        
        # Format helpers
        def fmt_curr(val): return f"{int(val):,}"
        def fmt_tm(val): return f"{int(val/10):,}"
        
        data = {
            "usd": usd_raw,
            "eur": eur_raw,
            "gold18": gold18_raw,
            "ons": ons_raw,
            "theoretical": fmt_curr(theoretical_val),
            "diff": ("+" if diff_val > 0 else "") + fmt_curr(diff_val),
            # Toman versions for Farsi
            "usd_tm": fmt_tm(usd_val),
            "eur_tm": fmt_tm(eur_val),
            "gold18_tm": fmt_tm(gold18_val),
            "theoretical_tm": fmt_tm(theoretical_val),
            "diff_tm": ("+" if diff_val > 0 else "") + fmt_tm(diff_val)
        }
        
        MARKET_DATA_CACHE = data
        MARKET_DATA_TIMESTAMP = now
        return data

    except Exception as e:
        logger.error(f"❌ Scraper Exception: {e}")
        return None

async def cmd_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /price command and button"""
    msg = update.message
    user_id = update.effective_user.id
    
    status_msg = await reply_and_delete(update, context, get_msg("price_loading", user_id), delay=60)
    
    data = await fetch_market_data()
    if not data:
        await status_msg.edit_text(get_msg("price_error", user_id))
        await report_error_to_admin(context, user_id, "/price", "Scraper Failure")
        return

    price_text = get_msg("price_msg", user_id).format(**data)
    await status_msg.edit_text(price_text, parse_mode='Markdown')
    
    # Auto-delete with countdown in groups
    if msg.chat_id < 0:  # Group chat
        asyncio.create_task(
            schedule_countdown_delete(
                context=context,
                chat_id=msg.chat_id,
                message_id=status_msg.message_id,
                user_message_id=msg.message_id,
                original_text=price_text,
                total_seconds=60,
                parse_mode='Markdown'
            )
        )

# ==============================================================================
# HELPERS
# ==============================================================================

async def smart_reply(msg, status_msg, response, user_id, lang="fa"):
    """Send AI response with formatted model name and /detail instruction"""
    if not response:
        await status_msg.edit_text(get_msg("err_api", user_id))
        return

    # 1. Format Model Name
    model_raw = response.response_metadata.get("model_name", "gemini-2.5-flash")
    if "token_usage" in response.response_metadata:
        model_raw = "deepseek-chat"
    
    model_map = {
        "gemini-2.5-pro": "Gemini 2.5 Pro",
        "gemini-1.5-pro": "Gemini 1.5 Pro",
        "gemini-2.5-flash": "Gemini 2.5 Flash",
        "gemini-2.0-flash": "Gemini 2.0 Flash",
        "gemini-1.5-flash": "Gemini 1.5 Flash",
        "gemini-1.5-flash-8b": "Gemini 1.5 Flash 8B",
        "deepseek-chat": "DeepSeek Chat"
    }
    model_name = model_map.get(model_raw, model_raw.replace("-", " ").title())
    
    # 2. Get Headers and Footers from Dictionary
    header = get_msg("analysis_header", user_id).format(model=model_name)
    footer = get_msg("analysis_footer_note", user_id)
    
    # 3. Parse Split (Summary vs Detail)
    full_content = extract_text(response)
    
    split_marker = "|||SPLIT|||"
    
    if split_marker in full_content:
        parts = full_content.split(split_marker, 1)
        summary_text = parts[0].strip()
        detail_text = parts[1].strip()
        
        # Cache detailed analysis
        LAST_ANALYSIS_CACHE[user_id] = f"{header}\n\n{detail_text}"
        logger.info(f"💾 Cached {len(detail_text)} chars for user {user_id}")
    else:
        # No split found - send everything as summary
        logger.warning(f"⚠️ No split marker found in response")
        summary_text = full_content
        
        no_detail_msgs = {
            "fa": "⚠️ جزئیات بیشتری در دسترس نیست",
            "en": "⚠️ No additional details available",
            "fr": "⚠️ Aucun détail supplémentaire"
        }
        LAST_ANALYSIS_CACHE[user_id] = no_detail_msgs.get(lang, no_detail_msgs["fa"])

    # 4. Construct final message
    final_text = f"{header}\n\n{summary_text}{footer}"
    
    # 5. Send (with chunking if needed)
    max_length = 4000
    if len(final_text) > max_length:
        # Chunk the message
        chunks = [final_text[i:i+max_length] for i in range(0, len(final_text), max_length)]
        for i, chunk in enumerate(chunks):
            try:
                if i == 0:
                    await status_msg.edit_text(chunk, parse_mode='Markdown')
                else:
                    await msg.reply_text(chunk, parse_mode='Markdown')
            except Exception:
                # Fallback without Markdown
                if i == 0:
                    await status_msg.edit_text(chunk, parse_mode=None)
                else:
                    await msg.reply_text(chunk, parse_mode=None)
    else:
        # Normal case
        try:
            logger.info(f"📤 [User {user_id}] Sending final {len(final_text)} chars response...")
            await status_msg.edit_text(final_text, parse_mode='Markdown')
            logger.info(f"✅ [User {user_id}] Response sent successfully.")
        except Exception as e:
            logger.warning(f"⚠️ [User {user_id}] Markdown send failed, falling back to plain text: {e}")
            await status_msg.edit_text(final_text, parse_mode=None)

# ==============================================================================
# LOGIC: INSTAGRAM DOWNLOAD (YT-DLP + COBALT FALLBACK)
# ==============================================================================

async def download_instagram_cobalt(url: str, filename: Path) -> bool:
    """Download video using Cobalt API as fallback"""
    logger.info("🛡️ Falling back to Cobalt API...")
    try:
        # List of public instances (Official + Community)
        # Strategy: Prioritize known-good community instances
        # Source: https://instances.cobalt.best & https://cobalt.directory
        instances = [
            "https://coapi.kelig.me/api/json",         # v7 style
            "https://cobalt.meowing.de",              # High reliability
            "https://cobalt.pub",                     # Community 1
            "https://api.cobalt.kwiatekmiki.pl",      # Community 2
            "https://cobalt.hyperr.net",              # Community 3
            "https://cobalt.kuba2k2.com"             # Additional Community
        ]
        
        # Enhanced headers to mimic browser
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://cobalt.tools",
            "Referer": "https://cobalt.tools/"
        }

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            # Strategy: Try each instance
            for base_url in instances:
                # Handle endpoint differences
                # v7 uses /api/json, v10 uses /
                # We try both implicitly by constructing full URLs or base
                
                # Clean base URL
                base = base_url.rstrip("/")
                if base.endswith("/api/json"):
                    api_url = base # v7 style
                else:
                    api_url = base # v10 style (often root)

                logger.info(f"🛡️ Trying Cobalt Instance: {api_url}")

                # Define Payloads (v10 vs v7)
                payloads_to_try = [
                    # v10 Syntax
                    {
                        "url": url,
                        "videoQuality": "max",
                        "audioFormat": "mp3",
                        "filenameStyle": "basic"
                    },
                    # v7 Syntax (Legacy)
                    {
                        "url": url,
                        "vCodec": "h264",
                        "vQuality": "max",
                        "aFormat": "mp3",
                        "filenamePattern": "basic"
                    }
                ]

                dl_url = None
                for i, payload in enumerate(payloads_to_try):
                    try:
                        logger.info(f"🛰️ [Cobalt] Payload {i+1} trial for {api_url}...")
                        resp = await client.post(api_url, json=payload, headers=headers)
                        if resp.status_code not in [200, 201]:
                             logger.warning(f"  > [Cobalt] Payload {i+1} HTTP {resp.status_code} Failure: {resp.text}")
                             continue
                             
                        data = resp.json()
                        if data.get("status") in ["error", "redirect"]:
                             logger.warning(f"  > [Cobalt] API level error: {data.get('text')}")
                             continue

                        dl_url = data.get("url")
                        if not dl_url and data.get("picker"):
                            dl_url = data["picker"][0]["url"]
                        
                        if dl_url:
                            logger.info(f"🔗 [Cobalt] Successfully extracted stream URL: {dl_url[:50]}...")
                            break 
                    except Exception as loop_e:
                        logger.error(f"💥 [Cobalt] Exception during payload {i+1} on {api_url}: {str(loop_e)}")
                        continue 

                if dl_url:
                    # Found a working URL from this instance!
                    logger.info(f"✅ Found working Cobalt instance: {api_url}")
                    
                    # Download File Stream
                    try:
                        logger.info("⬇️ Downloading stream from Cobalt...")
                        async with client.stream("GET", dl_url) as dl_resp:
                            dl_resp.raise_for_status()
                            with open(filename, "wb") as f:
                                async for chunk in dl_resp.aiter_bytes():
                                    f.write(chunk)
                        return True
                    except Exception as dl_e:
                        logger.error(f"Stream Download Failed: {dl_e}")
                        # Try next instance if download fails
                        continue 

        logger.error("❌ All Cobalt instances failed.")
        return False
    except Exception as e:
        logger.error(f"Cobalt Fallback Logic Failed: {e}")
        return False
async def convert_to_mac_compatible(input_path: Path) -> bool:
    """Re-encode video to H.264/AAC with yuv420p for Mac compatibility"""
    output_path = input_path.with_name(f"fixed_{input_path.name}")
    logger.info(f"🔄 Converting {input_path.name} for Mac compatibility...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "faster",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path)
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0 and output_path.exists():
            logger.info(f"✅ Conversion successful: {output_path.name}")
            # Replace original with fixed version
            input_path.unlink()
            output_path.rename(input_path)
            return True
        else:
            logger.error(f"❌ ffmpeg failed (Code {process.returncode}): {stderr.decode()[:200]}")
            if output_path.exists(): output_path.unlink()
            return False
    except Exception as e:
        logger.error(f"💥 ffmpeg Exception: {e}")
        if output_path.exists(): output_path.unlink()
        return False

async def download_instagram(url, chat_id, bot, reply_to_message_id=None):
    """Download and send video using yt-dlp with multi-stage fallback (Anonymous -> Cookies -> Cobalt)"""
    logger.info(f"🚀 [Chat {chat_id}] Initialization of Instagram download for: {url}")
    
    # Clean URL (Remove tracking parameters for better compatibility)
    if "?" in url:
        original_url = url
        url = url.split("?")[0]
        logger.info(f"🧹 URL cleaned: '{original_url}' -> '{url}'")
        
    try:
        # 1. Filename setup
        timestamp = int(asyncio.get_event_loop().time())
        filename = Path(f"insta_{timestamp}.mp4")
        info_file = Path(f"insta_{timestamp}.info.json")
        logger.debug(f"📂 Temp files initialized: {filename}, {info_file}")
        
        # 2. Command - use absolute path if in venv
        import sys
        venv_bin = Path(sys.executable).parent
        yt_dlp_path = venv_bin / "yt-dlp"
        executable = str(yt_dlp_path) if yt_dlp_path.exists() else "yt-dlp"
        logger.info(f"🛠️ Using yt-dlp executable: {executable}")
        
        cmd = [
            executable,
            "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", str(filename),
            "--write-info-json",
            "--no-playlist",
            # Remove --max-filesize to avoid silent skips with exit code 0
            url
        ]
        
        # 3. Cookies if available
        cookie_file = Path("cookies.txt")
        if cookie_file.exists():
            cmd.insert(1, str(cookie_file))
            cmd.insert(1, "--cookies")

        # 4. Run Download (1st Attempt: Anonymous)
        logger.info(f"📥 Attempt 1: Downloading {url} anonymously...")
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        # Treatment: Successful download MUST produce a file. 
        # If exit code 0 but no file, consider it a failure.
        if process.returncode != 0 or not filename.exists():
            err_msg = stderr.decode()
            out_msg = stdout.decode()
            logger.warning(f"⚠️ Attempt 1 failed (Code {process.returncode}, File: {filename.exists()}): {err_msg[:300]}")
            if out_msg: logger.debug(f"Attempt 1 stdout: {out_msg[:300]}")

            # 4.5 Attempt 2: With Browser Cookies (Safari)
            logger.info("📥 Attempt 2: Retrying with Safari cookies...")
            cmd_with_cookies = cmd[:-1] + ["--cookies-from-browser", "safari", url]
            process = await asyncio.create_subprocess_exec(
                *cmd_with_cookies, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 or not filename.exists():
                logger.warning(f"❌ Attempt 2 (Cookies) failed (Code {process.returncode}, File: {filename.exists()})")
                logger.error(f"Full stderr from Attempt 2: {stderr.decode()}")
                logger.warning("🧱 Both local yt-dlp attempts failed. Triggering Cobalt API fallback sequence...")
                
                success = await download_instagram_cobalt(url, filename)
                if not success:
                    logger.error(f"🛑 [Chat {chat_id}] All download methods exhausted for {url}")
                    return False
                logger.info(f"✨ [Chat {chat_id}] Recovery successful via Cobalt!")

        # 6. Check File Size (Final Safety Check)
        if filename.exists():
            filesize = filename.stat().st_size
            filesize_mb = filesize / 1024 / 1024
            logger.info(f"📊 Final file downloaded. Size: {filesize_mb:.2f} MB")
            
            if filesize > 50 * 1024 * 1024:
                logger.error(f"🚫 File size ({filesize_mb:.2f}MB) exceeds Telegram Bot API limit (50MB).")
                
                # Attempt 3: Try compressed resolution (720p or lower)
                if "[height<=1080]" in str(cmd):
                    logger.info("📉 Attempt 3: Retrying with lower resolution (720p)...")
                    filename.unlink()
                    cmd_720 = [executable, "-f", "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best", "-o", str(filename), "--no-playlist", url]
                    process = await asyncio.create_subprocess_exec(*cmd_720, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    await process.communicate()
                    
                    if filename.exists():
                        filesize = filename.stat().st_size
                        filesize_mb = filesize / 1024 / 1024
                        logger.info(f"📊 Compressed (720p) file size: {filesize_mb:.2f} MB")
                        if filesize <= 50 * 1024 * 1024:
                             logger.info("✅ 720p is within limits. Proceeding to send...")
                        else:
                            logger.info("📉 Attempt 4: Retrying with 480p...")
                            filename.unlink()
                            cmd_480 = [executable, "-f", "bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]/best", "-o", str(filename), "--no-playlist", url]
                            process = await asyncio.create_subprocess_exec(*cmd_480, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            await process.communicate()
                            
                            if filename.exists():
                                filesize = filename.stat().st_size
                                filesize_mb = filesize / 1024 / 1024
                                logger.info(f"📊 Compressed (480p) file size: {filesize_mb:.2f} MB")
                                if filesize <= 50 * 1024 * 1024:
                                     logger.info("✅ 480p is within limits. Proceeding to send...")
                                else:
                                     logger.error("🚫 Even 480p is too large.")
                                     filename.unlink()
                                     if info_file.exists(): info_file.unlink()
                                     return "TOO_LARGE"
                            else:
                                logger.error("❓ 480p download failed to produce a file.")
                                return False
                    else:
                        logger.error("❓ 720p download failed to produce a file.")
                        return False
                
                else:
                    # Still too big or already tried 720
                    filename.unlink()
                    if info_file.exists(): info_file.unlink()
                    return "TOO_LARGE"
        else:
            logger.error(f"❓ Download appeared successful but file '{filename}' is missing on disk.")
            return False

        # 5. Extract caption from info.json
        original_caption = ""
        if info_file.exists():
            try:
                import json
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                original_caption = info.get('description', '') or info.get('title', '') or ''
                info_file.unlink()  # Cleanup
            except Exception as e:
                logger.warning(f"Could not read caption: {e}")

        # 6. Build caption with smart_split
        header = f"📥 <b>Su6i Yar</b> | @su6i_yar_bot"
        caption, overflow_text = smart_split(original_caption, header=header, max_len=1024)
        
        # 6.5 Ensure Mac compatibility before sending
        if filename.exists():
            await convert_to_mac_compatible(filename)

        # 7. Send to User
        if filename.exists():
            try:
                with open(filename, "rb") as video_file:
                    video_msg = await bot.send_video(
                        chat_id=chat_id,
                        video=video_file,
                        caption=caption,
                        parse_mode='HTML',
                        reply_to_message_id=reply_to_message_id,
                        supports_streaming=True,
                        read_timeout=150,
                        write_timeout=150
                    )
                
                # Send overflow text as reply to video (multiple parts if needed)
                if overflow_text:
                    # For messages, max is 4096. No header needed for follow-up.
                    # We can use smart_split again or just chunk it.
                    remaining = overflow_text
                    while remaining:
                        chunk = remaining[:4000]
                        remaining = remaining[4000:]
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"📝 <b>ادامه کپشن:</b>\n\n{html.escape(chunk)}",
                            parse_mode='HTML',
                            reply_to_message_id=video_msg.message_id
                        )
                
                # Cleanup
                filename.unlink()
                return True
            except Exception as send_e:
                logger.error(f"Error sending video/overflow: {send_e}")
                # Try fallback without video or without caption
                return False
        return False
        
    except Exception as e:
        logger.error(f"DL Exception: {e}")
        return False

# ==============================================================================
# HANDLERS
# ==============================================================================

# ==============================================================================
# PROCESSED HANDLERS (DEBUGGING ADDED)
# ==============================================================================

async def cmd_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"🚀 Command /start triggered by {update.effective_user.id}")
    # Use reply_with_countdown for welcome message in group
    user = update.effective_user
    text = get_msg("welcome", user.id).format(name=user.first_name)
    await reply_with_countdown(update, context, text, delay=60, 
                           parse_mode='Markdown', 
                           reply_markup=get_main_keyboard(user.id))

async def cmd_close_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("❌ Command /close triggered")
    user_id = update.effective_user.id
    await reply_and_delete(update, context, get_msg("menu_closed", user_id), delay=5, reply_markup=ReplyKeyboardRemove())

async def cmd_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📊 Command /status triggered")
    msg = update.message
    user_id = update.effective_user.id
    
    dl_s = get_msg("dl_on", user_id) if SETTINGS["download"] else get_msg("dl_off", user_id)
    fc_s = get_msg("fc_on", user_id) if SETTINGS["fact_check"] else get_msg("fc_off", user_id)
    info = get_msg("status_fmt", user_id).format(dl=dl_s, fc=fc_s)
    
    # Add user quota info
    full_status = get_status_text(user_id)
    await reply_with_countdown(update, context, full_status, delay=30, parse_mode='Markdown')

async def cmd_toggle_dl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📥 Command /toggle_dl triggered")
    SETTINGS["download"] = not SETTINGS["download"]
    state = get_msg("dl_on") if SETTINGS["download"] else get_msg("dl_off")
    await reply_and_delete(update, context, get_msg("action_dl").format(state=state), delay=10)

async def cmd_toggle_fc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🧠 Command /toggle_fc triggered")
    SETTINGS["fact_check"] = not SETTINGS["fact_check"]
    state = get_msg("fc_on") if SETTINGS["fact_check"] else get_msg("fc_off")
    await reply_and_delete(update, context, get_msg("action_fc").format(state=state), delay=10)

async def cmd_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force download manual override"""
    logger.info("📥 Command /dl triggered")
    msg = update.message
    user_id = update.effective_user.id
    
    # 1. Determine Target (Link & Reply ID)
    target_link = ""
    reply_to_id = msg.message_id  # Default: reply to command
    
    if context.args:
        target_link = context.args[0]
    elif msg.reply_to_message:
        target_link = msg.reply_to_message.text or msg.reply_to_message.caption or ""
        reply_to_id = msg.reply_to_message.message_id  # Fix: Reply to original link
    
    # 2. Extract URL
    match = re.search(r'(https?://(?:www\.)?instagram\.com/\S+)', target_link)
    if match:
        target_link = match.group(1)
    
    # 3. Validate
    if "instagram.com" not in target_link:
        await reply_and_delete(update, context, get_msg("dl_usage_error", user_id))
        return

    # 4. Status Message (Auto-Delete on completion/fail)
    status_msg = await msg.reply_text(
        get_msg("downloading", user_id),
        reply_to_message_id=reply_to_id 
    )
    
    # 5. Execute Download
    try:
        success = await download_instagram(target_link, msg.chat_id, context.bot, reply_to_message_id=reply_to_id)
        if success == "TOO_LARGE":
            if not IS_DEV: await safe_delete(status_msg)
            await reply_and_delete(update, context, get_msg("err_too_large", user_id), delay=15)
        elif success:
            # Video sent successfully, cleanup status
            if not IS_DEV: await safe_delete(status_msg)
            # Cleanup command msg if in group
            if msg.chat_id < 0:
                async def del_cmd(ctx):
                    try: await ctx.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
                    except: pass
                context.job_queue.run_once(del_cmd, 1)
        else:
            if not IS_DEV: await safe_delete(status_msg)
            # Silent error to admin, generic fade-out to user
            await report_error_to_admin(context, user_id, "/dl", f"Download failed for {target_link}")
            await reply_and_delete(update, context, get_msg("err_dl", user_id), delay=10)
            
    except Exception as e:
        if not IS_DEV: await safe_delete(status_msg)
        await report_error_to_admin(context, user_id, "/dl", str(e))
        await reply_and_delete(update, context, get_msg("err_dl", user_id), delay=10)


async def cmd_stop_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != SETTINGS["admin_id"]:
        await update.message.reply_text(get_msg("only_admin"))
        return
    await update.message.reply_text(get_msg("bot_stop"), reply_markup=ReplyKeyboardRemove())
    logger.info("🛑 KILLING PROCESS WITH SIGKILL (9)")
    os.kill(os.getpid(), signal.SIGKILL)

async def global_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """MASTER HANDLER: Processes ALL text messages"""
    msg = update.message
    if not msg or not msg.text: return
    text = msg.text.strip()
    user = update.effective_user
    user_id = user.id
    
    # Ensure User Lang
    if user_id not in USER_LANG:
        USER_LANG[user_id] = "fa"
    lang = USER_LANG[user_id]

    logger.info(f"📨 Message received: '{text}' from {user.id} ({lang})")

    # --- 1. MENU COMMANDS (Check by Emoji/Start) --- 
    
    # Status
    if text.startswith("📊"):
        full_status = get_status_text(user_id)
        
        # In groups, send privately
        
        # In groups, send privately
        if msg.chat_id < 0:  # Negative ID = group
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=full_status,
                    parse_mode='Markdown'
                )
                notify = await reply_and_delete(update, context, get_msg("status_private_sent", user_id), delay=10)
            except Exception:
                # User hasn't started private chat with bot
                await reply_and_delete(update, context, get_msg("status_private_error", user_id), delay=15)
        else:
            await reply_and_delete(update, context, full_status, delay=30, parse_mode='Markdown')
        return

    # Language Switching
    if "فارسی" in text:
        USER_LANG[user_id] = "fa"
        save_persistence()
        await reply_and_delete(update, context, "✅ زبان فارسی انتخاب شد.", reply_markup=get_main_keyboard(user_id))
        return
    if "English" in text:
        USER_LANG[user_id] = "en"
        save_persistence()
        await msg.reply_text("✅ English language selected.", reply_markup=get_main_keyboard(user_id))
        logger.info(f"🇺🇸 User {user_id} switched to English")
        return
    if "Français" in text:
        USER_LANG[user_id] = "fr"
        save_persistence()
        await reply_and_delete(update, context, "✅ Langue française sélectionnée.", reply_markup=get_main_keyboard(user_id))
        return
    if "한국어" in text:
        USER_LANG[user_id] = "ko"
        save_persistence()
        await msg.reply_text("✅ 한국어가 선택되었습니다.", reply_markup=get_main_keyboard(user_id))
        return
    
    # Voice Button
    if text.startswith("🔊"):
        detail_text = LAST_ANALYSIS_CACHE.get(user_id)
        if not detail_text:
            await msg.reply_text("⛔ هیچ تحلیل ذخیره‌شده‌ای موجود نیست.")
            return
        status_msg = await msg.reply_text(get_msg("voice_generating", user_id))
        try:
            audio_buffer = await text_to_speech(detail_text, lang)
            await msg.reply_voice(voice=audio_buffer, caption="🔊 نسخه صوتی تحلیل")
            await safe_delete(status_msg)
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            await status_msg.edit_text(get_msg("voice_error", user_id))
        return
        
    # Help
    if text.startswith("ℹ️") or text.startswith("🆘"):
        # Use monospace help for all languages
        help_mono = get_msg("help_msg_mono", user_id)
        if help_mono:
            await reply_with_countdown(update, context, help_mono, delay=60, parse_mode='Markdown')
        else:
            # Fallback to standard help if mono not available
            help_text = get_msg("help_msg", user_id)
            await reply_with_countdown(update, context, help_text, delay=60, parse_mode='Markdown')
        return

    # Price Check
    if "قیمت ارز و طلا" in text or "Currency & Gold" in text or "Devises & Or" in text or "환율 및 금 시세" in text:
        await cmd_price_handler(update, context)
        return

    # Toggle DL
    if text.startswith("📥"):
        SETTINGS["download"] = not SETTINGS["download"]
        state = get_msg("dl_on", user_id) if SETTINGS["download"] else get_msg("dl_off", user_id)
        await msg.reply_text(get_msg("action_dl", user_id).format(state=state))
        return

    # Toggle FC
    if text.startswith("🧠") or "راستی‌آزمایی" in text:
        SETTINGS["fact_check"] = not SETTINGS["fact_check"]
        state = get_msg("fc_on", user_id) if SETTINGS["fact_check"] else get_msg("fc_off", user_id)
        await msg.reply_text(get_msg("action_fc", user_id).format(state=state))
        return

    # Stop (Button)
    if text.startswith("🛑") and user_id == SETTINGS["admin_id"]:
        logger.info("🛑 Stop Button Triggered")
        await msg.reply_text(get_msg("bot_stop", user_id), reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        os.kill(os.getpid(), signal.SIGKILL)
        return

    # --- 2. INSTAGRAM LINK CHECK ---
    if "instagram.com" in text:
        if not SETTINGS["download"]:
            await msg.reply_text("⚠️ " + get_msg("dl_off", user_id))
            return
            
        status_msg = await msg.reply_text(
            get_msg("downloading", user_id),
            reply_to_message_id=msg.message_id
        )
        
        success = await download_instagram(text, msg.chat_id, context.bot, msg.message_id)
        if success == "TOO_LARGE":
            await status_msg.edit_text(get_msg("err_too_large", user_id))
            if not IS_DEV: 
                async def del_msg(ctx): await safe_delete(status_msg)
                context.job_queue.run_once(del_msg, 15)
        elif success:
            if not IS_DEV: await safe_delete(status_msg)
        else:
            await status_msg.edit_text(get_msg("err_dl", user_id))
        return

    # --- 3. AI ANALYSIS (Fallback) ---
    
    if SETTINGS["fact_check"] and len(text) >= SETTINGS["min_fc_len"]:
        # Access Control Check
        allowed, reason = check_access(user_id, msg.chat_id)
        if not allowed:
            await msg.reply_text(get_msg("access_denied", user_id))
            return
        
        # Daily Limit Check
        has_quota, remaining = check_daily_limit(user_id)
        if not has_quota:
            limit = get_user_limit(user_id)
            await msg.reply_text(get_msg("limit_reached", user_id).format(remaining=0, limit=limit))
            return
        
        status_msg = await msg.reply_text(
            get_msg("analyzing", user_id),
            reply_to_message_id=msg.message_id
        )
        response = await analyze_text_gemini(text, status_msg, lang, user_id)
        
        # Increment usage and get remaining
        remaining = increment_daily_usage(user_id)
        
        await smart_reply(msg, status_msg, response, user_id, lang)
        
        # Show remaining requests (skip for admin)
        if user_id != SETTINGS["admin_id"]:
            limit = get_user_limit(user_id)
            limit = get_user_limit(user_id)
            await msg.reply_text(
                get_msg("remaining_requests", user_id).format(remaining=remaining, limit=limit),
                reply_to_message_id=status_msg.message_id
            )
        return

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

async def cmd_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches the cached detailed analysis (Zero-Cost)"""
    logger.info("🔍 Command /detail triggered")
    msg = update.message
    user_id = update.effective_user.id
    
    # Check Cache
    detail_text = LAST_ANALYSIS_CACHE.get(user_id)
    
    if not detail_text:
        await msg.reply_text("⛔ هیچ تحلیل ذخیره‌شده‌ای موجود نیست. ابتدا یک متن را تحلیل کنید.")
        return

    # Decide reply target
    reply_target_id = msg.message_id
    if msg.reply_to_message:
        reply_target_id = msg.reply_to_message.message_id

    # Smart chunking: split by paragraphs, not mid-paragraph
    max_length = 3900  # Leave some margin
    
    if len(detail_text) <= max_length:
        # Fits in one message
        try:
            await msg.reply_text(detail_text, parse_mode='Markdown', reply_to_message_id=reply_target_id)
        except Exception:
            await msg.reply_text(detail_text, parse_mode=None, reply_to_message_id=reply_target_id)
    else:
        # ... (rest of chunking logic)
        # Need to chunk - split by paragraphs
        paragraphs = detail_text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # If adding this paragraph exceeds limit, save current chunk and start new one
            if len(current_chunk) + len(para) + 2 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Send all chunks
        for i, chunk in enumerate(chunks):
            try:
                if i == 0:
                    await msg.reply_text(f"{chunk}\n\n━━━━━━━━━━━━━━\n📄 بخش {i+1} از {len(chunks)}", parse_mode='Markdown')
                else:
                    await msg.reply_text(f"📄 بخش {i+1} از {len(chunks)}\n━━━━━━━━━━━━━━\n\n{chunk}", parse_mode='Markdown')
            except Exception:
                if i == 0:
                    await msg.reply_text(f"{chunk}\n\n━━━━━━━━━━━━━━\n📄 بخش {i+1} از {len(chunks)}", parse_mode=None)
                else:
                    await msg.reply_text(f"📊 بخش {i+1} از {len(chunks)}\n━━━━━━━━━━━━━━\n\n{chunk}", parse_mode=None, reply_to_message_id=reply_target_id)
        
    # Delete command in groups
    if msg.chat_id < 0:
        await safe_delete(msg)


# TTS Voice Mapping (Standardized for edge-tts)
TTS_VOICES = {
    "fa": "fa-IR-FaridNeural",   # Persian
    "en": "en-US-GuyNeural",     # English
    "fr": "fr-FR-HenriNeural",   # French
    "ko": "ko-KR-InJoonNeural",  # Korean
    "ar": "ar-SA-HamedNeural",   # Arabic
    "de": "de-DE-ConradNeural",  # German
    "es": "es-ES-AlvaroNeural",  # Spanish
    "it": "it-IT-DiegoNeural",   # Italian
    "ja": "ja-JP-KeitaNeural",   # Japanese
    "zh": "zh-CN-YunxiNeural",   # Chinese
    "ru": "ru-RU-DmitryNeural",  # Russian
    "pt": "pt-PT-RaquelNeural",  # Portuguese
    "hi": "hi-IN-MadhurNeural",  # Hindi
}

async def text_to_speech(text: str, lang: str = "fa") -> io.BytesIO:
    """Convert text to speech using edge-tts. Returns audio as BytesIO."""
    # Ensure lang is standardized key
    lang_key = lang[:2].lower()
    
    # Try exact match, then try finding a voice for the ISO code dynamically
    voice = TTS_VOICES.get(lang_key)
    
    # If not in our internal map, try to construct a fallback or use English
    if not voice:
        # Most edge-tts voices follow [lang]-[COUNTRY]-[Name]Neural
        # But constructing them is brittle, so we prioritize the map and then English.
        voice = TTS_VOICES.get("en")
    
    # Heuristic: If text contains Persian/Arabic chars AND target lang is Persian, 
    # or if no specific voice for requested lang, ensure we use Persian if text looks like it.
    if lang_key == "fa" or lang_key not in TTS_VOICES:
        if re.search(r'[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
            voice = TTS_VOICES["fa"]
    
    # Clean text for TTS (remove markdown)
    clean_text = re.sub(r'\*\*|▫️|━+|✅|❌|⚠️|🧠|📄|💡', '', text)
    clean_text = re.sub(r'\[.*?\]', '', clean_text)  # Remove markdown links
    # Replace slashes with a double pause (two commas + pauses) for natural dictation
    clean_text = clean_text.replace(" / ", ", ... , ... ")
    clean_text = clean_text.strip()
    
    # Limit length for TTS (avoid very long audio)
    if len(clean_text) > 2000:
        clean_text = clean_text[:2000] + "..."
    
    communicate = edge_tts.Communicate(clean_text, voice)
    audio_buffer = io.BytesIO()
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
    
    audio_buffer.seek(0)
    return audio_buffer

async def merge_bilingual_audio(target_audio: io.BytesIO, trans_audio: io.BytesIO) -> io.BytesIO:
    """Merge two audio streams with a silence gap using ffmpeg."""
    import tempfile
    import os
    import subprocess
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            t_path = os.path.join(tmpdir, "target.mp3")
            tr_path = os.path.join(tmpdir, "trans.mp3")
            sil_path = os.path.join(tmpdir, "silence.mp3")
            out_path = os.path.join(tmpdir, "merged.mp3")
            
            with open(t_path, "wb") as f: f.write(target_audio.getvalue())
            with open(tr_path, "wb") as f: f.write(trans_audio.getvalue())
            
            # Generate 1 sec of silence
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", 
                "-t", "1", "-q:a", "9", sil_path
            ], capture_output=True, check=True)
            
            # Concat: Target -> Silence -> Translation
            cmd = [
                "ffmpeg", "-y",
                "-i", t_path, "-i", sil_path, "-i", tr_path,
                "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
                "-map", "[out]", "-acodec", "libmp3lame", "-b:a", "64k", out_path
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            
            if os.path.exists(out_path):
                with open(out_path, "rb") as f:
                    return io.BytesIO(f.read())
    except Exception as e:
        logger.warning(f"⚠️ merge_bilingual_audio failed (likely missing ffmpeg): {e}. Falling back to single-language audio.")
        
    return target_audio # Fallback to just the target language audio

# Language code mapping for /voice command
LANG_ALIASES = {
    "fa": "fa", "farsi": "fa", "persian": "fa", "فارسی": "fa",
    "en": "en", "english": "en", "انگلیسی": "en",
    "fr": "fr", "french": "fr", "français": "fr", "فرانسوی": "fr",
    "ko": "ko", "kr": "ko", "korean": "ko", "한국어": "ko", "کره‌ای": "ko",
    "ar": "ar", "arabic": "ar", "عربی": "ar",
    "de": "de", "german": "de", "آلمانی": "de",
    "es": "es", "spanish": "es", "اسپانیایی": "es",
    "it": "it", "italian": "it", "ایتالیایی": "it",
    "ja": "ja", "japanese": "ja", "ژاپنی": "ja",
    "zh": "zh", "chinese": "zh", "چینی": "zh",
    "ru": "ru", "russian": "ru", "روسی": "ru",
    "tr": "tr", "turkish": "tr", "ترکی": "tr",
    "pt": "pt", "portuguese": "pt", "پرتغالی": "pt",
    "hi": "hi", "hindi": "hi", "هندی": "hi"
}

LANG_NAMES = {
    "fa": "فارسی", "en": "انگلیسی", "fr": "فرانسوی", "ko": "کره‌ای",
    "ar": "عربی", "de": "آلمانی", "es": "اسپانیایی", "it": "ایتالیایی",
    "ja": "ژاپنی", "zh": "چینی", "ru": "روسی", "tr": "ترکی",
    "pt": "پرتغالی", "hi": "هندی"
}

LANG_FLAGS = {
    "fa": "🇮🇷", "en": "🇺🇸", "fr": "🇫🇷", "ko": "🇰🇷"
}

async def translate_text(text: str, target_lang: str) -> str:
    """Translate text to target language using Gemini"""
    lang_name = LANG_NAMES.get(target_lang, "English")
    
    try:
        chain = get_smart_chain(grounding=False)
        prompt = f"Translate the following text to {lang_name}. Only output the translation, no explanations:\n\n{text}"
        response = await chain.ainvoke([HumanMessage(content=prompt)])
        return extract_text(response)
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text  # Return original if translation fails

async def generate_visual_prompt(text: str) -> str:
    """Generate a short English visual prompt for an image representing the text"""
    try:
        chain = get_smart_chain(grounding=False)
        prompt = f"Generate a short, descriptive English visual prompt (single sentence, no style words) representing the core meaning of this text: '{text}'"
        response = await chain.ainvoke([HumanMessage(content=prompt)])
        return extract_text(response).replace('"', '').replace("'", "")
    except Exception as e:
        logger.error(f"Visual prompt generation error: {e}")
        return "abstract conceptual representation"  # Safe default



async def cmd_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send voice version of replied message or last analysis.
    Usage: /voice [language]
    Examples: /voice, /voice en, /voice english, /voice فارسی
    """
    logger.info("🔊 Command /voice triggered")
    msg = update.message
    user_id = update.effective_user.id
    user_lang = USER_LANG.get(user_id, "fa")
    
    # Check for language argument
    explicit_target = None
    if context.args:
        lang_arg = context.args[0].lower()
        if lang_arg in LANG_ALIASES:
            explicit_target = LANG_ALIASES[lang_arg]
        # If not a lang alias, we assume it's direct text input later
    
    # Priority 1: Check if replied to a message
    target_text = ""
    reply_target_id = msg.message_id
    if msg.reply_to_message:
        target_text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
        reply_target_id = msg.reply_to_message.message_id
    
    # Priority 2: Check for direct text input
    if not target_text and context.args:
        if context.args[0].lower() in LANG_ALIASES:
            if len(context.args) > 1:
                target_text = " ".join(context.args[1:])
        else:
            target_text = " ".join(context.args)
    
    # Priority 3: Check cache
    if not target_text:
        target_text = LAST_ANALYSIS_CACHE.get(user_id, "")
        # If from cache, we might not have a good reply target, use command
        reply_target_id = msg.message_id 
    
    if not target_text:
        await reply_and_delete(update, context, get_msg("voice_no_text", user_id), delay=10)
        return

    # Delete command in groups
    if msg.chat_id < 0:
        await safe_delete(msg)

    # Decide target language and translation need
    if explicit_target:
        # User explicitly asked for a specific language -> Translate if needed
        target_lang = explicit_target
        # We assume the source text is usually in the user's interface language for translation purposes,
        # but the translation logic itself handles any source.
        # Actually, let's detect source to be sure if translation is needed.
        source_lang = await detect_language(target_text)
        need_translation = target_lang != source_lang
    else:
        # No language specified -> Use the text's natural language (no translation)
        target_lang = await detect_language(target_text)
        need_translation = False
    
    try:
        # 1. Translate if needed
        if need_translation:
            status_msg = await context.bot.send_message(
                chat_id=msg.chat_id,
                text=get_msg("voice_translating", user_id).format(lang=LANG_NAMES.get(target_lang, target_lang)),
                reply_to_message_id=reply_target_id
            )
            translated_text = await translate_text(target_text, target_lang)
            await status_msg.edit_text(get_msg("voice_generating", user_id))
            target_text = translated_text
            voice_reply_to = reply_target_id
        else:
            voice_reply_to = reply_target_id
            
        # 2. Convert to speech
        audio_buffer = await text_to_speech(target_text, target_lang)
        
        # 3. Build caption with smart_split
        lang_name = LANG_NAMES.get(target_lang, target_lang)
        if need_translation:
            header = f"🎙️ <b>دوبله ({lang_name}):</b>"
            overflow_title = "ادامه دوبله"
        else:
            header = f"🔊 <b>نسخه صوتی ({lang_name}):</b>"
            overflow_title = "ادامه متن"
            
        caption, overflow_text = smart_split(target_text, header=header, max_len=1024)
        
        # 4. Send Voice
        voice_msg = await context.bot.send_voice(
            chat_id=msg.chat_id,
            voice=audio_buffer,
            caption=caption,
            parse_mode='HTML',
            reply_to_message_id=voice_reply_to,
            read_timeout=90
        )
        
        # 5. Send overflow parts
        if overflow_text:
            remaining = overflow_text
            while remaining:
                chunk = remaining[:4000]
                remaining = remaining[4000:]
                await context.bot.send_message(
                    chat_id=msg.chat_id,
                    text=f"📝 <b>{overflow_title}:</b>\n\n{html.escape(chunk)}",
                    parse_mode='HTML',
                    reply_to_message_id=voice_msg.message_id
                )
        
        if 'status_msg' in locals():
            if not IS_DEV: await safe_delete(status_msg)
            
    except Exception as e:
        logger.error(f"Voice Error: {e}")
        await report_error_to_admin(context, user_id, "/voice", str(e))
        error_msg = get_msg("err_ai", user_id) if 'user_id' in locals() else "خطایی رخ داد."
        if 'status_msg' in locals():
            if not IS_DEV: await safe_delete(status_msg)
        
        await reply_and_delete(update, context, error_msg, delay=10)


def main():
    if not TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env")
        return

    print("🚀 Starting SmartBot Core...")
    from telegram.ext import JobQueue
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .concurrent_updates(True)
        .job_queue(JobQueue())  # Enable JobQueue for countdown timers
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("dl", cmd_download_handler))
    app.add_handler(CommandHandler("download", cmd_download_handler))
    app.add_handler(CommandHandler("start", cmd_start_handler))
    app.add_handler(CommandHandler("help", cmd_start_handler)) # Reuse start for help
    app.add_handler(CommandHandler("close", cmd_close_handler))
    app.add_handler(CommandHandler("status", cmd_status_handler))
    app.add_handler(CommandHandler("toggle_dl", cmd_toggle_dl_handler))
    app.add_handler(CommandHandler("toggle_fc", cmd_toggle_fc_handler))
    app.add_handler(CommandHandler("price", cmd_price_handler))
    app.add_handler(CommandHandler("p", cmd_price_handler))
    app.add_handler(CommandHandler("check", cmd_check_handler))
    app.add_handler(CommandHandler("detail", cmd_detail_handler))
    app.add_handler(CommandHandler("voice", cmd_voice_handler))  # TTS Voice
    app.add_handler(CommandHandler("learn", cmd_learn_handler))
    app.add_handler(CommandHandler("l", cmd_learn_handler))
    app.add_handler(CommandHandler("t", cmd_learn_handler))  # /t is for /learn
    app.add_handler(CommandHandler("translate", cmd_learn_handler))
    app.add_handler(CommandHandler("edu", cmd_learn_handler))
    app.add_handler(CommandHandler("education", cmd_learn_handler))
    app.add_handler(CommandHandler("stop", cmd_stop_bot_handler))
    
    # All Messages (Text)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), global_message_handler))

    print("✅ Bot is Polling...")
    app.run_polling(
        allowed_updates=["message", "callback_query"],  # Only listen to needed updates
        drop_pending_updates=True,  # Ignore old messages on restart
        close_loop=False  # Allow graceful shutdown
    )

if __name__ == "__main__":
    main()

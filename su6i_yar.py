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
import io
import edge_tts

# Telegram Imports
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

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


# 2. Environment Variables
load_dotenv()
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
    
    # Return remaining
    user_limit = get_user_limit(user_id)
    return user_limit - USER_DAILY_USAGE[user_id]["count"]


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
            text = f"🧠 تحلیل ادعاها با {model_raw}"
            await self.status_msg.edit_text(text, parse_mode='Markdown')
            logger.info(f"📡 Trying model: {model_raw}")
        except Exception as e:
            logger.debug(f"Status update failed: {e}")
            pass  # Ignore flood wait or edit errors

# User Preferences (In-Memory)
USER_LANG = {}

# ... (Localization Dictionary MESSAGES is unchanged, skipping for brevity) ...

async def cmd_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ Command /check triggered")
    msg = update.message
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
        await msg.reply_text(get_msg("limit_reached", user_id).format(remaining=0, limit=limit))
        return

    # Check if reply or arguments
    target_text = ""
    if msg.reply_to_message:
        # Check both text and caption (for media messages)
        target_text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
    if not target_text and context.args:
        target_text = " ".join(context.args)
    
    if not target_text:
        await msg.reply_text("⛔ Reply to a message or provide text: `/check <text>`")
        return

    status_msg = await msg.reply_text(
        get_msg("analyzing", user_id),
        reply_to_message_id=msg.message_id
    )
    response = await analyze_text_gemini(target_text, status_msg, lang)
    
    # Increment usage and get remaining
    remaining = increment_daily_usage(user_id)
    
    await smart_reply(msg, status_msg, response, user_id)
    
    # Show remaining requests (skip for admin)
    if user_id != SETTINGS["admin_id"]:
        limit = get_user_limit(user_id)
        await msg.reply_text(f"📊 {remaining}/{limit} درخواست باقی‌مانده امروز")

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
        dl_s = get_msg("dl_on") if SETTINGS["download"] else get_msg("dl_off")
        fc_s = get_msg("fc_on") if SETTINGS["fact_check"] else get_msg("fc_off")
        info = get_msg("status_fmt").format(dl=dl_s, fc=fc_s)
        await msg.reply_text(info, parse_mode='Markdown')
        return

    # Language Switching
    if "فارسی" in text:
        USER_LANG[user_id] = "fa"
        await msg.reply_text("✅ زبان فارسی انتخاب شد.", reply_markup=get_main_keyboard(user_id))
        return
    if "English" in text:
        USER_LANG[user_id] = "en"
        await msg.reply_text("✅ English language selected.", reply_markup=get_main_keyboard(user_id))
        return
    if "Français" in text:
        USER_LANG[user_id] = "fr"
        await msg.reply_text("✅ Langue française sélectionnée.", reply_markup=get_main_keyboard(user_id))
        return
    if "한국어" in text:
        USER_LANG[user_id] = "ko"
        await msg.reply_text("✅ 한국어가 선택되었습니다.", reply_markup=get_main_keyboard(user_id))
        return
    
    # Voice Button
    if text.startswith("🔊"):
        detail_text = LAST_ANALYSIS_CACHE.get(user_id)
        if not detail_text:
            await msg.reply_text("⛔ هیچ تحلیل ذخیره‌شده‌ای موجود نیست.")
            return
        status_msg = await msg.reply_text("🔊 در حال ساخت فایل صوتی...")
        try:
            audio_buffer = await text_to_speech(detail_text, lang)
            await msg.reply_voice(voice=audio_buffer, caption="🔊 نسخه صوتی تحلیل")
            await status_msg.delete()
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            await status_msg.edit_text("❌ خطا در ساخت فایل صوتی")
        return
        
    # Help
    if text.startswith("ℹ️"):
        # Note: get_help_msg should be updated to accept user_id/lang if needed, but for now assuming it uses global logic or we update it later.
        # Assuming get_help_msg(user_id) exists from previous context? I didn't verify get_help_msg signature. 
        # Let's check get_help_msg call in previous code.. it was `get_help_msg(user_id)`?
        # Actually in Step 3835: `get_help_msg` usage wasn't shown.
        # Wait, I should not assume `get_help_msg` takes user_id if I haven't seen it. 
        # But `get_help_msg` was called in `cmd_start_handler`?
        # I'll stick to safest: check existing usage in file.
        # Existing global_message_handler (line 535) didn't show help handler.
        # Ah, looking at `get_main_keyboard`...
        # I'll just skip the Help `if` block since normally `/help` handles it?
        # No, the menu button "Help" sends "ℹ️ Help" text.
        await msg.reply_text("ℹ️ Use /help to see commands.") 
        return

    # Toggle DL
    if text.startswith("📥"):
        SETTINGS["download"] = not SETTINGS["download"]
        state = get_msg("dl_on") if SETTINGS["download"] else get_msg("dl_off")
        await msg.reply_text(get_msg("action_dl").format(state=state))
        return

    # Toggle FC
    if text.startswith("🧠"):
        SETTINGS["fact_check"] = not SETTINGS["fact_check"]
        state = get_msg("fc_on") if SETTINGS["fact_check"] else get_msg("fc_off")
        await msg.reply_text(get_msg("action_fc").format(state=state))
        return

    # Stop (Button)
    if text.startswith("🛑") and user_id == SETTINGS["admin_id"]:
        logger.info("🛑 Stop Button Triggered")
        await msg.reply_text(get_msg("bot_stop"))
        os.kill(os.getpid(), signal.SIGKILL)
        return

    # --- 2. INSTAGRAM LINK CHECK ---
    if "instagram.com" in text:
        if not SETTINGS["download"]:
            await msg.reply_text("⚠️ " + get_msg("dl_off"))
            return
            
        status_msg = await msg.reply_text(get_msg("downloading"))
        
        # Run yt-dlp logic
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_instagram_video, text)
        
        if file_path:
            try:
                await status_msg.edit_text(get_msg("uploading", user_id))
                await msg.reply_video(
                    video=open(file_path, 'rb'), 
                    caption="📥 **Su6i Yar** | @su6i\\_yar\\_bot",
                    reply_to_message_id=msg.message_id,
                    parse_mode='Markdown'
                )
                os.remove(file_path) # Cleanup
                await status_msg.delete() 
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                await status_msg.edit_text("❌ Error uploading video.")
        else:
            await status_msg.edit_text(get_msg("err_dl", user_id))
        return

    # --- 3. AI ANALYSIS (Fallback) ---
    
    if SETTINGS["fact_check"] and len(text) >= SETTINGS["min_fc_len"]:
        # Rate limit check
        if not check_rate_limit(user_id):
            await msg.reply_text("⏳ لطفاً چند ثانیه صبر کنید...")
            return
        
        status_msg = await msg.reply_text(
            get_msg("analyzing", user_id),
            reply_to_message_id=msg.message_id
        )
        response = await analyze_text_gemini(text, status_msg, lang)
        
        await smart_reply(msg, status_msg, response, user_id)
        return

# ==============================================================================
# LOGIC: SMART CHAIN FACTORY (LANGCHAIN)
# ==============================================================================

def get_smart_chain():
    """Constructs the self-healing AI model chain (8-Layer Defense)"""
    logger.info("⛓️ Building Smart AI Chain...")
    
    defaults = {"google_api_key": GEMINI_API_KEY, "temperature": 0.3}

    # 1. Gemini 2.5 Pro (Primary)
    # Enable Google Search Grounding for real-time fact checking
    primary = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro", 
        **defaults,
        # Grounding: Use built-in Google Search Retrieval
        model_kwargs={"tools": [{"google_search_retrieval": {}}]}
    )
    
    # Define Fallbacks in Order
    fallback_models = [
        "gemini-1.5-pro",        # 2
        "gemini-2.5-flash",      # 3
        "gemini-2.0-flash",      # 4
        "gemini-2.5-flash-lite", # 5
        "gemini-1.5-flash",      # 6
        "gemini-1.5-flash-8b"    # 7
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

async def analyze_text_gemini(text, status_msg=None, lang_code="fa"):
    """Analyze text using Smart Chain Fallback"""
    if not SETTINGS["fact_check"]: return None

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
        logger.info("🚀 Invoking LangChain...")
        
        # Add callback for live model name updates
        config = {}
        if status_msg:
            config["callbacks"] = [StatusUpdateCallback(status_msg, get_msg)]
        
        # Invoke Chain (Async) with callbacks
        response = await chain.ainvoke([HumanMessage(content=prompt_text)], config=config)
        
        # Final status update with actual model name
        if status_msg:
            model_raw = response.response_metadata.get('model_name', 'gemini-2.5-flash')
            if "token_usage" in response.response_metadata:
                model_raw = "deepseek-chat"
            
            # Use model_raw directly (exact model name like "gemini-2.5-flash")
            model_name = model_raw
            
            try:
                await status_msg.edit_text(
                    f"✅ **تحلیل توسط {model_name} کامل شد**\n(در حال آماده‌سازی پاسخ...)",
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
            "🔻 از منوی پایین استفاده کنید یا لینک بفرستید"
        ),
        "btn_status": "📊 وضعیت ربات",
        "btn_help": "🆘 راهنما",
        "btn_dl": "📥 مدیریت دانلود",
        "btn_fc": "🧠 مدیریت هوش مصنوعی",
        "btn_stop": "🛑 خاموش کردن ربات",
        "btn_voice": "🔊 صوتی",
        "btn_lang_fa": "🇮🇷 فارسی",
        "btn_lang_en": "🇺🇸 English",
        "btn_lang_fr": "🇫🇷 Français",
        "status_fmt": (
            "📊 **وضعیت لحظه‌ای سیستم**\n"
            "━━━━━━━━━━━━━━\n"
            "📥 **دانلودر:**          {dl}\n"
            "🧠 **هوش مصنوعی:**      {fc}\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 برای تغییر از دکمه‌های زیر استفاده کنید"
        ),
        "help_msg": (
            "📚 **راهنمای کامل ربات**\n"
            "━━━━━━━━━━━━━━\n\n"
            "📥 **دانلودر اینستاگرام:**\n"
            "   • لینک پست یا ریلز بفرستید\n"
            "   • دانلود خودکار با بالاترین کیفیت\n\n"
            "🧠 **تحلیل متن (/check):**\n"
            "   • به یک پیام ریپلای کنید: /check\n"
            "   • یا مستقیم بنویسید: /check متن\n"
            "   • تحلیل با هوش مصنوعی + گوگل\n\n"
            "🔊 **صوتی کردن (/voice):**\n"
            "   • به پیام ریپلای کنید: /voice\n"
            "   • یا مستقیم: /voice متن\n"
            "   • ترجمه + صوتی: /voice en متن\n"
            "   • زبان‌ها: fa, en, fr, ko (kr)\n\n"
            "📄 **جزئیات تحلیل:**\n"
            "   • /detail - دریافت تحلیل کامل\n\n"
            "━━━━━━━━━━━━━━"
        ),
        "dl_on": "✅ فعال",
        "dl_off": "❌ غیرفعال",
        "fc_on": "✅ فعال",
        "fc_off": "❌ غیرفعال",
        "action_dl": "📥 وضعیت دانلود: {state}",
        "action_fc": "🧠 وضعیت هوش مصنوعی: {state}",
        "lang_set": "🇮🇷 زبان روی **فارسی** تنظیم شد",
        "menu_closed": "❌ منو بسته شد. برای باز کردن /start بزنید",
        "only_admin": "⛔ فقط ادمین می‌تواند این کار را انجام دهد",
        "bot_stop": "🛑 ربات در حال خاموش شدن...",
        "analyzing": "🧠 در حال تحلیل علمی...",
        "too_short": "⚠️ متن برای تحلیل خیلی کوتاه است",
        "downloading": "📥 در حال دانلود... لطفاً صبر کنید",
        "uploading": "📤 در حال آپلود به تلگرام...",
        "err_dl": "❌ خطا در دانلود. لینک را بررسی کنید",
        "err_api": "❌ خطا در ارتباط با هوش مصنوعی. بعداً تلاش کنید",
        "voice_generating": "🔊 در حال ساخت فایل صوتی...",
        "voice_translating": "🌐 در حال ترجمه به {lang}...",
        "voice_caption": "🔊 نسخه صوتی",
        "voice_caption_lang": "🔊 نسخه صوتی ({lang})",
        "voice_error": "❌ خطا در ساخت فایل صوتی",
        "voice_no_text": "⛔ به یک پیام ریپلای بزنید یا ابتدا یک متن را تحلیل کنید.",
        "voice_invalid_lang": "⛔ زبان نامعتبر. زبان‌های پشتیبانی: fa, en, fr, ko",
        "access_denied": "⛔ شما دسترسی به این ربات ندارید.",
        "limit_reached": "⛔ سقف درخواست روزانه شما تمام شد ({remaining} از {limit}).",
        "remaining_requests": "📊 درخواست‌های باقی‌مانده امروز: {remaining}"
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
            "   • Auto-download in highest quality\n\n"
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
        "remaining_requests": "📊 Remaining requests today: {remaining}"
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
            "   • Téléchargement auto en HD\n\n"
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
        "remaining_requests": "📊 Requêtes restantes aujourd'hui: {remaining}"
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
            "   • 최고 화질 자동 다운로드\n\n"
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
        "remaining_requests": "📊 오늘 남은 요청: {remaining}"
    }
}

def get_msg(key, user_id=None):
    """Retrieve localized message based on User ID or Global Settings"""
    lang = "fa"
    if user_id and user_id in USER_LANG:
        lang = USER_LANG[user_id]
        # logger.info(f"DEBUG: Found User {user_id} Lang: {lang}") # Debug
    else:
        lang = SETTINGS.get("lang", "fa")
    
    # Validation
    if lang not in MESSAGES: lang = "fa"
    
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, MESSAGES["en"].get(key, ""))

# ==============================================================================
# LOGIC: MENU & KEYBOARDS
# ==============================================================================

def get_main_keyboard(user_id):
    """Generate the dynamic keyboard based on User Language"""
    is_admin = user_id == SETTINGS["admin_id"]
    
    # Base keyboard for all users
    kb = [
        [KeyboardButton(get_msg("btn_status", user_id)), KeyboardButton(get_msg("btn_help", user_id)), KeyboardButton(get_msg("btn_voice", user_id))],
        [KeyboardButton("🇮🇷 فارسی"), KeyboardButton("🇺🇸 English"), KeyboardButton("🇫🇷 Français"), KeyboardButton("🇰🇷 한국어")]
    ]
    
    # Admin-only: Settings row
    if is_admin:
        kb.insert(1, [KeyboardButton(get_msg("btn_dl", user_id)), KeyboardButton(get_msg("btn_fc", user_id)), KeyboardButton(get_msg("btn_stop", user_id))])
    
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
# HELPERS
# ==============================================================================

async def smart_reply(msg, status_msg, response, user_id):
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
    
    # 2. Get user language for header/footer
    lang = USER_LANG.get(user_id, "fa")
    
    header_templates = {
        "fa": "🧠 **تحلیل توسط {}**",
        "en": "🧠 **Analysis by {}**",
        "fr": "🧠 **Analyse par {}"
    }
    
    footer_templates = {
        "fa": (
            "\n\n━━━━━━━━━━━━━━\n"
            "💡 **برای مشاهده تحلیل کامل:**\n"
            "به این پیام ریپلای بزنید و `/detail` بنویسید"
        ),
        "en": (
            "\n\n━━━━━━━━━━━━━━\n"
            "💡 **For full analysis:**\n"
            "Reply to this message with `/detail`"
        ),
        "fr": (
            "\n\n━━━━━━━━━━━━━━\n"
            "💡 **Pour l'analyse complète:**\n"
            "Répondez avec `/detail`"
        )
    }
    
    header = header_templates.get(lang, header_templates["fa"]).format(model_name)
    footer = footer_templates.get(lang, footer_templates["fa"])
    
    # 3. Parse Split (Summary vs Detail)
    full_content = response.content
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
            await status_msg.edit_text(final_text, parse_mode='Markdown')
        except Exception:
            await status_msg.edit_text(final_text, parse_mode=None)

# ==============================================================================
# LOGIC: INSTAGRAM DOWNLOAD
# ==============================================================================

async def download_instagram(url, chat_id, bot, reply_to_message_id=None):
    """Download and send video using yt-dlp"""
    try:
        # 1. Filename setup
        timestamp = int(asyncio.get_event_loop().time())
        filename = Path(f"insta_{timestamp}.mp4")
        
        # 2. Command
        cmd = [
            "yt-dlp",
            "-f", "best[ext=mp4]",
            "-o", str(filename),
            url
        ]
        
        # 3. Cookies if available
        cookie_file = Path("cookies.txt")
        if cookie_file.exists():
            cmd.insert(1, str(cookie_file))
            cmd.insert(1, "--cookies")

        # 4. Run Download
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Download Error: {stderr.decode()}")
            return False

        # 5. Send to User
        if filename.exists():
            with open(filename, "rb") as video_file:
                await bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    caption="📥 **Su6i Yar** | @su6i\\_yar\\_bot",
                    parse_mode='Markdown',
                    reply_to_message_id=reply_to_message_id,
                    supports_streaming=True
                )
            # Cleanup
            filename.unlink()
            return True
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
    await send_welcome(update)

async def cmd_close_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("❌ Command /close triggered")
    await update.message.reply_text(
        get_msg("menu_closed"), 
        reply_markup=ReplyKeyboardRemove()
    )

async def cmd_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📊 Command /status triggered")
    dl_s = get_msg("dl_on") if SETTINGS["download"] else get_msg("dl_off")
    fc_s = get_msg("fc_on") if SETTINGS["fact_check"] else get_msg("fc_off")
    info = get_msg("status_fmt").format(dl=dl_s, fc=fc_s)
    await update.message.reply_text(info, parse_mode='Markdown')

async def cmd_toggle_dl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📥 Command /toggle_dl triggered")
    SETTINGS["download"] = not SETTINGS["download"]
    state = get_msg("dl_on") if SETTINGS["download"] else get_msg("dl_off")
    await update.message.reply_text(get_msg("action_dl").format(state=state))

async def cmd_toggle_fc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🧠 Command /toggle_fc triggered")
    SETTINGS["fact_check"] = not SETTINGS["fact_check"]
    state = get_msg("fc_on") if SETTINGS["fact_check"] else get_msg("fc_off")
    await update.message.reply_text(get_msg("action_fc").format(state=state))

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
        dl_s = get_msg("dl_on", user_id) if SETTINGS["download"] else get_msg("dl_off", user_id)
        fc_s = get_msg("fc_on", user_id) if SETTINGS["fact_check"] else get_msg("fc_off", user_id)
        info = get_msg("status_fmt", user_id).format(dl=dl_s, fc=fc_s)
        await msg.reply_text(info, parse_mode='Markdown')
        return

    # Language Switching
    if "فارسی" in text:
        USER_LANG[user_id] = "fa"
        await msg.reply_text("✅ زبان فارسی انتخاب شد.", reply_markup=get_main_keyboard(user_id))
        return
    if "English" in text:
        USER_LANG[user_id] = "en"
        await msg.reply_text("✅ English language selected.", reply_markup=get_main_keyboard(user_id))
        logger.info(f"🇺🇸 User {user_id} switched to English")
        return
    if "Français" in text:
        USER_LANG[user_id] = "fr"
        await msg.reply_text("✅ Langue française sélectionnée.", reply_markup=get_main_keyboard(user_id))
        return
    if "한국어" in text:
        USER_LANG[user_id] = "ko"
        await msg.reply_text("✅ 한국어가 선택되었습니다.", reply_markup=get_main_keyboard(user_id))
        return
    
    # Voice Button
    if text.startswith("🔊"):
        detail_text = LAST_ANALYSIS_CACHE.get(user_id)
        if not detail_text:
            await msg.reply_text("⛔ هیچ تحلیل ذخیره‌شده‌ای موجود نیست.")
            return
        status_msg = await msg.reply_text("🔊 در حال ساخت فایل صوتی...")
        try:
            audio_buffer = await text_to_speech(detail_text, lang)
            await msg.reply_voice(voice=audio_buffer, caption="🔊 نسخه صوتی تحلیل")
            await status_msg.delete()
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            await status_msg.edit_text("❌ خطا در ساخت فایل صوتی")
        return
        
    # Help
    if text.startswith("ℹ️") or text.startswith("🆘"):
        help_text = get_msg("help_msg", user_id)
        await msg.reply_text(help_text, parse_mode='Markdown') 
        return

    # Toggle DL
    if text.startswith("📥"):
        SETTINGS["download"] = not SETTINGS["download"]
        state = get_msg("dl_on", user_id) if SETTINGS["download"] else get_msg("dl_off", user_id)
        await msg.reply_text(get_msg("action_dl", user_id).format(state=state))
        return

    # Toggle FC
    if text.startswith("🧠"):
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
            
        status_msg = await msg.reply_text(get_msg("downloading", user_id))
        
        success = await download_instagram(text, msg.chat_id, context.bot, msg.message_id)
        if success:
            await status_msg.delete()
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
        response = await analyze_text_gemini(text, status_msg, lang)
        
        # Increment usage and get remaining
        remaining = increment_daily_usage(user_id)
        
        await smart_reply(msg, status_msg, response, user_id)
        
        # Show remaining requests (skip for admin)
        if user_id != SETTINGS["admin_id"]:
            limit = get_user_limit(user_id)
            await msg.reply_text(f"📊 {remaining}/{limit} درخواست باقی‌مانده امروز")
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

    # Smart chunking: split by paragraphs, not mid-paragraph
    max_length = 3900  # Leave some margin
    
    if len(detail_text) <= max_length:
        # Fits in one message
        try:
            await msg.reply_text(detail_text, parse_mode='Markdown')
        except Exception:
            await msg.reply_text(detail_text, parse_mode=None)
    else:
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
                    await msg.reply_text(f"📄 بخش {i+1} از {len(chunks)}\n━━━━━━━━━━━━━━\n\n{chunk}", parse_mode=None)


# TTS Voice Mapping
TTS_VOICES = {
    "fa": "fa-IR-FaridNeural",   # Persian - Male
    "en": "en-US-GuyNeural",     # English - Male
    "fr": "fr-FR-HenriNeural",   # French - Male
    "ko": "ko-KR-InJoonNeural"   # Korean - Male
}

async def text_to_speech(text: str, lang: str = "fa") -> io.BytesIO:
    """Convert text to speech using edge-tts. Returns audio as BytesIO."""
    voice = TTS_VOICES.get(lang, TTS_VOICES["fa"])
    
    # Clean text for TTS (remove markdown)
    clean_text = re.sub(r'\*\*|▫️|━+|✅|❌|⚠️|🧠|📄|💡', '', text)
    clean_text = re.sub(r'\[.*?\]', '', clean_text)  # Remove markdown links
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

# Language code mapping for /voice command
LANG_ALIASES = {
    "fa": "fa", "farsi": "fa", "persian": "fa", "فارسی": "fa",
    "en": "en", "english": "en", "انگلیسی": "en",
    "fr": "fr", "french": "fr", "français": "fr", "فرانسوی": "fr",
    "ko": "ko", "kr": "ko", "korean": "ko", "한국어": "ko", "کره‌ای": "ko"
}

LANG_NAMES = {
    "fa": "Persian (Farsi)", "en": "English", "fr": "French", "ko": "Korean"
}

async def translate_text(text: str, target_lang: str) -> str:
    """Translate text to target language using Gemini"""
    lang_name = LANG_NAMES.get(target_lang, "English")
    
    try:
        chain = get_smart_chain()
        prompt = f"Translate the following text to {lang_name}. Only output the translation, no explanations:\n\n{text}"
        response = await chain.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text  # Return original if translation fails


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
    target_lang = user_lang  # Default to user's app language
    if context.args:
        lang_arg = context.args[0].lower()
        if lang_arg in LANG_ALIASES:
            target_lang = LANG_ALIASES[lang_arg]
        else:
            await msg.reply_text(get_msg("voice_invalid_lang", user_id))
            return
    
    # Priority 1: Check if replied to a message
    target_text = ""
    if msg.reply_to_message:
        logger.info(f"🔊 Reply detected: text={bool(msg.reply_to_message.text)}, caption={bool(msg.reply_to_message.caption)}")
        target_text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
    else:
        logger.info("🔊 No reply_to_message detected")
    
    # Priority 2: Check for direct text input (/voice <text> or /voice <lang> <text>)
    if not target_text and context.args:
        # If first arg is a language code, text starts from arg[1]
        if context.args[0].lower() in LANG_ALIASES:
            if len(context.args) > 1:
                target_text = " ".join(context.args[1:])
                logger.info(f"🔊 Using direct text after lang arg: {len(target_text)} chars")
        else:
            # First arg is text, not a language code
            target_text = " ".join(context.args)
            logger.info(f"🔊 Using direct text: {len(target_text)} chars")
    
    # Priority 3: Check cache if no reply and no direct text
    if not target_text:
        target_text = LAST_ANALYSIS_CACHE.get(user_id, "")
        logger.info(f"🔊 Using cache: {bool(target_text)}")
    
    if not target_text:
        logger.info("🔊 No text found, sending error")
        await msg.reply_text(get_msg("voice_no_text", user_id))
        return
    
    # Check if translation is needed (if target_lang differs from user's default)
    need_translation = target_lang != user_lang
    
    if need_translation:
        status_msg = await msg.reply_text(get_msg("voice_translating", user_id).format(lang=LANG_NAMES.get(target_lang, target_lang)))
        target_text = await translate_text(target_text, target_lang)
        await status_msg.edit_text(get_msg("voice_generating", user_id))
    else:
        status_msg = await msg.reply_text(get_msg("voice_generating", user_id))
    
    try:
        audio_buffer = await text_to_speech(target_text, target_lang)
        # Reply to the original message (not the /voice command)
        reply_to_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id
        
        caption = get_msg("voice_caption_lang", user_id).format(lang=LANG_NAMES.get(target_lang, target_lang)) if need_translation else get_msg("voice_caption", user_id)
        await msg.reply_voice(
            voice=audio_buffer,
            caption=caption,
            reply_to_message_id=reply_to_id
        )
        await status_msg.delete()
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        await status_msg.edit_text(get_msg("voice_error", user_id))


def main():
    if not TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env")
        return

    print("🚀 Starting SmartBot Core...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start_handler))
    app.add_handler(CommandHandler("help", cmd_start_handler)) # Reuse start for help
    app.add_handler(CommandHandler("close", cmd_close_handler))
    app.add_handler(CommandHandler("status", cmd_status_handler))
    app.add_handler(CommandHandler("toggle_dl", cmd_toggle_dl_handler))
    app.add_handler(CommandHandler("toggle_fc", cmd_toggle_fc_handler))
    app.add_handler(CommandHandler("check", cmd_check_handler))
    app.add_handler(CommandHandler("detail", cmd_detail_handler))
    app.add_handler(CommandHandler("voice", cmd_voice_handler))  # TTS Voice
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

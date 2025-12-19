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

# Telegram Imports
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# ==============================================================================
# CONFIGURATION & SETUP
# ==============================================================================

# 1. Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("SmartBot")

# 2. Environment Variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 3. Global Settings
SETTINGS = {
    "download": True,
    "fact_check": True,
    "min_fc_len": 50,
    "lang": "fa",
    "admin_id": int(TELEGRAM_CHAT_ID) if TELEGRAM_CHAT_ID else 0
}

# User Preferences (In-Memory)
USER_LANG = {}

# ... (Localization Dictionary MESSAGES is unchanged, skipping for brevity) ...

async def cmd_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ Command /check triggered")
    msg = update.message
    user_id = update.effective_user.id
    lang = USER_LANG.get(user_id, "fa")

    # Check if reply or arguments
    target_text = ""
    if msg.reply_to_message and msg.reply_to_message.text:
        target_text = msg.reply_to_message.text
    elif context.args:
        target_text = " ".join(context.args)
    
    if not target_text:
        await msg.reply_text("⛔ Reply to a message or provide text: `/check <text>`")
        return

    status_msg = await msg.reply_text(get_msg("analyzing"))
    response = await analyze_text_gemini(target_text, lang)
    
    await smart_reply(msg, status_msg, response, user_id)

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
                await status_msg.edit_text(get_msg("uploading"))
                await msg.reply_video(video=open(file_path, 'rb'), caption="🤖 @SmartInstaDL_Bot")
                os.remove(file_path) # Cleanup
                await status_msg.delete() 
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                await status_msg.edit_text("❌ Error uploading video.")
        else:
            await status_msg.edit_text("❌ Download failed (Private/Invalid link).")
        return

    # --- 3. AI ANALYSIS (Fallback) ---
    
    if SETTINGS["fact_check"] and len(text) >= SETTINGS["min_fc_len"]:
        status_msg = await msg.reply_text(get_msg("analyzing"))
        response = await analyze_text_gemini(text, lang)
        
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

async def analyze_text_gemini(text, status_msg=None, lang_code="fa"):
    """Analyze text using Smart Chain Fallback with Live Status Updates"""
    if not SETTINGS["fact_check"]: return None

    # Map lang_code to English name for Prompt
    lang_map = {"fa": "Persian (Farsi)", "en": "English", "fr": "French"}
    target_lang = lang_map.get(lang_code, "Persian")

    try:
        logger.info(f"🧠 STARTING AI ANALYSIS ({target_lang}) for text: {text[:20]}...")
        prompt_text = (
            "You are a professional Fact-Check Assistant. "
            f"Analyze the following text. Answer strictly in **{target_lang}** language.\n\n"
            "IMPORTANT: Telegram DOES NOT support Tables. Do NOT use Markdown Tables (no | pipes).\n"
            "Use this LIST format instead:\n\n"
            "PART 1: SUMMARY\n"
            "- Status: (✅ Verified / ⚠️ Misleading / ❌ False)\n\n"
            "1️⃣ **Claim:** [Quote the claim]\n"
            "   ✅ **Status:** [True/False]\n"
            "   📚 **Source:** [Title + Link]\n\n"
            "2️⃣ **Claim:** ...\n\n"
            "- **Conclusion:** [Brief summary]\n\n"
            "|||SPLIT|||\n\n"
            "PART 2: DEEP DIVE\n"
            "- Detail Scientific Analysis.\n"
            "- Biological Mechanisms.\n"
            "- **Academic References:** [Full Title + Link]\n"
            f"Text:\n{text}"
        )
        
        chain = get_smart_chain()
        logger.info("🚀 Invoking LangChain...")
        
        # Callbacks for Live Updates
        config = {}
        if status_msg:
             config["callbacks"] = [StatusUpdateCallback(status_msg, get_msg)]

        # Invoke Chain (Async)
        response = await chain.ainvoke(
            [HumanMessage(content=prompt_text)],
            config=config
        )
        
        # Log metadata to see which model was used
        model_used = response.response_metadata.get('model_name', 'Unknown')
        logger.info(f"✅ Response from {model_used}. Split Token Present: {'|||SPLIT|||' in response.content}")
        return response

    except Exception as e:
        logger.error(f"❌ SmartChain Error: {e}", exc_info=True)
        return None

# 4. Localization Dictionary
# 4. Localization Dictionary
MESSAGES = {
    "fa": {
        "welcome": "👋 **سلام {name}!**\nبه ربات هوشمند خوش آمدید.\n\n🔻 از منوی پایین استفاده کنید یا لینک بفرستید:",
        "btn_status": "📊 وضعیت ربات",
        "btn_help": "🆘 راهنما",
        "btn_dl": "📥 مدیریت دانلود",
        "btn_fc": "🧠 مدیریت هوش مصنوعی",
        "btn_stop": "🛑 خاموش کردن ربات",
        "btn_lang_fa": "🇮🇷 فارسی",
        "btn_lang_en": "🇺🇸 English",
        "btn_lang_fr": "🇫🇷 Français",
        "status_fmt": (
            "📊 **وضعیت لحظه‌ای ربات هوشمند**\n"
            "━━━━━━━━━━━━━━\n"
            "📥 **سیستم دانلود:**        {dl}\n"
            "🧠 **هوش مصنوعی:**      {fc}\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 برای تغییر از دکمه‌های زیر استفاده کنید."
        ),
        "help_msg": (
            "📚 **راهنمای کامل ربات:**\n\n"
            "📥 **دانلودر اینستاگرام:**\n"
            "• لینک پست یا ریلز (Reels) را بفرستید -> ویدیو با بالاترین کیفیت دانلود می‌شود.\n\n"
            "🧠 **هوش مصنوعی (فکت‌چکینگ):**\n"
            "• هر متنی (اخبار، شایعه، کپشن) بفرستید -> ربات با ۸ مدل هوشمند (گوگل + دیپ‌سیک) آن را بررسی و تایید/رد می‌کند.\n"
            "• قابلیت جستجو در گوگل برای بررسی اخبار لحظه‌ای فعال است.\n\n"
            "⚙️ **دستورات:**\n"
            "/start - شروع مجدد\n"
            "/status - وضعیت ربات\n"
            "/check [متن] - تحلیل متن در گروه‌ها\n"
            "/stop - خاموش کردن ربات (ادمین)\n"
        ),
        "dl_on": "✅ فعال",
        "dl_off": "❌ غیرفعال",
        "fc_on": "✅ فعال",
        "fc_off": "❌ غیرفعال",
        "action_dl": "📥 وضعیت دانلود تغییر کرد: {state}",
        "action_fc": "🧠 وضعیت هوش مصنوعی تغییر کرد: {state}",
        "lang_set": "🇮🇷 زبان روی **فارسی** تنظیم شد.",
        "menu_closed": "❌ منو بسته شد. برای باز کردن مجدد /start بزنید.",
        "only_admin": "⛔ فقط ادمین می‌تواند این کار را انجام دهد.",
        "bot_stop": "🛑 ربات در حال خاموش شدن...",
        "analyzing": "🧠 در حال تحلیل دقیق علمی... (مدل‌های Gemini + DeepSeek w/ Search)",
        "too_short": "⚠️ متن برای تحلیل خیلی کوتاه است.",
        "downloading": "📥 در حال دانلود ویدیو... لطفا صبر کنید.",
        "uploading": "📤 در حال آپلود به تلگرام...",
        "err_dl": "❌ خطا در دانلود. لینک بررسی شود.",
        "err_api": "❌ خطا در ارتباط با هوش مصنوعی. لطفا بعدا تلاش کنید."
    },
    "en": {
        "welcome": "👋 **Hello {name}!**\nWelcome to Smart Bot.\n\n🔻 Use the menu below or send a link:",
        "btn_status": "📊 Status",
        "btn_help": "🆘 Help",
        "btn_dl": "📥 Toggle Download",
        "btn_fc": "🧠 Toggle AI",
        "btn_stop": "🛑 Stop Bot",
        "btn_lang_fa": "🇮🇷 فارسی",
        "btn_lang_en": "🇺🇸 English",
        "btn_lang_fr": "🇫🇷 Français",
        "status_fmt": (
            "📊 **Live System Status**\n"
            "━━━━━━━━━━━━━━\n"
            "📥 **Downloader:**        {dl}\n"
            "🧠 **AI Fact-Check:**     {fc}\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 Use buttons below to toggle."
        ),
        "help_msg": (
            "📚 **Full Bot Guide:**\n\n"
            "📥 **Instagram Downloader:**\n"
            "• Send Post/Reels Link -> Download High Quality Video.\n\n"
            "🧠 **AI Fact-Checker:**\n"
            "• Send any text -> Analyzed by 8 AI Models (Google + DeepSeek).\n"
            "• Real-time Google Search enabled for latest news.\n\n"
            "⚙️ **Commands:**\n"
            "/start - Restart Menu\n"
            "/status - Check Settings\n"
            "/check [text] - Check text in groups\n"
            "/stop - Shutdown Bot (Admin)\n"
        ),
        "dl_on": "✅ On ",
        "dl_off": "❌ Off",
        "fc_on": "✅ On ",
        "fc_off": "❌ Off",
        "action_dl": "📥 Download status: {state}",
        "action_fc": "🧠 AI status: {state}",
        "lang_set": "🇺🇸 Language set to **English**.",
        "menu_closed": "❌ Menu closed. Type /start to open.",
        "only_admin": "⛔ Admin only.",
        "bot_stop": "🛑 Bot is shutting down...",
        "analyzing": "🧠 Analyzing text... (Smart Chain)",
        "too_short": "⚠️ Text is too short.",
        "downloading": "📥 Downloading video...",
        "uploading": "📤 Uploading to Telegram...",
        "err_dl": "❌ Download failed.",
        "err_api": "⚠️ AI API Error."
    },
    "fr": {
        "welcome": "👋 **Bonjour {name}!**\nBienvenue.\n\n🔻 Utilisez le menu ci-dessous :",
        "btn_status": "📊 État",
        "btn_help": "🆘 Aide",
        "btn_dl": "📥 Téléchargement",
        "btn_fc": "🧠 IA",
        "btn_stop": "🛑 Arrêter",
        "btn_lang_fa": "🇮🇷 فارسی",
        "btn_lang_en": "🇺🇸 English",
        "btn_lang_fr": "🇫🇷 Français",
        "status_fmt": (
            "📊 **État du Système**\n"
            "━━━━━━━━━━━━━━\n"
            "📥 **Téléchargement:**    {dl}\n"
            "🧠 **IA Fact-Check:**     {fc}\n"
            "━━━━━━━━━━━━━━\n"
            "🔻 Utilisez les boutons pour changer."
        ),
        "help_msg": (
            "📚 **Guide Complet:**\n\n"
            "📥 **Instagram:**\n"
            "• Envoyez lien (Reels/Post) -> Téléchargement HD.\n\n"
            "🧠 **Intelligence Artificielle:**\n"
            "• Envoyez un texte -> Analyse par 8 modèles IA.\n\n"
            "⚙️ **Commandes:**\n"
            "/start - Menu\n"
            "/status - État\n"
            "/check [texte] - Vérifier le texte\n"
        ),
        "dl_on": "✅ Activé",
        "dl_off": "❌ Désactivé",
        "fc_on": "✅ Activé",
        "fc_off": "❌ Désactivé",
        "action_dl": "📥 Téléchargement: {state}",
        "action_fc": "🧠 IA: {state}",
        "lang_set": "🇫🇷 Langue définie sur **Français**.",
        "menu_closed": "❌ Menu fermé. Tapez /start.",
        "only_admin": "⛔ Admin seulement.",
        "bot_stop": "🛑 Arrêt du bot...",
        "analyzing": "🧠 Analyse en cours...",
        "too_short": "⚠️ Texte trop court.",
        "downloading": "📥 Téléchargement...",
        "uploading": "📤 Envoi...",
        "err_dl": "❌ Échec du téléchargement.",
        "err_api": "⚠️ Erreur API."
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
    kb = [
        [KeyboardButton(get_msg("btn_status", user_id)), KeyboardButton(get_msg("btn_help", user_id))],
        [KeyboardButton(get_msg("btn_dl", user_id)), KeyboardButton(get_msg("btn_fc", user_id))],
        [KeyboardButton("🇮🇷 فارسی"), KeyboardButton("🇺🇸 English"), KeyboardButton("🇫🇷 Français")]
    ]
    if user_id == SETTINGS["admin_id"]:
        # Append to the first row (Status, Help, Stop) to keep it 3 rows total
        kb[0].append(KeyboardButton(get_msg("btn_stop", user_id)))
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
    """Handles AI response sending with Chunking, Caching, and Markdown Safety"""
    if not response:
        await status_msg.edit_text(get_msg("err_api"))
        return

    # 1. Determine Header
    model_name = "Gemini"
    if "model_name" in response.response_metadata:
        model_name = response.response_metadata["model_name"]
    elif "token_usage" in response.response_metadata: # DeepSeek usually relies on this
        model_name = "DeepSeek"
    
    header = f"🧠 **Analysis by {model_name}:**"
    
    # 2. Parse Split (Summary vs Detail)
    full_content = response.content
    
    # Try different split markers just in case
    split_marker = "|||SPLIT|||"
    if split_marker not in full_content:
        # Fallback: Try to find a natural break if AI ignored instructions
        if "---" in full_content:
            split_marker = "---"
    
    if split_marker in full_content and split_marker != "---":
        parts = full_content.split(split_marker)
        summary_text = parts[0].strip()
        detail_text = parts[1].strip()
        # CACHE DETAIL
        LAST_ANALYSIS_CACHE[user_id] = f"{header} (Deep Dive)\n\n{detail_text}"
        logger.info(f"💾 Detail Cached for User {user_id}")
    else:
        # Fallback if AI completely failed to split: Send everything but warn
        logger.warning(f"⚠️ Split Token NOT found in response (Len: {len(full_content)})")
        summary_text = full_content
        LAST_ANALYSIS_CACHE[user_id] = "⚠️ جزئیات بیشتری در دسترس نیست (مدل پاسخ یکپارچه داد)."

    final_text = f"{header}\n\n{summary_text}"
    
    # 3. Send Summary
    # Telegram Limit is 4096.
    if len(final_text) > 4000:
         # If Summary itself is huge, we must chunk it
         chunks = [final_text[i:i+4000] for i in range(0, len(final_text), 4000)]
         for i, chunk in enumerate(chunks):
             try:
                 if i == 0:
                     await status_msg.edit_text(chunk, parse_mode='Markdown')
                 else:
                     await msg.reply_text(chunk, parse_mode='Markdown')
             except Exception:
                 if i == 0: await status_msg.edit_text(chunk, parse_mode=None)
                 else: await msg.reply_text(chunk, parse_mode=None)
    else:
        # Normal Case
        try:
             await status_msg.edit_text(final_text, parse_mode='Markdown')
        except Exception:
             await status_msg.edit_text(final_text, parse_mode=None)

# ==============================================================================
# LOGIC: INSTAGRAM DOWNLOAD
# ==============================================================================

async def download_instagram(url, chat_id, bot):
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
                    caption="🤖 Downloaded by SmartBot",
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

async def cmd_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ Command /check triggered")
    msg = update.message
    # Check if reply or arguments
    target_text = ""
    if msg.reply_to_message and msg.reply_to_message.text:
        target_text = msg.reply_to_message.text
    elif context.args:
        target_text = " ".join(context.args)
    
    if not target_text:
        await msg.reply_text("⛔ Reply to a message or provide text: `/check <text>`")
        return

    status_msg = await msg.reply_text(get_msg("analyzing"))
    # --- 3. AI ANALYSIS (Fallback) ---
    
    if SETTINGS["fact_check"] and len(text) >= SETTINGS["min_fc_len"]:
        status_msg = await msg.reply_text(get_msg("analyzing"))
        response = await analyze_text_gemini(text)
        
        if response:
            header = "🧠 **Gemini Analysis:**"
            # DeepSeek detection
            if "model_name" in response.response_metadata or "token_usage" in response.response_metadata:
                header = "🧠 **DeepSeek Analysis:**"
            
            final_text = f"{header}\n\n{response.content}"
            
            try:
                # Try Markdown first (Prettiest)
                await status_msg.edit_text(final_text, parse_mode='Markdown')
            except Exception as e:
                logger.warning(f"Markdown Fail ({e}), sending plain text.")
                # Fallback to Plain Text (Reliable)
                await status_msg.edit_text(final_text, parse_mode=None)
        else:
            await status_msg.delete() 
        return

async def cmd_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ Command /check triggered")
    msg = update.message
    user_id = update.effective_user.id
    lang = USER_LANG.get(user_id, "fa")

    # Check if reply or arguments
    target_text = ""
    if msg.reply_to_message and msg.reply_to_message.text:
        target_text = msg.reply_to_message.text
    elif context.args:
        target_text = " ".join(context.args)
    
    if not target_text:
        await msg.reply_text("⛔ Reply to a message or provide text: `/check <text>`")
        return

    status_msg = await msg.reply_text(get_msg("analyzing"))
    response = await analyze_text_gemini(target_text, lang)
    
    await smart_reply(msg, status_msg, response, user_id)

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
        
        success = await download_instagram(text, msg.chat_id, context.bot)
        if success:
            await status_msg.delete()
        else:
            await status_msg.edit_text(get_msg("err_dl", user_id))
        return

    # --- 3. AI ANALYSIS (Fallback) ---
    
    if SETTINGS["fact_check"] and len(text) >= SETTINGS["min_fc_len"]:
        status_msg = await msg.reply_text(get_msg("analyzing", user_id))
        response = await analyze_text_gemini(text, status_msg, lang)
        
        await smart_reply(msg, status_msg, response, user_id)
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

    await msg.reply_text(f"🔬 **Deep Dive Analysis:**\n\n{detail_text}", parse_mode='Markdown')

def main():
    if not TELEGRAM_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env")
        return

    print("🚀 Starting SmartBot Core...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start_handler))
    app.add_handler(CommandHandler("help", cmd_start_handler)) # Reuse start for help
    app.add_handler(CommandHandler("close", cmd_close_handler))
    app.add_handler(CommandHandler("status", cmd_status_handler))
    app.add_handler(CommandHandler("toggle_dl", cmd_toggle_dl_handler))
    app.add_handler(CommandHandler("toggle_fc", cmd_toggle_fc_handler))
    app.add_handler(CommandHandler("check", cmd_check_handler))
    app.add_handler(CommandHandler("detail", cmd_detail_handler)) # NEW COMMAND
    app.add_handler(CommandHandler("stop", cmd_stop_bot_handler))

    # All Messages (Text)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), global_message_handler))

    print("✅ Bot is Polling...")
    app.run_polling()

if __name__ == "__main__":
    main()

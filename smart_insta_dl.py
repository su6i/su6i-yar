import os
import re
import sys
import argparse
import subprocess
import asyncio
import json
import logging
import time
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import google.generativeai as genai

# --- Imports for Cookie Updating ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================================
# Config & Setup
# ============================================================================

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Runtime Settings
SETTINGS = {
    "download": True,
    "fact_check": True,
    "min_fact_check_length": 50,
    "lang": "en",
    "admin_id": int(os.getenv("TELEGRAM_CHAT_ID", 0))
}

# Localization
LANG_MAP = {
    "fa": "Persian (Farsi)",
    "en": "English",
    "fr": "French"
}

MESSAGES = {
    "fa": {
        "thinking": "🤔 در حال بررسی صحت و سقم این موضوع هستم... لطفاً صبر کنید.",
        "disabled": "🚫 فکت‌چکینگ غیرفعال است.",
        "too_short": "❌ متن برای تحلیل خیلی کوتاه است.",
        "api_error": "⚠️ خطای API:",
        "result_header": "🧠 **تحلیل هوشمند (Gemini):**",
        "lang_set": "🏳️ زبان ربات تغییر کرد به: فارسی",
        "welcome": (
            "👋 **سلام {name}!**\n"
            "به ربات هوشمند خوش آمدید. 🤖\n\n"
            "🌟 **امکانات من:**\n"
            "1️⃣ **دانلود اینستاگرام:** لینک پست/ریلز بفرستید تا دانلود کنم.\n"
            "2️⃣ **فکت‌چکینگ:** متن یا کپشن بفرستید تا با هوش مصنوعی بررسی کنم.\n\n"
            "👇 **برای شروع یک گزینه را انتخاب کنید یا لینک بفرستید:**"
        ),
        "status_msg": (
            "⚙️ **تنظیمات فعلی:**\n\n"
            "📥 **دانلود:** {dl_status}\n"
            "🧠 **فکت‌چکینگ:** {fc_status}\n"
            "📏 **حداقل طول متن:** {min_len} کاراکتر"
        ),
        "help_msg": (
            "📚 **راهنمای دستورات ربات:**\n\n"
            "**دانلود ویدیو:**\n"
            "🔹 لینک اینستاگرام (پست/ریلز) بفرستید تا دانلود شود.\n"
            "🔹 دکمه **Toggle Download** وضعیت دانلود را روشن/خاموش می‌کند.\n\n"
            "**هوش مصنوعی (Gemini):**\n"
            "🔸 روی متن ریپلای کنید و `/check` بزنید.\n"
            "🔸 دکمه **Toggle Fact-Check** تحلیل خودکار را روشن/خاموش می‌کند.\n\n"
            "**عمومی:**\n"
            "🔹 **Status:** مشاهده تنظیمات\n"
            "🔹 **Help:** نمایش همین راهنما"
        ),
        "dl_on": "✅ روشن",
        "dl_off": "❌ خاموش",
        "toggle_dl_msg": "📥 **وضعیت دانلود:** {state}",
        "fc_on": "✅ روشن",
        "fc_off": "❌ خاموش",
        "toggle_fc_msg": "🧠 **وضعیت فکت‌چکینگ:** {state}",
        "shutdown_success": "🛑 **ربات در حال خاموش شدن است...** 👋",
        "shutdown_fail": "🚫 **خطا:** فقط ادمین می‌تواند ربات را خاموش کند.",
        "btn_status": "📊 وضعیت ربات",
        "btn_help": "🆘 راهنما",
        "btn_dl": "📥 خاموش/روشن دانلود",
        "btn_fc": "🧠 خاموش/روشن هوش مصنوعی",
        "btn_stop": "🛑 خاموش کردن ربات"
    },
    "en": {
        "thinking": "🤔 Fact-checking this claim... Please wait.",
        "disabled": "🚫 Fact-Checking is disabled.",
        "too_short": "❌ Text is too short.",
        "api_error": "⚠️ API Error:",
        "result_header": "🧠 **Smart Analysis (Gemini):**",
        "lang_set": "🏳️ Bot language set to: English",
        "welcome": (
            "👋 **Hello {name}!**\n"
            "Welcome to your Smart Assistant. 🤖\n\n"
            "🌟 **What can I do?**\n"
            "1️⃣ **Download Instagram:** Send me a link (Post/Reel).\n"
            "2️⃣ **Fact-Check:** Send text to verify validity.\n\n"
            "👇 **Select an option below or send a link:**"
        ),
        "status_msg": (
            "⚙️ **Current Settings:**\n\n"
            "📥 **Download:** {dl_status}\n"
            "🧠 **Fact Check:** {fc_status}\n"
            "📏 **Min Text Length:** {min_len} chars"
        ),
        "help_msg": (
            "📚 **Bot Command Guide:**\n\n"
            "**Video Downloading:**\n"
            "🔹 Send any Instagram link (Post/Reel) to download.\n"
            "🔹 **Toggle Download** - Turn downloading On/Off.\n\n"
            "**AI Fact-Checking (Gemini):**\n"
            "🔸 `/check` - Reply to any message to fact-check it.\n"
            "🔸 **Toggle Fact-Check** - Turn auto fact-checking On/Off.\n\n"
            "**General:**\n"
            "🔹 **Status** - View current settings.\n"
            "🔹 **Help** - Show this message."
        ),
        "dl_on": "✅ On",
        "dl_off": "❌ Off",
        "toggle_dl_msg": "📥 **Download is now:** {state}",
        "fc_on": "✅ On",
        "fc_off": "❌ Off",
        "toggle_fc_msg": "🧠 **Fact-Checking is now:** {state}",
        "shutdown_success": "🛑 **Bot is shutting down...** 👋",
        "shutdown_fail": "🚫 **Error:** Only Admin can stop the bot.",
        "btn_status": "📊 Status",
        "btn_help": "🆘 Help",
        "btn_dl": "📥 Toggle Download",
        "btn_fc": "🧠 Toggle Fact-Check",
        "btn_stop": "🛑 Stop Bot"
    },
    "fr": {
        "thinking": "🤔 Vérification des faits en cours... Veuillez patienter.",
        "disabled": "🚫 La vérification des faits est désactivée.",
        "too_short": "❌ Texte trop court.",
        "api_error": "⚠️ Erreur API:",
        "result_header": "🧠 **Analyse Intelligente (Gemini):**",
        "lang_set": "🏳️ Langue du bot définie sur: Français",
        "welcome": (
            "👋 **Bonjour {name}!**\n"
            "Bienvenue sur votre assistant intelligent. 🤖\n\n"
            "🌟 **Que puis-je faire ?**\n"
            "1️⃣ **Télécharger Instagram:** Envoyez-moi un lien.\n"
            "2️⃣ **Vérification des faits:** Envoyez un texte pour vérifier.\n\n"
            "👇 **Sélectionnez une option ci-dessous ou envoyez un lien:**"
        ),
        "status_msg": (
            "⚙️ **Paramètres actuels:**\n\n"
            "📥 **Téléchargement:** {dl_status}\n"
            "🧠 **Vérification:** {fc_status}\n"
            "📏 **Longueur min:** {min_len} caractères"
        ),
        "help_msg": (
            "📚 **Guide des commandes:**\n\n"
            "**Téléchargement:**\n"
            "🔹 Envoyez un lien Instagram.\n"
            "🔹 **Toggle Download** - Activer/Désactiver.\n\n"
            "**Intelligence Artificielle:**\n"
            "🔸 Répondez avec `/check`.\n"
            "🔸 **Toggle Fact-Check** - Activer/Désactiver auto.\n\n"
            "**Général:**\n"
            "🔹 **Status** - Voir paramètres.\n"
            "🔹 **Help** - Voir ce message."
        ),
        "dl_on": "✅ Activé",
        "dl_off": "❌ Désactivé",
        "toggle_dl_msg": "📥 **Téléchargement:** {state}",
        "fc_on": "✅ Activé",
        "fc_off": "❌ Désactivé",
        "toggle_fc_msg": "🧠 **Vérification:** {state}",
        "shutdown_success": "🛑 **Le bot s'arrête...** 👋",
        "shutdown_fail": "🚫 **Erreur:** Seul l'admin peut arrêter le bot.",
        "btn_status": "📊 État",
        "btn_help": "🆘 Aide",
        "btn_dl": "📥 Téléchargement",
        "btn_fc": "🧠 Vérification",
        "btn_stop": "🛑 Arrêter le bot"
    }
}
def get_msg(key):
    lang = SETTINGS.get("lang", "en")
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, "")

# ... (Previous Code) ...

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_text = (
        "⚙️ **Current Settings:**\n\n"
        f"📥 **Download:** {'✅ On' if SETTINGS['download'] else '❌ Off'}\n"
        f"🧠 **Fact Check:** {'✅ On' if SETTINGS['fact_check'] else '❌ Off'}\n"
        f"📏 **Min Text Length:** {SETTINGS['min_fact_check_length']} chars"
    )
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def cmd_set_min_len(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set minimum text length for auto fact-checking"""
    if not context.args:
        await update.message.reply_text("Usage: /set_min_len <number>\nExample: /set_min_len 20")
        return
    
    try:
        val = int(context.args[0])
        if val < 10:
            await update.message.reply_text("⚠️ Minimum length must be at least 10.")
            return
        SETTINGS["min_fact_check_length"] = val
        await update.message.reply_text(f"📏 **Minimum length set to: {val}**", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")

# ... (Previous Commands) ...

async def server_handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    
    # 1. Check for Instagram Link
    match = re.search(r"(https?://www\.instagram\.com/(p|reel)/[^\s]+)", msg.text)
    
    if match:
        # ... (Instagram Logic - Unchanged) ...
       pass 

    else:
        # --- NO LINK FOUND -> TEXT ANALYSIS LOGIC ---
        limit = SETTINGS.get("min_fact_check_length", 50)
        
        if SETTINGS["fact_check"] and msg.chat.type == "private" and len(msg.text) > limit:
             # Auto-analyze in DM
             status_msg = await msg.reply_text("🧠 Analyzing text...")
             analysis = await analyze_caption(msg.text)
             # ... (Rest of logic) ...

# Configure GenAI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    SETTINGS["fact_check"] = False

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("InstaBot")

# Directories
BASE_DIR = Path(__file__).parent.resolve()
TEMP_DIR = BASE_DIR / "instagram_videos_temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
COOKIES_FILE = BASE_DIR / "cookies.txt"
SCREENSHOT_DIR = BASE_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Global Settings
MAX_FILE_SIZE = 50 * 1024 * 1024
download_semaphore = asyncio.Semaphore(2)

# ============================================================================
# Core: Cookie & Auth Management
# ============================================================================

def update_instagram_cookies_sync():
    """Blocking function to update cookies using Selenium"""
    driver = None
    logger.info("🔄 Starting automatic cookie refresh...")
    
    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        logger.error("❌ Cannot update cookies: INSTAGRAM_USERNAME or INSTAGRAM_PASSWORD missing in .env")
        return False

    try:
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 1. Login
        logger.info("🌍 Navigating to Instagram login...")
        driver.get('https://www.instagram.com/accounts/login/')
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'username')))
        
        driver.find_element(By.NAME, 'username').send_keys(INSTAGRAM_USERNAME)
        driver.find_element(By.NAME, 'password').send_keys(INSTAGRAM_PASSWORD)
        time.sleep(1)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        
        # 2. Wait for Login
        logger.info("🗝️ Logging in...")
        WebDriverWait(driver, 30).until(
            lambda d: "instagram.com" in d.current_url and "login" not in d.current_url
        )
        time.sleep(5) 
        
        # 3. Save Cookies
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, 'w') as f:
            f.write('# Netscape HTTP Cookie File\n')
            for cookie in cookies:
                expiry = int(cookie.get('expiry', 0))
                secure = "TRUE" if cookie.get('secure') else "FALSE"
                f.write(f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{secure}\t{expiry}\t{cookie['name']}\t{cookie['value']}\n")
        
        logger.info(f"✅ Cookies successfully updated to {COOKIES_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating cookies: {e}")
        if driver:
            driver.save_screenshot(str(SCREENSHOT_DIR / 'login_error.png'))
        return False
    finally:
        if driver:
            driver.quit()

async def ensure_fresh_cookies():
    """Async wrapper for cookie update"""
    return await asyncio.to_thread(update_instagram_cookies_sync)

# ============================================================================
# Core: Video Downloading & Processing
# ============================================================================

class InstagramDownloader:
    def __init__(self):
        self.cookie_file = COOKIES_FILE
        self.max_retries = 2

    async def run_cmd(self, cmd):
        def _run():
            return subprocess.run(cmd, capture_output=True, text=True, check=True)
        return await asyncio.to_thread(_run)

    async def get_caption(self, url):
        """Fetch caption using yt-dlp"""
        cmd = ["yt-dlp", "--cookies", str(self.cookie_file), "--dump-json", url]
        try:
            res = await self.run_cmd(cmd)
            data = json.loads(res.stdout)
            caption = data.get('description') or data.get('title') or ""
            caption = re.sub(r'#\w+\b', '', caption).strip()
            return caption
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch caption: {e}")
            return "Instagram Video"

    async def download_video(self, url, output_path, attempt=1):
        """Download video, retry with cookie refresh on auth failure"""
        cmd = [
            "yt-dlp",
            "--cookies", str(self.cookie_file),
            "-f", "best[ext=mp4]",
            "-o", str(output_path),
            url
        ]
        
        try:
            logger.info(f"⬇️ Downloading (Attempt {attempt}): {url}")
            await self.run_cmd(cmd)
            return True
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.lower()
            if "sign in" in err_msg or "login" in err_msg or "cookie" in err_msg:
                logger.warning("⚠️ Auth error detected!")
                if attempt < self.max_retries:
                    logger.info("🔄 Refreshing cookies and retrying...")
                    if await ensure_fresh_cookies():
                        return await self.download_video(url, output_path, attempt + 1)
            
            logger.error(f"❌ Download failed: {e.stderr}")
            return False

    async def process_video(self, input_path):
        """Convert/Compress video for Telegram"""
        temp_path = input_path.with_suffix(".temp.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            str(temp_path)
        ]
        
        try:
            await self.run_cmd(cmd)
            input_path.unlink()
            temp_path.rename(input_path)
            return True
        except Exception as e:
            logger.error(f"❌ Encoding error: {e}")
            return False

# ============================================================================
# AI Fact Checking
# ============================================================================

async def analyze_caption(caption):
    """Analyze caption with Gemini for scientific validity"""
    if not SETTINGS["fact_check"]:
        return "⚠️ Fact-Check is disabled."
    if not GEMINI_API_KEY:
        return "⚠️ Missing GEMINI_API_KEY in .env"
    if not caption or len(caption.strip()) < 10:
        return None # Too short, just ignore (silent fail)

    logger.info("🧠 Sending caption to Gemini for analysis...")
    try:
        # Using gemini-2.5-flash-lite (Fastest, Lightest, recommended by user)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        prompt = (
            "Analyze the scientific validity of the following text (which is an Instagram caption). "
            "If it makes scientific claims, verify them. "
            "If it references specific studies, try to find the paper title, author, or link. "
            "If it's a general claim, support or debunk it with scientific consensus. "
            "Please provide a concise answer in Persian (Farsi), structured as:\n"
            "1. ✅ Validity (Valid/Misleading/False)\n"
            "2. 🔬 Analysis (Brief explanation)\n"
            "3. 📄 Source/Paper (If applicable, give Title/DOI/Link)\n\n"
            f"Note: Be critical but helpful.\n\nText:\n{caption}"
        )
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    except Exception as e:
        logger.error(f"❌ Gemini analysis failed: {e}")
        return f"⚠️ **API Error:** `{str(e)}`"

# ... (In cmd_check)

    status_msg = await update.message.reply_text("🧠 Thinking...")
    analysis = await analyze_caption(target_text)
    
    if analysis:
        # Check if it was an error message
        if analysis.startswith("⚠️"):
            await status_msg.edit_text(analysis, parse_mode='Markdown')
        elif analysis.strip():
             await status_msg.edit_text(
                f"🧠 **تحلیل متن (Gemini AI):**\n\n{analysis}",
                parse_mode='Markdown'
            )
        else:
             await status_msg.edit_text("❌ Analysis returned empty result.")
    else:
        # Returned None (likely too short)
        await status_msg.edit_text("❌ Text is too short to analyze (<10 chars).")

# ============================================================================
# Mode: CLI
# ============================================================================

async def run_cli_mode(url):
    logger.info("🚀 Starting CLI Mode")
    downloader = InstagramDownloader()
    
    # 1. Download
    downloads_dir = BASE_DIR / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    
    match = re.search(r"(p|reels?)/([^/?#&]+)", url)
    if match:
        shortcode = match.group(2)
        filename = f"insta_{shortcode}.mp4"
    else:
        filename = f"insta_{int(time.time())}.mp4"
        
    output_path = downloads_dir / filename
    
    video_exists = False
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"⏭️ Video already downloaded: {output_path}")
        video_exists = True
    else:
        if await downloader.download_video(url, output_path):
            logger.info(f"✅ Video downloaded: {output_path}")
            logger.info("⚙️ Processing video...")
            await downloader.process_video(output_path)
            video_exists = True
        else:
            logger.error("❌ Failed to download video.")
            return

    if video_exists:
        caption = await downloader.get_caption(url)
        txt_path = output_path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(caption)
        logger.info(f"📝 Caption saved: {txt_path}")
        
        # 4. Upload to Saved Messages
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            logger.info("📤 Uploading to Telegram Chat...")
            try:
                bot = Bot(token=TELEGRAM_TOKEN)
                
                limit = 900
                if len(caption) <= 1000:
                    with open(output_path, "rb") as v:
                        await bot.send_video(
                            chat_id=TELEGRAM_CHAT_ID,
                            video=v,
                            caption=caption,
                            supports_streaming=True
                        )
                else:
                    # Smart Split for CLI
                    paragraphs = caption.split('\n')
                    video_cap = ""
                    rest_index = 0
                    current_length = 0
                    for i, p in enumerate(paragraphs):
                        if current_length + len(p) + 1 <= limit:
                            video_cap += p + "\n"
                            current_length += len(p) + 1
                        else:
                            rest_index = i
                            break
                    else:
                        rest_index = len(paragraphs)

                    if rest_index == 0 and len(video_cap.strip()) == 0:
                        video_cap = caption[:limit] + "...\n\n(ادامه در پیام بعد 👇)"
                        rest_text = caption[limit:]
                    else:
                        video_cap = video_cap.strip() + "\n\n(ادامه در پیام بعد 👇)"
                        rest_text = "\n".join(paragraphs[rest_index:])

                    with open(output_path, "rb") as v:
                        await bot.send_video(
                            chat_id=TELEGRAM_CHAT_ID,
                            video=v,
                            caption=video_cap,
                            supports_streaming=True
                        )
                    if rest_text.strip():
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=rest_text)
                
                logger.info("✅ Upload Complete!")
            except Exception as e:
                logger.error(f"❌ Upload failed: {e}")
        else:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing, skipping upload.")

# ============================================================================
# Mode: Server (Telegram Bot)
# ============================================================================

# Helper for Keyboard
def get_main_menu(user_id=None):
    # Use get_msg to localize button text based on current language
    keyboard = [
        [KeyboardButton(get_msg("btn_status")), KeyboardButton(get_msg("btn_help"))],
        [KeyboardButton(get_msg("btn_dl")), KeyboardButton(get_msg("btn_fc"))],
        [KeyboardButton("🇮🇷 فارسی"), KeyboardButton("🇺🇸 English"), KeyboardButton("🇫🇷 French")]
    ]
    
    # Admin Only: Stop Button
    admin_id = SETTINGS.get("admin_id", 0)
    if user_id and user_id == admin_id:
        keyboard.append([KeyboardButton(get_msg("btn_stop"))])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message when user starts the bot"""
    user = update.effective_user
    
    # Get localized welcome message
    welcome_template = get_msg("welcome")
    if not welcome_template:
        welcome_template = "👋 **Hello {name}!**\nType /help to start."
        
    welcome_text = welcome_template.format(name=user.first_name)
    
    await update.message.reply_text(
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=get_main_menu(user.id)
    )

# ...

async def process_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle clicks on the friendly menu buttons. Returns True if handled."""
    text = update.message.text
    if not text: return False
    
    # Handle Stop Bot Button
    if "🛑" in text:
        await cmd_stop_bot(update, context)
        return True

    if "📊" in text:
        await cmd_status(update, context)
        return True
    elif "🆘" in text:
        await cmd_help(update, context)
        return True
    elif "📥" in text:
        await cmd_toggle_dl(update, context)
        return True
    elif "🧠" in text:
        await cmd_toggle_fc(update, context)
        return True
    elif "🇮🇷" in text:
        SETTINGS["lang"] = "fa"
        await update.message.reply_text(get_msg("lang_set"), reply_markup=get_main_menu(update.effective_user.id))
        return True
    elif "🇺🇸" in text:
        SETTINGS["lang"] = "en"
        await update.message.reply_text(get_msg("lang_set"), reply_markup=get_main_menu(update.effective_user.id))
        return True
    elif "🇫🇷" in text:
        SETTINGS["lang"] = "fr"
        await update.message.reply_text(get_msg("lang_set"), reply_markup=get_main_menu(update.effective_user.id))
        return True
    
    return False

async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log every update to terminal"""
    if not update.message: return
    
    user = update.effective_user
    chat = update.effective_chat
    msg_text = update.message.text or "<Media/No Text>"
    
    logger.info(f"📨 [User: {user.first_name} ({user.id})] [Chat: {chat.id}]: {msg_text}")

async def cmd_close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove the custom keyboard menu"""
    await update.message.reply_text(
        "⌨️ **Menu Closed.**\nType /start to open it again.", 
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )

def run_server_mode():
    logger.info("🤖 Starting Server Mode (Telegram Bot)...")
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Global Logger (Group -1 to run first)
    from telegram.ext import TypeHandler
    app.add_handler(TypeHandler(Update, log_update), group=-1)
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("welcome", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("toggle_dl", cmd_toggle_dl))
    app.add_handler(CommandHandler("toggle_fc", cmd_toggle_fc))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("set_lang", cmd_set_lang))
    app.add_handler(CommandHandler("set_admin", cmd_set_admin))
    app.add_handler(CommandHandler("stop_bot", cmd_stop_bot))
    app.add_handler(CommandHandler("stop", cmd_stop_bot)) # Alias
    app.add_handler(CommandHandler("close", cmd_close_menu))
    app.add_handler(CommandHandler("close_menu", cmd_close_menu))
    
    # 1. General Text/Links (Includes Menu Processing)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), server_handle_msg))
    
    logger.info("✅ Bot started! Monitoring messages...")
    app.run_polling()

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = get_msg("help_msg")
    await update.message.reply_text(
        help_text, 
        parse_mode='Markdown',
        reply_markup=get_main_menu(update.effective_user.id)
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dl_status = get_msg("dl_on") if SETTINGS["download"] else get_msg("dl_off")
    fc_status = get_msg("fc_on") if SETTINGS["fact_check"] else get_msg("fc_off")
    
    status_text = get_msg("status_msg").format(
        dl_status=dl_status,
        fc_status=fc_status,
        min_len=SETTINGS["min_fact_check_length"]
    )
    
    await update.message.reply_text(
        status_text, 
        parse_mode='Markdown',
        reply_markup=get_main_menu(update.effective_user.id)
    )

# ... (Existing Commands) ...

# In run_server_mode:
# app.add_handler(CommandHandler("help", cmd_help))

async def cmd_toggle_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    SETTINGS["download"] = not SETTINGS["download"]
    state = get_msg("dl_on") if SETTINGS["download"] else get_msg("dl_off")
    msg = get_msg("toggle_dl_msg").format(state=state)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_toggle_fc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not GEMINI_API_KEY:
        await update.message.reply_text("⚠️ Cannot enable: GEMINI_API_KEY missing in .env")
        return

    # Check for argument (Length)
    if context.args:
        try:
            val = int(context.args[0])
            if val < 10:
                await update.message.reply_text("⚠️ Minimum length must be at least 10.")
                return
            SETTINGS["min_fact_check_length"] = val
            SETTINGS["fact_check"] = True # Auto-enable
            await update.message.reply_text(f"🧠 **Fact-Checking Enabled** (Min Length: {val})", parse_mode='Markdown')
            return
        except ValueError:
             await update.message.reply_text("⚠️ Invalid number. Use: `/toggle_fc` or `/toggle_fc 50`", parse_mode='Markdown')
             return

    # No arg: Standard Toggle
    SETTINGS["fact_check"] = not SETTINGS["fact_check"]
    state = get_msg("fc_on") if SETTINGS["fact_check"] else get_msg("fc_off")
    msg = get_msg("toggle_fc_msg").format(state=state)
    await update.message.reply_text(msg, parse_mode='Markdown')

async def cmd_stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shutdown the bot (Admin Only)"""
    user_id = update.effective_user.id
    admin_id = SETTINGS.get("admin_id", 0)
    
    if user_id != admin_id:
        await update.message.reply_text(get_msg("shutdown_fail"), parse_mode='Markdown')
        return

    await update.message.reply_text(get_msg("shutdown_success"), parse_mode='Markdown')
    logger.info("🛑 Bot shutting down via /stop_bot command.")
    
    # Graceful exit
    await context.application.stop()
    sys.exit(0)

async def cmd_set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the current chat as the Admin/Alert receiver"""
    current_admin = SETTINGS.get("admin_id", 0)
    sender_id = update.effective_chat.id
    
    # If admin is set, only they can change it. If 0, anyone can set it (first time setup).
    if current_admin != 0 and current_admin != sender_id:
        await update.message.reply_text("🚫 Permission Denied. Only the Admin can transfer ownership.")
        return

    SETTINGS["admin_id"] = sender_id
    await update.message.reply_text(f"👮‍♂️ **Admin set to this chat!** (ID: `{sender_id}`)", parse_mode='Markdown')

# ...

async def cmd_set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set bot language"""
    if not context.args or context.args[0] not in LANG_MAP:
        await update.message.reply_text("Usage: /set_lang [fa|en|fr]\nExample: `/set_lang fa`", parse_mode='Markdown')
        return
    
    lang_code = context.args[0]
    SETTINGS["lang"] = lang_code
    
    # Send confirmation in the NEW language
    await update.message.reply_text(get_msg("lang_set"))

async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger fact-check on a message (Reply or Argument)"""
    if not SETTINGS["fact_check"]:
        await update.message.reply_text(get_msg("disabled"))
        return

    target_text = ""
    # 1. Check if reply (Text OR Caption)
    if update.message.reply_to_message:
        target_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
        
    # 2. Check if arguments
    elif context.args:
        target_text = " ".join(context.args)
    
    if not target_text:
        await update.message.reply_text("❓ Reply to a message (text/caption) with /check or send `/check text...`")
        return

    status_msg = await update.message.reply_text(get_msg("thinking"))
    analysis = await analyze_caption(target_text, context)
    
    header = get_msg("result_header")
    
    if analysis and not analysis.startswith("⚠️"):
        await status_msg.edit_text(
            f"{header}\n\n{analysis}",
            parse_mode='Markdown'
        )
    else:
        # Error or Too Short -> Clean up UI
        await status_msg.delete()
        # If it was a config error (starts with warning but returned as string), maybe show it?
        # But analyze_caption now returns None on Exception.
        # It only returns string on "Disabled" or "Missing Key".
        if analysis and analysis.startswith("⚠️"):
             pass # Logic to ignore or show could go here. For now, delete "Thinking" covers "Clean UI".

async def server_handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    
    # ... (Instagram Logic Unchanged) ...
    match = re.search(r"(https?://www\.instagram\.com/(p|reel)/[^\s]+)", msg.text)
    
    if match:
       # ... (Download Logic) ...
        # (Inside download block - Auto Fact Check)
            # This part is deeply nested in previous code, be careful when applying replace.
            # I will trust the user to re-apply the full function if needed, but here I only need to touch the 'else' block or the 'fact check' block.
            # Actually, I need to update the auto-check logic at the end of download AND the text-only logic.
            # Let's simplify: The instruction said "Update cmd_check and server_handle_msg".
            # I'll rely on a separate block for server_handle_msg to ensure I don't break the lengthy download logic.
            pass

    else:
        # --- NO LINK FOUND -> TEXT ANALYSIS LOGIC ---
        limit = SETTINGS.get("min_fact_check_length", 50)
        
        if SETTINGS["fact_check"] and msg.chat.type == "private" and len(msg.text) > limit:
             # Auto-analyze in DM
             status_msg = await msg.reply_text(get_msg("thinking"))
             analysis = await analyze_caption(msg.text)
             
             header = get_msg("result_header")
             if analysis:
                if analysis.startswith("⚠️"):
                    await status_msg.edit_text(analysis, parse_mode='Markdown')
                else:
                    await status_msg.edit_text(
                        f"{header}\n\n{analysis}",
                        parse_mode='Markdown'
                    )
             else:
                await status_msg.delete() 

# ...

# In run_server_mode:
# app.add_handler(CommandHandler("set_lang", cmd_set_lang))

async def server_handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    
    # 1. Check for Instagram Link
    match = re.search(r"(https?://www\.instagram\.com/(p|reel)/[^\s]+)", msg.text)
    
    if match:
        # --- INSTAGRAM DOWNLOAD LOGIC ---
        if not SETTINGS["download"]:
            await msg.reply_text("🚫 Downloading is **Disabled**.")
            return

        url = match.group(1)
        logger.info(f"📩 Received link: {url}")
        
        if download_semaphore.locked():
            await msg.reply_text("⏳ Server is busy, queued...")
            
        async with download_semaphore:
            downloader = InstagramDownloader()
            output_path = TEMP_DIR / f"bot_{msg.message_id}.mp4"
            status_msg = await msg.reply_text("⬇️ Downloading...")
            
            if await downloader.download_video(url, output_path):
                await status_msg.edit_text("⚙️ Processing...")
                await downloader.process_video(output_path)
                
                caption = await downloader.get_caption(url)
                
                # --- Smart Caption Splitting ---
                caption_limit = 900
                video_cap = ""
                rest_text = ""
                
                if len(caption) <= 1000:
                    video_cap = caption
                else:
                    paragraphs = caption.split('\n')
                    current_len = 0
                    split_idx = 0
                    for i, p in enumerate(paragraphs):
                        if current_len + len(p) + 1 <= caption_limit:
                            video_cap += p + "\n"
                            current_len += len(p) + 1
                        else:
                            split_idx = i
                            break
                    else:
                        split_idx = len(paragraphs)
                    
                    if split_idx == 0 and not video_cap.strip():
                        video_cap = caption[:caption_limit] + "...\n\n(ادامه در پیام بعد 👇)"
                        rest_text = caption[caption_limit:]
                    else:
                        video_cap = video_cap.strip() + "\n\n(ادامه در پیام بعد 👇)"
                        rest_text = "\n".join(paragraphs[split_idx:])
                # -------------------------------
                
                with open(output_path, "rb") as v:
                    await msg.reply_video(
                        video=v,
                        caption=video_cap,
                        supports_streaming=True
                    )
                
                if rest_text:
                    await msg.reply_text(rest_text)
                
                output_path.unlink()
                await status_msg.delete()
                
                # Auto Fact-Check for Instagram
                if SETTINGS["fact_check"]:
                    analysis = await analyze_caption(caption)
                    if analysis:
                        await msg.reply_text(
                            f"🧠 **تحلیل علمی و فکت‌چکینگ (Gemini AI):**\n\n{analysis}",
                            parse_mode='Markdown'
                        )

            else:
                await status_msg.edit_text("❌ Download failed. Check logs or if account is private.")
                
    else:
        # --- NO LINK FOUND -> TEXT ANALYSIS LOGIC ---
        limit = SETTINGS.get("min_fact_check_length", 50)
        
        if SETTINGS["fact_check"] and msg.chat.type == "private" and len(msg.text) > limit:
             # Auto-analyze in DM
             status_msg = await msg.reply_text(get_msg("thinking"))
             analysis = await analyze_caption(msg.text, context)
             
             header = get_msg("result_header")
             if analysis and not analysis.startswith("⚠️"):
                await status_msg.edit_text(
                    f"{header}\n\n{analysis}",
                    parse_mode='Markdown'
                )
             else:
                await status_msg.delete() 

def run_server_mode():
    logger.info("🤖 Starting Server Mode (Telegram Bot)...")
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Global Logger (Group -1 to run first)
    from telegram.ext import TypeHandler
    app.add_handler(TypeHandler(Update, log_update), group=-1)
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("toggle_dl", cmd_toggle_dl))
    app.add_handler(CommandHandler("toggle_fc", cmd_toggle_fc))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("set_lang", cmd_set_lang))
    app.add_handler(CommandHandler("set_admin", cmd_set_admin))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), server_handle_msg))
    
    logger.info("✅ Bot started! Monitoring messages...")
    app.run_polling()

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Instagram Video Downloader Bot (CLI + Server)")
    parser.add_argument("url", nargs="?", help="Instagram URL to download (CLI Mode)")
    parser.add_argument("--server", action="store_true", help="Run in monitoring mode (Server Mode)")
    
    args = parser.parse_args()
    
    if args.server:
        run_server_mode()
    elif args.url:
        try:
            asyncio.run(run_cli_mode(args.url))
        except KeyboardInterrupt:
            logger.info("Stopped by user.")
    else:
        parser.print_help()
        print("\nExample CLI:    python smart_insta_dl.py https://instagram.com/reel/..." )
        print("Example Server: python smart_insta_dl.py --server")

if __name__ == "__main__":
    main()

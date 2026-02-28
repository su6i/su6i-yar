import os
import json
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from src.core.config import SETTINGS, STORAGE_DIR
from src.core.logger import logger
from src.features.downloader.utils import convert_cookies_json_to_netscape

# Import shared cache and handler for auto-resume
from src.core.handlers import PENDING_AUTH_URLS, global_message_handler

async def cookie_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles uploaded cookies.txt or cookies.json files from the admin.
    Automatically installs them to bypass anti-bot challenges like YouTube/Instagram.
    """
    msg = update.effective_message
    if not msg or not msg.document:
        return
        
    user_id = update.effective_user.id
    
    # Security check: Only admin can upload cookies
    if user_id != SETTINGS.get("admin_id"):
        return
        
    doc = msg.document
    if not doc.file_name:
        return
        
    fname = doc.file_name.lower()
    
    if fname in ["cookies.txt", "cookies.json"]:
        status_msg = await msg.reply_text("📥 در حال دریافت و نصب کوکی‌های جدید...")
        try:
            # Download file
            file = await context.bot.get_file(doc.file_id)
            target_path = Path(STORAGE_DIR) / fname
            await file.download_to_drive(custom_path=target_path)
            
            # Check content to see if it's JSON, regardless of extension
            content = target_path.read_text(encoding="utf-8").strip()
            if content.startswith("[") or content.startswith("{"):
                logger.info(f"🍪 Uploaded '{fname}' contains JSON, converting to Netscape...")
                # Write to a temp JSON file first so converter can read it
                temp_json_path = Path(STORAGE_DIR) / "cookies_temp.json"
                target_path.rename(temp_json_path)
                
                txt_path = Path(STORAGE_DIR) / "cookies.txt"
                convert_cookies_json_to_netscape(temp_json_path, txt_path)
                temp_json_path.unlink() # Cleanup
            else:
                # If it's not JSON, assume it's already Netscape format
                if target_path.name != "cookies.txt":
                    target_path.rename(Path(STORAGE_DIR) / "cookies.txt")
                logger.info("🍪 Installed explicit cookies.txt (Netscape format).")
            logger.info(f"🍪 New cookies installed by admin: {fname}")
            
            # Auto-resume download if a URL was pending
            pending_url = PENDING_AUTH_URLS.pop(user_id, None)
            if pending_url:
                await status_msg.edit_text("✅ کوکی‌ها با موفقیت روی سرور نصب شدند!\n\n🚀 در حال تلاش مجدد برای دانلود ویدیوی قبلی...")
                context.user_data["override_text"] = pending_url
                await global_message_handler(update, context)
            else:
                await status_msg.edit_text("✅ کوکی‌ها با موفقیت در فضای امن سرور ذخیره و روی موتور دانلود نصب شدند!\n\n🚀 حالا ربات به عنوان شما وارد وبسایت می‌شود. می‌توانید لینک ویدیوی قبلی را دوباره بفرستید.")
            
        except Exception as e:
            logger.error(f"Failed to install cookies: {e}")
            await status_msg.edit_text(f"❌ خطا در نصب کوکی‌ها:\n`{e}`")

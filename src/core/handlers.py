import os
import signal
import asyncio
import traceback
import html
import json
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.core.config import SETTINGS, ALLOWED_USERS, IS_DEV
from src.core.logger import logger
from src.core.database import USER_LANG, save_persistence
from src.core.access import check_access, check_daily_limit, increment_daily_usage, get_user_limit

from src.utils.text_tools import get_msg, extract_link_from_text
from src.utils.telegram import reply_and_delete, safe_delete, reply_with_countdown

from src.features.utility.utils import get_status_text, get_main_keyboard
from src.features.downloader.utils import download_instagram, download_video, detect_platform
from src.features.fact_check.utils import smart_reply, LAST_ANALYSIS_CACHE
from src.features.voice.utils import text_to_speech
from src.features.finance.handlers import cmd_price_handler
from src.services.gemini import analyze_text_gemini

async def global_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """MASTER HANDLER: Processes ALL text messages"""
    msg = update.effective_message
    if not msg or not msg.text: return
    text = msg.text.strip()
    user = update.effective_user
    user_id = user.id
    
    # Ensure User Lang
    if user_id not in USER_LANG:
        USER_LANG[user_id] = "fa"
    lang = USER_LANG[user_id]

    logger.info(f"📨 Message received request from {user.id} ({lang})")

    # --- 1. MENU COMMANDS (Check by Emoji/Start) --- 
    
    # Status
    if text.startswith("📊"):
        full_status = get_status_text(user_id)
        if msg.chat_id < 0:  # Group
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=full_status,
                    parse_mode=ParseMode.MARKDOWN
                )
                await reply_and_delete(update, context, get_msg("status_private_sent", user_id), delay=10)
            except Exception:
                await reply_and_delete(update, context, get_msg("status_private_error", user_id), delay=15)
        else:
            await reply_and_delete(update, context, full_status, delay=30, parse_mode=ParseMode.MARKDOWN)
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
            await msg.reply_text(get_msg("voice_no_text", user_id))
            return
        status_msg = await msg.reply_text(get_msg("voice_generating", user_id))
        try:
            audio_buffer = await text_to_speech(detail_text, lang)
            if audio_buffer:
                await msg.reply_voice(voice=audio_buffer, caption=get_msg("voice_caption", user_id))
                await safe_delete(status_msg)
            else:
                await status_msg.edit_text(get_msg("voice_error", user_id))
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            await status_msg.edit_text(get_msg("voice_error", user_id))
        return
        
    # Help
    if text.startswith("ℹ️") or text.startswith("🆘"):
        # Use monospace help for all languages if available (not in text_tools currently, maybe added later)
        # Fallback to standard help
        help_text = get_msg("help_msg", user_id)
        await reply_with_countdown(update, context, help_text, delay=60, parse_mode=ParseMode.MARKDOWN)
        return

    # Price Check
    if any(keyword in text for keyword in ["قیمت ارز و طلا", "Currency & Gold", "Devises & Or", "환율 및 금 시세"]):
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

    # --- 2. SUPPORTED VIDEO LINK CHECK (Instagram / YouTube / Aparat) ---
    platform = detect_platform(text)
    if platform != "unknown":
        if not SETTINGS["download"]:
            await msg.reply_text("⚠️ " + get_msg("dl_off", user_id))
            return

        platform_label = {"instagram": "Instagram", "youtube": "YouTube", "aparat": "Aparat"}.get(platform, "video")
        status_msg = await msg.reply_text(
            get_msg("downloading", user_id),
            reply_to_message_id=msg.message_id
        )

        path = await download_video(text)
        success = False
        if path and path.exists():
            try:
                await msg.reply_video(
                    video=open(path, 'rb'),
                    caption=f"🎥 {platform_label} | @Su6i_Yar_Bot",
                    supports_streaming=True,
                    reply_to_message_id=msg.message_id
                )
                success = True
                path.unlink()
            except Exception as e:
                logger.error(f"Send Video Error ({platform_label}): {e}")

        if success:
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
        
        # Pass status_msg to analyze_text_gemini (it uses StatusUpdateCallback)
        response = await analyze_text_gemini(text, status_msg, lang, user_id)
        
        # Increment usage and get remaining
        remaining = increment_daily_usage(user_id)
        
        await smart_reply(msg, status_msg, response, user_id, lang)
        
        # Show remaining requests (skip for admin)
        if user_id != SETTINGS["admin_id"]:
            limit = get_user_limit(user_id)
            await msg.reply_text(
                get_msg("remaining_requests", user_id).format(remaining=remaining, limit=limit),
                reply_to_message_id=status_msg.message_id
            )
        return

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a list of strings
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Split message if too long
    if len(message) > 4000:
        message = message[:4000] + "... (truncated)"
        
    admin_id = SETTINGS.get("admin_id")
    if admin_id:
        try:
            await context.bot.send_message(chat_id=admin_id, text=message, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send error report: {e}")

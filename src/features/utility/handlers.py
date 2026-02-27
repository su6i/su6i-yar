from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.core.config import SETTINGS
from src.core.logger import logger
from src.utils.text_tools import get_msg
from src.utils.telegram import reply_and_delete, reply_with_countdown
from src.features.utility.utils import get_status_text, get_main_keyboard

async def cmd_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main keyboard."""
    logger.info(f"🚀 Command /start triggered by {update.effective_user.id}")
    user = update.effective_user
    text = get_msg("welcome", user.id).format(name=user.first_name)
    
    # Use reply_with_countdown for welcome message in group, or just reply in private
    # Original code used reply_with_countdown.
    # But wait, reply_with_countdown only counts down in groups.
    # In private chat it just replies (and returns msg).
    
    await reply_with_countdown(
        update, 
        context, 
        text, 
        delay=60, 
        parse_mode=ParseMode.MARKDOWN, 
        reply_markup=get_main_keyboard(user.id)
    )

async def cmd_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    user_id = update.effective_user.id
    # Use reply_and_delete to keep chat clean
    await reply_and_delete(
        update, 
        context, 
        get_msg("help_msg", user_id), 
        delay=60, 
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system status and user quota"""
    logger.info("📊 Command /status triggered")
    user_id = update.effective_user.id
    
    full_status = get_status_text(user_id)
    await reply_with_countdown(
        update, 
        context, 
        full_status, 
        delay=30, 
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_close_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove keyboard and close menu"""
    logger.info("❌ Command /close triggered")
    user_id = update.effective_user.id
    await reply_and_delete(
        update, 
        context, 
        get_msg("menu_closed", user_id), 
        delay=5, 
        reply_markup=ReplyKeyboardRemove()
    )

async def cmd_toggle_dl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle downloader feature (Admin/Global setting)"""
    logger.info("📥 Command /toggle_dl triggered")
    # Note: Authorization check should ideally be here if not handled by decorator
    # The original code just toggled. Assuming access control is separate or permissive for mechanics.
    # But wait, modifying global settings usually requires admin?
    # In original `su6i_yar.py`, there was no explicit admin check inside the handler, 
    # but maybe the handler was added with a filter?
    # Let's assume for now we port logic as is.
    
    SETTINGS["download"] = not SETTINGS["download"]
    state = get_msg("dl_on", update.effective_user.id) if SETTINGS["download"] else get_msg("dl_off", update.effective_user.id)
    await reply_and_delete(
        update, 
        context, 
        get_msg("action_dl", update.effective_user.id).format(state=state), 
        delay=10
    )

async def cmd_toggle_fc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle fact-check feature (Admin/Global setting)"""
    logger.info("🧠 Command /toggle_fc triggered")
    SETTINGS["fact_check"] = not SETTINGS["fact_check"]
    state = get_msg("fc_on", update.effective_user.id) if SETTINGS["fact_check"] else get_msg("fc_off", update.effective_user.id)
    await reply_and_delete(
        update, 
        context, 
        get_msg("action_fc", update.effective_user.id).format(state=state), 
        delay=10
    )

async def cmd_stop_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin only: Stop the bot process."""
    user_id = update.effective_user.id
    if user_id != SETTINGS["admin_id"]:
        await update.message.reply_text(get_msg("only_admin", user_id))
        return
        
    logger.info("🛑 Stop Button Triggered")
    await update.message.reply_text(get_msg("bot_stop", user_id), reply_markup=ReplyKeyboardRemove())
    
    import os, signal, asyncio
    await asyncio.sleep(1)
    os.kill(os.getpid(), signal.SIGKILL)

async def cmd_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches the cached detailed analysis."""
    from src.features.fact_check.utils import LAST_ANALYSIS_CACHE
    
    logger.info("🔍 Command /detail triggered")
    msg = update.effective_message
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

    # Chunking logic
    max_length = 3900
    if len(detail_text) <= max_length:
        await msg.reply_text(detail_text, parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_target_id)
    else:
        # Simple splitting
        parts = []
        while detail_text:
            if len(detail_text) <= max_length:
                parts.append(detail_text)
                break
            # Find nearest newline
            split_idx = detail_text.rfind('\n', 0, max_length)
            if split_idx == -1: split_idx = max_length
            parts.append(detail_text[:split_idx])
            detail_text = detail_text[split_idx:]
            
        for i, chunk in enumerate(parts):
            await msg.reply_text(f"📄 بخش {i+1}/{len(parts)}\n\n{chunk}", parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_target_id)

async def cmd_fun_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process media/links for the Fun channel."""
    from src.utils.text_tools import extract_link_from_text
    from src.features.downloader.utils import download_instagram
    import os
    
    msg = update.effective_message
    user_id = update.effective_user.id
    is_target_channel = (msg.chat.username == "just_for_fun_persian")
    
    # Only Admin or Channel can use this
    if not is_target_channel and user_id != SETTINGS["admin_id"]:
        return

    # Determine Target (File or URL)
    target_file = msg.video or msg.animation or (msg.document if msg.document and msg.document.mime_type and msg.document.mime_type.startswith("video/") else None)
    target_url = None
    
    if not target_file:
        text_content = msg.caption or msg.text or ""
        target_url = extract_link_from_text(msg.caption_entities or msg.entities, text_content)
        
        # Check reply
        if not target_url and msg.reply_to_message:
            reply = msg.reply_to_message
            target_file = reply.video or reply.animation or (reply.document if reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/") else None)
            if not target_file:
                target_url = extract_link_from_text(reply.caption_entities or reply.entities, reply.caption or reply.text or "")

    if not target_url and not target_file:
        if msg.text and msg.text.startswith("/fun"):
             await msg.reply_text("❌ خطا: نه لینک پیدا کردم نه فایل!", reply_to_message_id=msg.message_id)
        return

    target_channel_id = "@just_for_fun_persian"
    custom_header = "🎥 <b>Just For Fun</b> | @just_for_fun_persian"
    status_msg = None

    if is_target_channel:
        await safe_delete(msg)
    else:
        status_msg = await msg.reply_text("📥 در حال پردازش...", reply_to_message_id=msg.message_id)

    try:
        # Case 1: File
        if target_file:
            # Forward directly if possible or re-upload? 
            # Re-upload to add caption
            # For now, simplistic approach: Copy message
            await context.bot.copy_message(
                chat_id=target_channel_id,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id if msg.video else (msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id),
                caption=custom_header,
                parse_mode=ParseMode.HTML
            )
            if status_msg: await status_msg.edit_text(f"✅ پست شد: {target_channel_id}")
            return

        # Case 2: URL
        if target_url:
            path = await download_instagram(target_url)
            if path and path.exists():
                await context.bot.send_video(
                    chat_id=target_channel_id,
                    video=open(path, 'rb'),
                    caption=custom_header,
                    parse_mode=ParseMode.HTML,
                    read_timeout=120, 
                    write_timeout=120, 
                    pool_timeout=120
                )
                path.unlink() # Cleanup
                if status_msg: await status_msg.edit_text(f"✅ پست شد: {target_channel_id}")
            else:
                if status_msg: await status_msg.edit_text("❌ دانلود ناموفق.")
                
    except Exception as e:
        logger.error(f"Fun Error: {e}")
        if status_msg: await status_msg.edit_text(f"❌ خطا: {e}")

async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-process posts in @just_for_fun_persian"""
    msg = update.channel_post
    if not msg: return
    
    if msg.chat.username != "just_for_fun_persian":
        return
        
    text_content = msg.caption or msg.text or ""
    if "Just For Fun" in text_content:
        return # Loop protection

    # Check media/link
    has_media = msg.video or msg.animation or (msg.document and msg.document.mime_type and msg.document.mime_type.startswith("video/"))
    has_link = "http" in text_content
    
    if has_media or has_link:
        await cmd_fun_handler(update, context)


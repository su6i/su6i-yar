from telegram import Update
from telegram.ext import ContextTypes
from src.core.config import SETTINGS
from src.core.database import USER_LANG
from src.core.access import check_access, check_daily_limit, get_user_limit, increment_daily_usage
from src.core.logger import logger
from src.utils.text_tools import get_msg
from src.utils.telegram import safe_delete, reply_and_delete
from src.services.gemini import analyze_text_gemini
from src.features.fact_check.utils import smart_reply, LAST_ANALYSIS_CACHE

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
        if remaining % 2 == 0: # Reduce spam, show every other time? Or always? Logic in original was always.
             await reply_and_delete(update, context, f"📊 {remaining}/{limit} {get_msg('limit_remaining_count', user_id)}", delay=15, reply_to_message_id=status_msg.message_id)


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

    # Smart chunking
    max_length = 3900
    
    if len(detail_text) <= max_length:
        try:
            await msg.reply_text(detail_text, parse_mode='Markdown', reply_to_message_id=reply_target_id)
        except Exception:
            await msg.reply_text(detail_text, parse_mode=None, reply_to_message_id=reply_target_id)
    else:
        chunks = [detail_text[i:i+max_length] for i in range(0, len(detail_text), max_length)]
        for chunk in chunks:
             try:
                await msg.reply_text(chunk, parse_mode='Markdown', reply_to_message_id=reply_target_id)
             except Exception:
                await msg.reply_text(chunk, parse_mode=None, reply_to_message_id=reply_target_id)

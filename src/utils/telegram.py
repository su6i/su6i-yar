from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import logging
import asyncio

logger = logging.getLogger(__name__)

async def safe_delete(message):
    """Safely delete a message without crashing on BadRequest"""
    if not message: return
    try:
        await message.delete()
    except Exception:
        # Silently ignore deletion errors (common in groups)
        pass

async def delete_scheduled_message(context: ContextTypes.DEFAULT_TYPE):
    """
    Job Queue Callback: Safely deletes a message.
    Expects `context.job.data` to be a dict with `chat_id` and `message_id`.
    """
    job_data = context.job.data
    chat_id = job_data.get("chat_id")
    message_id = job_data.get("message_id")
    
    if not chat_id or not message_id:
        return

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

async def reply_and_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, delay: int = 15, **kwargs):
    """Reply to user and delete both request & response after delay."""
    try:
        msg = await update.message.reply_text(text, **kwargs)
        
        # Schedule deletion
        context.job_queue.run_once(
            delete_scheduled_message, 
            delay, 
            data={"chat_id": msg.chat_id, "message_id": msg.message_id}
        )
        
        # Also delete user's command
        context.job_queue.run_once(
            delete_scheduled_message, 
            delay, 
            data={"chat_id": update.message.chat_id, "message_id": update.message.message_id}
        )
        return msg

    except Exception as e:
        logger.error(f"Reply & Delete Error: {e}")
        return None

from src.core.config import SETTINGS

async def report_error_to_admin(context: ContextTypes.DEFAULT_TYPE, user_id: int, command: str, error_msg: str):
    """
    Silently reports an error to the admin instead of spamming the group.
    """
    admin_id = SETTINGS.get("admin_id")
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

    except Exception as e:
        logger.error(f"Failed to send error report to admin: {e}")

async def reply_with_countdown(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, delay: int = 60, **kwargs):
    """
    Reply to message with countdown timer (only in groups).
    Returns the reply message object.
    """
    msg = update.effective_message
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

async def schedule_countdown_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, user_message_id: int, 
                                   original_text: str, total_seconds: int = 60, parse_mode: str = 'Markdown'):
    """
    Updates message with countdown timer and deletes after time expires.
    """
    intervals = [50, 40, 30, 20, 10]
    
    elapsed = 0
    # Logic in original was checking if remaining < total, and sleeping.
    # Simplified logic: just update occasionally.
    # Original logic:
    # for remaining in intervals:
    #    if remaining < total_seconds:
    #       sleep_time = (total_seconds - remaining) - elapsed
    #       if sleep_time > 0: await asyncio.sleep(sleep_time); elapsed += sleep_time
    #       ... edit message ...
    
    # We can copy the logic exactly.
    for remaining in intervals:
        if remaining < total_seconds:
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
            except Exception:
                pass
    
    # Final sleep
    remaining_time = total_seconds - elapsed
    if remaining_time > 0:
        await asyncio.sleep(remaining_time)
    
    # Delete bot message
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
    
    # Delete user message
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=user_message_id)
    except Exception:
        pass



from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
import asyncio

from src.utils.text_tools import get_msg
from src.utils.telegram import reply_and_delete, schedule_countdown_delete, report_error_to_admin
from src.features.finance.utils import fetch_market_data

async def cmd_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /price command and button"""
    msg = update.effective_message
    user_id = update.effective_user.id
    
    status_msg = await reply_and_delete(update, context, get_msg("price_loading", user_id), delay=60)
    
    data = await fetch_market_data()
    if not data:
        error_text = get_msg("price_error", user_id)
        if status_msg:
             await status_msg.edit_text(error_text)
        else:
             await msg.reply_text(error_text)
             
        await report_error_to_admin(context, user_id, "/price", "Scraper Failure")
        return

    price_text = get_msg("price_msg", user_id).format(**data)
    
    if status_msg:
        await status_msg.edit_text(price_text, parse_mode=ParseMode.MARKDOWN)
        
        # Auto-delete with countdown in groups
        if msg.chat.id < 0:  # Group chat
            asyncio.create_task(
                schedule_countdown_delete(
                    context=context,
                    chat_id=msg.chat.id,
                    message_id=status_msg.message_id,
                    user_message_id=msg.message_id,
                    original_text=price_text,
                    total_seconds=60,
                    parse_mode=ParseMode.MARKDOWN
                )
            )
    else:
        # If reply_and_delete failed to return msg (e.g. error), send fresh one
        # But reply_and_delete only returns None on error.
        # If it returns None, it means it failed to send message? Or just failed to schedule?
        # My implementation returns None on Exception.
        pass

from telegram import Update
from telegram.ext import ContextTypes
import asyncio

from src.core.config import SETTINGS
from src.core.database import USER_LANG
from src.core.logger import logger
from src.utils.text_tools import get_msg, LANG_ALIASES
from src.utils.telegram import reply_and_delete, safe_delete
from src.services.translator import detect_language, translate_text, LANG_NAMES
from src.features.voice.utils import text_to_speech
from src.features.fact_check.utils import LAST_ANALYSIS_CACHE

async def cmd_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send voice version of replied message or last analysis.
    Usage: /voice [language]
    """
    msg = update.effective_message
    user_id = update.effective_user.id
    
    # Check for language argument
    explicit_target = None
    if context.args:
        lang_arg = context.args[0].lower()
        if lang_arg in LANG_ALIASES:
            explicit_target = LANG_ALIASES[lang_arg]
    
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
        reply_target_id = msg.message_id 
    
    if not target_text:
        await reply_and_delete(update, context, get_msg("voice_no_text", user_id), delay=10)
        return

    # Delete command in groups
    if msg.chat_id < 0:
        await safe_delete(msg)

    # Decide target language and translation need
    if explicit_target:
        target_lang = explicit_target
        source_lang = await detect_language(target_text)
        need_translation = target_lang != source_lang
    else:
        target_lang = await detect_language(target_text)
        need_translation = False
    
    try:
        # 1. Translate if needed
        voice_reply_to = reply_target_id
        if need_translation:
            status_msg = await context.bot.send_message(
                chat_id=msg.chat_id,
                text=get_msg("voice_translating", user_id).format(lang=LANG_NAMES.get(target_lang, target_lang)),
                reply_to_message_id=reply_target_id
            )
            translated_text = await translate_text(target_text, target_lang)
            await status_msg.edit_text(get_msg("voice_generating", user_id))
            target_text = translated_text
            
            # Update status msg content to avoid confusion or delete it?
            # Original code edited status_msg. 
            # We can use status_msg to reply with voice later?
            # Or just reply to original and delete status_msg.
            # Let's keep status_msg for now.
        else:
             status_msg = await context.bot.send_message(
                chat_id=msg.chat_id,
                text=get_msg("voice_generating", user_id),
                reply_to_message_id=reply_target_id
            )
            
        # 2. Generate Audio
        audio_buffer = await text_to_speech(target_text, target_lang)
        
        if audio_buffer:
            caption = f"🗣️ <b>Voice ({LANG_NAMES.get(target_lang, target_lang)})</b>"
            await context.bot.send_voice(
                chat_id=msg.chat_id, 
                voice=audio_buffer, 
                caption=caption, 
                parse_mode='HTML',
                reply_to_message_id=reply_target_id
            )
            await safe_delete(status_msg)
        else:
           await status_msg.edit_text(get_msg("err_api", user_id))
            
    except Exception as e:
        logger.error(f"Voice Command Error: {e}")
        if 'status_msg' in locals():
            await safe_delete(status_msg)
        await reply_and_delete(update, context, get_msg("err_api", user_id), delay=15)

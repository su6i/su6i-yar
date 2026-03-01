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
    
    # Check for language and gender arguments
    explicit_target = None
    explicit_gender = "male" # Default gender
    args_copy = list(context.args) if context.args else []
    
    # 1. Look for gender keyword
    if "female" in args_copy:
        explicit_gender = "female"
        args_copy.remove("female")
    elif "male" in args_copy:
        explicit_gender = "male"
        args_copy.remove("male")
        
    # 2. Look for language alias
    if args_copy:
        lang_arg = args_copy[0].lower()
        if lang_arg in LANG_ALIASES:
            explicit_target = LANG_ALIASES[lang_arg]
            args_copy.pop(0)
    
    # Priority 1: Check if replied to a message
    target_text = ""
    reply_target_id = msg.message_id
    if msg.reply_to_message:
        target_text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
        reply_target_id = msg.reply_to_message.message_id
    
    # Priority 2: Check for direct text input
    if not target_text and args_copy:
        target_text = " ".join(args_copy)
    
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
        voice_reply_to = reply_target_id
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        import json
        
        # --- MULTI-MODEL COMPARISON (PERSIAN ONLY) ---
        if target_lang == "fa":
            await context.bot.send_message(
                chat_id=msg.chat_id, 
                text="🧪 <b>تست مقایسه موتورهای صوتی (۲ مدل)</b>", 
                parse_mode="HTML", 
                reply_to_message_id=voice_reply_to
            )
            
            # Model 1: Datacula (Amir - Male)
            try:
                import httpx
                import io
                from src.features.voice.utils import DATACULA_API_URL
                from src.utils.text_tools import clean_text_strict
                
                clean_text = clean_text_strict(target_text)
                params = {"text": clean_text[:2000], "model_name": "امیر"}
                
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.get(DATACULA_API_URL, params=params)
                
                if response.status_code == 200 and len(response.content) > 1000:
                    audio_amir = io.BytesIO(response.content)
                    caption_amir = "🗣️ <b>مدل ۱: Datacula (امیر)</b> - آنلاین"
                    await context.bot.send_voice(chat_id=msg.chat_id, voice=audio_amir, caption=caption_amir, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Datacula Fail in handler: {e}")

            # Model 2: EdgeTTS (Dilara - Female) -> So the user actually hears a different voice!
            try:
                audio_edge = await text_to_speech(target_text, "fa", "female")
                if audio_edge:
                    caption_edge = "🗣️ <b>مدل ۲: EdgeTTS (دیلارا)</b> - مایکروسافت"
                    await context.bot.send_voice(chat_id=msg.chat_id, voice=audio_edge, caption=caption_edge, parse_mode='HTML')
            except Exception as e:
                logger.error(f"EdgeTTS Fail in handler: {e}")
                
            await safe_delete(status_msg)
            return # Exit after sending comparison

        # --- STANDARD SINGLE VOICE (NON-PERSIAN) ---
        # Default to male voice
        audio_buffer = await text_to_speech(target_text, target_lang, "male")
        
        if audio_buffer:
            caption = f"🗣️ <b>Voice ({LANG_NAMES.get(target_lang, target_lang)})</b>"
            
            # Add voice toggle buttons
            # We compress the text to fit in callback_data limit (64 bytes). 
            # If text is too long, we can't easily pass it. Better to just pass target_lang and gender toggle.
            # But we don't have a DB for state here, so let's stick to simple implementation without inline buttons for now, 
            # Or pass a hash if we had a cache. Since we have LAST_ANALYSIS_CACHE, we could use that, but it's complex for arbitrary replies.
            # The User specifically asked for a single voice explicitly (or 2 models for Persian).
            # I will omit the callback buttons for now because Telegram limits callback_data to 64 bytes, 
            # and caching arbitrary user messages just for voice toggling is overkill. The 2-model Persian split covers their main use case.

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

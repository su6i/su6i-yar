from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
import asyncio
import json
import os

import fal_client

from src.core.config import SETTINGS
from src.core.database import USER_LANG, save_persistence
from src.core.logger import logger
from src.core.access import check_daily_limit, increment_daily_usage
from src.utils.text_tools import get_msg, LANG_ALIASES
from src.utils.telegram import safe_delete
from src.services.gemini import get_smart_chain
from src.features.learning.state import LEARN_WAITERS, LEARN_LOCK, SEARCH_FILE_ID, SEARCH_GIF_FALLBACK
from src.features.learning.utils import refresh_learn_queue

LANG_NAMES = {
    "fa": "Persian", "en": "English", "fr": "French", "ko": "Korean",
    "de": "German", "es": "Spanish", "it": "Italian", "ru": "Russian",
    "ja": "Japanese", "zh": "Chinese", "ar": "Arabic", "tr": "Turkish"
}


async def _generate_image(prompt: str) -> str | None:
    """
    Generate one image via fal.ai flux/schnell ($0.003/image).
    Returns a URL string, or None on failure.
    """
    try:
        result = await fal_client.run_async(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": prompt,
                "image_size": "square_hd",
                "num_images": 1,
                "enable_safety_checker": True,
            },
        )
        return result["images"][0]["url"]
    except Exception as e:
        logger.warning(f"fal.ai image gen failed: {e}")
        return None

async def cmd_learn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Educational tutor: 1 variation with fal.ai image, definition, and example sentence."""
    msg = update.effective_message
    user_id = update.effective_user.id
    
    # Ensure User Lang is initialized immediately
    if user_id not in USER_LANG:
        USER_LANG[user_id] = "fa"
    user_lang = USER_LANG[user_id]
    
    # Check Daily Limit
    has_quota, _ = check_daily_limit(user_id)
    if not has_quota:
        await msg.reply_text(get_msg("learn_quota_exceeded", user_id))
        return

    # Extract target text and language
    target_text = ""
    target_lang = user_lang # Default to user's app language
    
    if msg.reply_to_message:
        target_text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
        if context.args:
            lang_arg = context.args[0].lower()
            if lang_arg in LANG_ALIASES:
                target_lang = LANG_ALIASES[lang_arg]
    elif context.args:
        # Check if first arg is a language code/alias
        lang_arg = context.args[0].lower()
        if lang_arg in LANG_ALIASES:
            target_lang = LANG_ALIASES[lang_arg]
            target_text = " ".join(context.args[1:])
        else:
            target_text = " ".join(context.args)

    if not target_text:
        await msg.reply_text(get_msg("learn_no_text", user_id))
        return

    # 3. Queue Management & Status Message
    original_msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id
    
    # Need to modify global SEARCH_FILE_ID
    # Since we imported it, 'SEARCH_FILE_ID' is local name unless we use src.features.learning.state.SEARCH_FILE_ID
    from src.features.learning import state as learning_state

    try:
        status_msg = await msg.reply_animation(
            animation=learning_state.SEARCH_FILE_ID or SEARCH_GIF_FALLBACK,
            caption=f"🪄 {get_msg('learn_designing', user_id)}",
            reply_to_message_id=original_msg_id,
            parse_mode=ParseMode.MARKDOWN
        )
        # Capture file_id for next time
        if not learning_state.SEARCH_FILE_ID and status_msg.animation:
            learning_state.SEARCH_FILE_ID = status_msg.animation.file_id
            # Log or save if needed (in original code it saved persistence)
            logger.info(f"🚀 Captured and cached Search GIF file_id: {learning_state.SEARCH_FILE_ID}")
    except Exception as e:
        logger.error(f"GIF status failed: {e}")
        status_msg = await msg.reply_text(get_msg("learn_designing", user_id), reply_to_message_id=original_msg_id)
    
    # Add to waiters and refresh positions
    waiter_entry = {"user_id": user_id, "status_msg": status_msg, "lang": user_lang}
    LEARN_WAITERS.append(waiter_entry)
    await refresh_learn_queue()

    # 4. Wait for Global Lock
    async with LEARN_LOCK:
        try:
            await refresh_learn_queue()
        except: pass
            
        try:
            # 4. Educational AI Call
            increment_daily_usage(user_id) # Consumes quota upon processing start
            
            logger.info(f"🤖 Step 1: Requesting deep educational content from AI in {target_lang}...")
            lang_name = LANG_NAMES.get(target_lang, target_lang)
            explanation_lang = "Persian" if user_lang == "fa" else ("English" if user_lang == "en" else ("French" if user_lang == "fr" else "Korean"))
            chain = get_smart_chain(grounding=False)
            
            educational_prompt = (
                f"SYSTEM ROLE: You are a linguistic tutor. Your student's interface language is '{explanation_lang}'.\n\n"
                f"CORE TASK: The student wants to learn about the concept: '{target_text}' in '{target_lang}'.\n\n"
                f"STRICT LANGUAGE MAPPING:\n"
                f"1. 'word': MUST be the translation of '{target_text}' into '{target_lang}'.\n"
                f"2. 'sentence': MUST be a complete example sentence ONLY in '{target_lang}'.\n"
                f"3. 'meaning': MUST be a definition/explanation written ONLY in '{explanation_lang}'.\n"
                f"4. 'translation': MUST be the translation of the 'sentence' (field #2) ONLY into '{explanation_lang}'.\n\n"
                f"Return ONLY valid JSON in this structure:\n"
                f"{{\n"
                f"  \"valid\": true,\n"
                f"  \"lang\": \"detected language\",\n"
                f"  \"dict\": \"source dictionary\",\n"
                f"  \"suggestion\": \"correction if any\",\n"
                f"  \"slides\": [\n"
                f"    {{\n"
                f"      \"word\": \"...\",\n"
                f"      \"phonetic\": \"...\",\n"
                f"      \"meaning\": \"...\",\n"
                f"      \"sentence\": \"...\",\n"
                f"      \"translation\": \"...\",\n"
                f"      \"prompt\": \"Highly detailed English visual description for AI image generator.\",\n"
                f"      \"keywords\": \"3-4 English keywords\"\n"
                f"    }}\n"
                f"  ]\n"
                f"}}\n"
                f"IMPORTANT: 'slides' must contain EXACTLY 1 object.\n"
                f"REPLY ONLY WITH JSON."
            )
            
            ai_resp = await chain.ainvoke(educational_prompt)
            raw_text = ai_resp.content.replace('```json', '').replace('```', '').strip()
            data = json.loads(raw_text)
            
            slides = data.get("slides", [])
            if not slides:
                raise ValueError("No slides in AI response")
            slide = slides[0]

            # Generate image with fal.ai flux/schnell
            img_prompt = slide.get("prompt", f"educational illustration {target_text}")
            image_url = await _generate_image(img_prompt)

            caption = (
                f"🎓 *{slide.get('word')}* `/{slide.get('phonetic')}/`\n\n"
                f"📝 *{get_msg('learn_fallback_meaning', user_id)}:*\n{slide.get('meaning')}\n\n"
                f"🗣 *{get_msg('learn_example_sentence', user_id)}:*\n`{slide.get('sentence')}`\n"
                f"_{slide.get('translation')}_"
            )

            try:
                if image_url:
                    await msg.reply_photo(photo=image_url, caption=caption, parse_mode=ParseMode.MARKDOWN)
                else:
                    await msg.reply_text(caption, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.warning(f"Photo send failed: {e}")
                await msg.reply_text(caption, parse_mode=ParseMode.MARKDOWN)

            await safe_delete(status_msg)
            
        except Exception as e:
            logger.error(f"Learning Error: {e}")
            await status_msg.edit_text(get_msg("learn_error", user_id))
            
    # Cleanup Waiter
    if waiter_entry in LEARN_WAITERS:
        LEARN_WAITERS.remove(waiter_entry)
        await refresh_learn_queue()

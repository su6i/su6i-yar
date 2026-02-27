from telegram import Message
import asyncio
from src.core.logger import logger
from src.utils.text_tools import get_msg

# In-memory cache for detailed analysis
LAST_ANALYSIS_CACHE = {} 

async def smart_reply(msg: Message, status_msg: Message, response: str, user_id: int, lang: str):
    """
    Handles the 2-part split response from AI (Summary + Detail).
    """
    if not response:
        await status_msg.edit_text(get_msg("err_api", user_id))
        return

    # 1. Check for Irrelevant
    if "|||IRRELEVANT|||" in response.upper():
        await status_msg.edit_text(get_msg("irrelevant_msg", user_id))
        return

    # 2. Extract Text (if LangChain object)
    if hasattr(response, 'content'):
        full_content = response.content
    else:
        full_content = str(response)

    # 3. Format Model Header
    header = get_msg("analysis_header", user_id).format(model="Gemini 2.0 Flash")
    footer = get_msg("analysis_footer_note", user_id)

    # 4. Split Parts
    if "|||SPLIT|||" in full_content:
        parts = full_content.split("|||SPLIT|||")
        summary = parts[0].strip()
        detail = parts[1].strip()
        
        # Cache detailed analysis
        LAST_ANALYSIS_CACHE[user_id] = f"{header}\n\n{detail}"
        logger.info(f"💾 Cached detail for user {user_id}")
    else:
        summary = full_content
        logger.warning("⚠️ No split marker found in response")
        LAST_ANALYSIS_CACHE[user_id] = "⚠️ جزئیات بیشتری در دسترس نیست"

    # 5. Send Summary
    final_text = f"{header}\n\n{summary}{footer}"
    
    # Chunk long messages
    max_length = 4000
    if len(final_text) > max_length:
        chunks = [final_text[i:i+max_length] for i in range(0, len(final_text), max_length)]
        for i, chunk in enumerate(chunks):
            if i == 0:
                await status_msg.edit_text(chunk, parse_mode='Markdown')
            else:
                await msg.reply_text(chunk, parse_mode='Markdown')
    else:
        await status_msg.edit_text(final_text, parse_mode='Markdown')

    logger.info(f"✅ Analysis sent to {user_id}")


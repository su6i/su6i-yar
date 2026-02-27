import re
from langchain_core.messages import HumanMessage
from src.core.logger import logger
from src.services.gemini import get_smart_chain
from src.utils.text_tools import extract_text, LANG_ALIASES

# Language Names Mapping
LANG_NAMES = {
    "fa": "فارسی", "en": "انگلیسی", "fr": "فرانسوی", "ko": "کره‌ای",
    "ar": "عربی", "de": "آلمانی", "es": "اسپانیایی", "it": "ایتالیایی",
    "ja": "ژاپنی", "zh": "چینی", "ru": "روسی", "tr": "ترکی",
    "pt": "پرتغالی", "hi": "هندی"
}

LANG_FLAGS = {
    "fa": "🇮🇷", "en": "🇺🇸", "fr": "🇫🇷", "ko": "🇰🇷"
}

async def detect_language(text: str) -> str:
    """Detect language of text. Prioritizes local regex for FA/KO, then AI."""
    if not text:
        return "fa"
        
    # Heuristic for Persian/Arabic
    if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
        return "fa"
    
    # Heuristic for Korean (Hangul)
    if re.search(r'[\uAC00-\uD7AF\u1100-\u11FF]', text):
        return "ko"
        
    # Use AI for EN vs FR or others
    try:
        # Use a very short, fast prompt
        chain = get_smart_chain(grounding=False)
        response = await chain.ainvoke(f"Return only the 2-letter ISO code for this text's language: {text[:100]}")
        content = extract_text(response)
        code = content.lower()[:2]
        return LANG_ALIASES.get(code, code) if code in LANG_ALIASES else code
    except:
        return "en"

async def translate_text(text: str, target_lang: str) -> str:
    """Translate text to target language using Gemini"""
    lang_name = LANG_NAMES.get(target_lang, "English")
    
    try:
        chain = get_smart_chain(grounding=False)
        prompt = f"Translate the following text to {lang_name}. Only output the translation, no explanations:\n\n{text}"
        response = await chain.ainvoke([HumanMessage(content=prompt)])
        return extract_text(response)
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text  # Return original if translation fails

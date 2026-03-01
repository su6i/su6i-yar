import io
import asyncio
import httpx
import edge_tts
from src.core.logger import logger
from src.utils.text_tools import clean_text_strict
import re

DATACULA_API_URL = "https://tts.datacula.com/api/tts"

# Best EdgeTTS voice per language
# Two options per language: [0] = primary  [1] = secondary (different gender)
TTS_VOICES = {
    "fa": ("fa-IR-FaridNeural",   "fa-IR-DilaraNeural"),   # Persian  M / F
    "en": ("en-US-GuyNeural",     "en-US-JennyNeural"),    # English  M / F
    "fr": ("fr-FR-HenriNeural",   "fr-FR-DeniseNeural"),   # French   M / F
    "ko": ("ko-KR-InJoonNeural",  "ko-KR-SunHiNeural"),    # Korean   M / F
    "ar": ("ar-SA-HamedNeural",   "ar-EG-SalmaNeural"),    # Arabic   M / F
    "de": ("de-DE-ConradNeural",  "de-DE-KatjaNeural"),    # German   M / F
    "es": ("es-ES-AlvaroNeural",  "es-ES-ElviraNeural"),   # Spanish  M / F
    "it": ("it-IT-DiegoNeural",   "it-IT-ElsaNeural"),     # Italian  M / F
    "ja": ("ja-JP-KeitaNeural",   "ja-JP-NanamiNeural"),   # Japanese M / F
    "zh": ("zh-CN-YunxiNeural",   "zh-CN-XiaoxiaoNeural"), # Chinese  M / F
    "ru": ("ru-RU-DmitryNeural",  "ru-RU-SvetlanaNeural"), # Russian  M / F
    "tr": ("tr-TR-AhmetNeural",   "tr-TR-EmelNeural"),     # Turkish  M / F
    "pt": ("pt-BR-AntonioNeural", "pt-BR-FranciscaNeural"),# Portuguese M/F
    "hi": ("hi-IN-MadhurNeural",  "hi-IN-SwaraNeural"),    # Hindi    M / F
}

_FALLBACK_VOICE = "en-US-GuyNeural"


async def text_to_speech(text: str, lang: str = "fa", gender: str = "male") -> io.BytesIO | None:
    """
    Convert text to speech.
    Primary: Datacula (Amir) for Persian.
    Fallback: EdgeTTS (Farid/Dilara) for Persian, or appropriate voice for others.
    """
    lang_key = lang[:2].lower()
    
    # Determine Logic (Is it Persian?)
    is_persian_request = (lang_key == "fa") or (lang_key not in TTS_VOICES and re.search(r'[\u0600-\u06FF]', text))
    
    clean_text = clean_text_strict(text) or text
    if len(clean_text) > 2000:
        clean_text = clean_text[:2000] + "..."

    audio_buffer = io.BytesIO()
    
    # --- STRATEGY 1: DATACULA (Persian Only) ---
    if is_persian_request:
        try:
            logger.info("🎙️ Using Datacula (Amir) for Persian TTS...")
            params = {
                "text": clean_text,
                "model_name": "امیر" # Confirmed Persian ID
            }
            # Timeout is important as it's a queued free API (20s)
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(DATACULA_API_URL, params=params)
            
            if response.status_code == 200 and len(response.content) > 1000:
                audio_buffer.write(response.content)
                audio_buffer.seek(0)
                return audio_buffer
            else:
                logger.warning(f"⚠️ Datacula Failed: {response.status_code}")
                # Fall through to EdgeTTS
        except Exception as e:
            logger.error(f"⚠️ Datacula Error: {e}")
            # Fall through to EdgeTTS
            
    # --- STRATEGY 2: EDGE TTS (Fallback/Default) ---
    voices = TTS_VOICES.get(lang_key, TTS_VOICES["en"])
    primary_voice = voices[1] if gender == "female" else voices[0]
    alternate_voice = voices[0] if gender == "female" else voices[1]
    
    # Attempt 1: Primary Voice
    edge_buffer = await _attempt_edge_tts(clean_text, primary_voice)
    if edge_buffer: return edge_buffer
        
    logger.warning(f"⚠️ Primary EdgeTTS voice ({primary_voice}) failed. Falling back to {alternate_voice}...")
    
    # Attempt 2: Alternate Voice
    edge_buffer = await _attempt_edge_tts(clean_text, alternate_voice)
    if edge_buffer: return edge_buffer
        
    logger.error(f"❌ Alternate EdgeTTS voice ({alternate_voice}) also failed.")
    
    # Attempt 3: Universal Fallback (Only if the requested language wasn't already English)
    if lang_key != "en":
        logger.info(f"🎙️ Universal Fallback to English Voice: {_FALLBACK_VOICE}")
        audio_buffer = await _attempt_edge_tts(clean_text, _FALLBACK_VOICE)
        if audio_buffer:
            return audio_buffer
            
    return None

async def _attempt_edge_tts(text: str, voice: str) -> io.BytesIO | None:
    """Helper to stream from edge-tts and catch exceptions"""
    audio_buffer = io.BytesIO()
    try:
        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
                
        # Check size before seeking to 0!
        if audio_buffer.tell() == 0:
            raise ValueError("Empty audio stream returned")
            
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        logger.error(f"EdgeTTS error with {voice}: {e}")
        return None


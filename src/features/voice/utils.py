import io
import asyncio
import edge_tts
from src.core.logger import logger
from src.utils.text_tools import clean_text_strict

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
    Convert text to speech using EdgeTTS.

    Args:
        text:   The text to speak.
        lang:   BCP-47 language code prefix (e.g. 'fa', 'en', 'ko').
        gender: 'male' (index 0) or 'female' (index 1).  Default: male.

    Returns:
        BytesIO with MP3 audio, or None on failure.
    """
    lang_key = lang[:2].lower()
    clean_text = clean_text_strict(text) or text
    if len(clean_text) > 2000:
        clean_text = clean_text[:2000] + "..."

    voices = TTS_VOICES.get(lang_key, TTS_VOICES["en"])
    voice = voices[1] if gender == "female" else voices[0]

    audio_buffer = io.BytesIO()
    try:
        communicate = edge_tts.Communicate(clean_text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        audio_buffer.seek(0)
        if audio_buffer.tell() == 0:
            raise ValueError("Empty audio stream returned")
        return audio_buffer
    except Exception as e:
        logger.error(f"EdgeTTS failed (voice={voice}): {e}")
        
        # Smart Fallback: If it's Persian, edge-tts is known to fail frequently. Use gTTS instead.
        if lang_key == "fa":
            try:
                from gtts import gTTS
                logger.info("🎙️ Falling back to Google TTS (gTTS) for Persian...")
                tts = gTTS(text=clean_text, lang="ar") # gTTS doesn't formally support 'fa', but 'ar' reads Persian script perfectly without accent in gTTS
                
                # We save to a temporary file because gTTS write_to_fp has historically had bugs with BytesIO
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                    temp_path = temp_audio.name
                    
                tts.save(temp_path)
                
                fallback_buffer = io.BytesIO()
                with open(temp_path, "rb") as f:
                    fallback_buffer.write(f.read())
                    
                fallback_buffer.seek(0)
                os.remove(temp_path)
                return fallback_buffer
                
            except Exception as gtts_e:
                logger.error(f"❌ gTTS fallback also failed: {gtts_e}")
                return None
                
        # Last-resort fallback: English male for other languages
        elif voice != _FALLBACK_VOICE:
            try:
                logger.info(f"🎙️ Falling back to English Voice: {_FALLBACK_VOICE}")
                audio_buffer = io.BytesIO()
                communicate = edge_tts.Communicate(clean_text, _FALLBACK_VOICE)
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_buffer.write(chunk["data"])
                audio_buffer.seek(0)
                return audio_buffer
            except Exception as e2:
                logger.error(f"❌ EdgeTTS English fallback also failed: {e2}")
        return None


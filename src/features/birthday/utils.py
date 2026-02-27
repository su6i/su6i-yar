from datetime import date
import jdatetime
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import GEMINI_API_KEY
from src.core.logger import logger

async def generate_birthday_wish(target_name: str, month_name: str):
    """
    Generate a personalized birthday wish using Gemini (with robust model detection).
    Returns: (wish_text: str, english_name: str)
    """
    # ONLY use Gemini 2.0+ models as strictly requested
    # Discovered via diagnostics: 2.5 and 2.0 are available!
    models_to_try = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash-lite", # Try lite first if flash is exhausted
        "models/gemini-2.0-flash",
        "models/gemini-flash-latest"
    ]
    
    prompt = (
        f"I need a birthday wish for user '{target_name}' (born in month {month_name}).\n"
        f"Include a short, fun fact about people born in this month.\n"
        f"Respond with valid JSON only: {{ \"wish\": \"Persian wish with emojis + fun fact\", \"english_name\": \"Transliterated name\" }}"
    )

    for model_name in models_to_try:
        try:
            logger.info(f"🧠 Attempting birthday wish with model: {model_name}")
            model = ChatGoogleGenerativeAI(model=model_name, google_api_key=GEMINI_API_KEY)
            # CRITICAL: Use ainvoke for async compatibility in LangChain
            response = await model.ainvoke(prompt)
            text_resp = response.content.replace('```json', '').replace('```', '').strip()
            data = json.loads(text_resp)
            return data.get("wish", "تولدت مبارک!"), data.get("english_name", target_name)
        except Exception as e:
            logger.warning(f"⚠️ Model {model_name} failed: {e}")
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                logger.warning(f"🛑 Quota reached for {model_name}, trying next...")
            continue

    # If all models fail
    logger.error(f"❌ All Gemini models failed to generate a birthday wish.")
    return "امیدواریم سالی پر از موفقیت و شادی داشته باشی! 🥳", target_name


def parse_smart_date(date_str: str):
    """
    Parses date string (DD-MM-YYYY or DD-MM).
    Smartly detects Jalali if year < 1700.
    Returns: (g_y, g_m, g_d, j_y, j_m, j_d, is_jalali)
    """
    try:
        # Normalize separators
        date_str = date_str.replace("/", "-").replace(".", "-")
        parts = [int(p) for p in date_str.split("-") if p.isdigit()]
        
        if len(parts) == 2:
            # Format: DD-MM -> Default Year 1360 (Jalali)
            d, m = parts[0], parts[1]
            y = 1360
            
        elif len(parts) == 3:
            if parts[0] > 1000:
                # Format: YYYY-MM-DD
                y, m, d = parts[0], parts[1], parts[2]
            else:
                # Format: DD-MM-YYYY
                d, m, y = parts[0], parts[1], parts[2]
        else:
            return None

        # Logic: year < 1700 => Jalali
        is_jalali = (y < 1700)
        
        if is_jalali:
            j_date = jdatetime.date(y, m, d)
            g_date = j_date.togregorian()
            return (g_date.year, g_date.month, g_date.day, 
                    j_date.year, j_date.month, j_date.day, True)
        else:
            g_date = date(y, m, d)
            j_date = jdatetime.date.fromgregorian(date=g_date)
            return (g_date.year, g_date.month, g_date.day,
                    j_date.year, j_date.month, j_date.day, False)

    except Exception as e:
        logger.error(f"Date Parse Error: {e}")
        return None

def get_month_theme(month: int, is_jalali: bool = False) -> str:
    """Returns a visual theme string for the month."""
    if is_jalali:
        themes = {
            1: "Spring nature, cherry blossoms, Aries zodiac",      # Farvardin
            2: "Green meadows, Taurus zodiac, spring breeze",      # Ordibehesht
            3: "Gemini zodiac, late spring flowers, sunny",        # Khordad
            4: "Summer heat, Cancer zodiac, beach vibes",          # Tir
            5: "Hot summer, Leo zodiac, golden sun, sunflowers",   # Mordad
            6: "End of summer, Virgo zodiac, harvest time",        # Shahrivar
            7: "Autumn, orange leaves, Libra zodiac, cozy",        # Mehr
            8: "Rainy autumn, Scorpio zodiac, pomegranates",       # Aban
            9: "Late autumn, Sagittarius zodiac, fire and cold",   # Azar
            10: "Winter snow, Capricorn zodiac, festive",          # Dey
            11: "Deep winter, Aquarius zodiac, ice crystals",      # Bahman
            12: "Late winter, Pisces zodiac, melting snow"         # Esfand
        }
    else:
        themes = {
            1: "Winter, Capricorn/Aquarius, snow", 2: "Winter, Aquarius/Pisces, ice",
            3: "Spring, Pisces/Aries, green grass", 4: "Spring, Aries/Taurus, rain",
            5: "Spring, Taurus/Gemini, flowers", 6: "Summer, Gemini/Cancer, sun",
            7: "Summer, Cancer/Leo, beach", 8: "Summer, Leo/Virgo, heat",
            9: "Autumn, Virgo/Libra, leaves", 10: "Autumn, Libra/Scorpio, pumpkins",
            11: "Autumn, Scorpio/Sagittarius, rain", 12: "Winter, Sagittarius/Capricorn, snow"
        }
    return themes.get(month, "Festive colorful party")

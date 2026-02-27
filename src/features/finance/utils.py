import time
import re
import httpx
from bs4 import BeautifulSoup
from src.core.logger import logger

# Cache
MARKET_DATA_CACHE = None
MARKET_DATA_TIMESTAMP = 0
MARKET_CACHE_TTL = 300 # 5 minutes

async def fetch_market_data():
    """Scrape USD, EUR, Gold 18k, and Ons from tgju.org with caching"""
    global MARKET_DATA_CACHE, MARKET_DATA_TIMESTAMP
    
    now = time.time()
    if MARKET_DATA_CACHE and (now - MARKET_DATA_TIMESTAMP) < MARKET_CACHE_TTL:
        logger.info("📡 Using cached market data")
        return MARKET_DATA_CACHE

    logger.info("🌐 Fetching live market data from tgju.org")
    url = "https://www.tgju.org/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Scrape data using verified selectors with fallbacks
        def get_val(selectors):
            if isinstance(selectors, str):
                selectors = [selectors]
            
            for selector in selectors:
                el = soup.select_one(selector)
                if el:
                    # Remove commas and non-numeric chars for calculation, but keep raw for display
                    raw = el.get_text(strip=True)
                    # For Euro particularly, sometimes the text has extra labels, clean it
                    if "یورو" in raw: raw = raw.replace("یورو", "").strip()
                    val = re.sub(r'[^\d.]', '', raw)
                    if val:
                        return raw, float(val)
            return "N/A", 0.0

        usd_raw, usd_val = get_val(["li#l-price_dollar_rl span span", "tr[data-market-nameslug='price_dollar_rl'] td.market-price"])
        eur_raw, eur_val = get_val([
            "li#l-price_eur span span", 
            "tr[data-market-nameslug='price_eur'] td.market-price",
            "tr[data-market-row='price_eur'] td.market-price"
        ])
        gold18_raw, gold18_val = get_val(["li#l-geram18 span span", "tr[data-market-nameslug='geram18'] td.market-price"])
        ons_raw, ons_val = get_val(["li#l-ons span span", "tr[data-market-nameslug='ons'] td.market-price"])

        if usd_val == 0 or ons_val == 0:
            logger.warning("⚠️ Scraper returned zero for critical values. Check selectors.")
            return None

        # Calculate Theoretical Gold (18k)
        # Formula: (Ons * Dollar) / 31.1034768 * 0.750
        theoretical_val = (ons_val * usd_val) / 31.1034768 * 0.750
        diff_val = gold18_val - theoretical_val
        
        # Format helpers
        def fmt_curr(val): return f"{int(val):,}"
        def fmt_tm(val): return f"{int(val/10):,}"
        
        data = {
            "usd": usd_raw,
            "eur": eur_raw,
            "gold18": gold18_raw,
            "ons": ons_raw,
            "theoretical": fmt_curr(theoretical_val),
            "diff": ("+" if diff_val > 0 else "") + fmt_curr(diff_val),
            # Toman versions for Farsi
            "usd_tm": fmt_tm(usd_val),
            "eur_tm": fmt_tm(eur_val),
            "gold18_tm": fmt_tm(gold18_val),
            "theoretical_tm": fmt_tm(theoretical_val),
            "diff_tm": ("+" if diff_val > 0 else "") + fmt_tm(diff_val)
        }
        
        MARKET_DATA_CACHE = data
        MARKET_DATA_TIMESTAMP = now
        return data

    except Exception as e:
        logger.error(f"❌ Scraper Exception: {e}")
        return None

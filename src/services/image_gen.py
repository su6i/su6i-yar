import urllib.parse
import httpx
import asyncio
from src.core.logger import logger

async def generate_birthday_image(name_text: str, theme: str) -> bytes:
    """
    Generate a birthday cake image using AI (Pollinations) or Pexels fallback.
    Returns image bytes or None if failed.
    """
    from src.core.config import PEXELS_API_KEY
    import random

    # 1. AI GENERATION (Retries)
    text_on_cake = name_text.upper() if name_text.isascii() else "HAPPY BIRTHDAY"
    
    # Add random word/entropy for variety
    variations = ["dreamy", "colorful", "hyper-realistic", "artistic", "festive", "vibrant", "elegant"]
    random_variation = random.choice(variations)
    
    image_prompt_text = (
        f"Happy Birthday {name_text}, {theme} theme, {random_variation}, "
        f"delicious cake with text '{text_on_cake}' written on it, "
        f"cinematic lighting, 8k"
    )
    
    for attempt in range(2): # Try twice
        try:
            # New seed for each attempt
            seed = random.randint(1, 1000000)
            encoded_prompt = urllib.parse.quote(image_prompt_text)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1024&height=1024&nologo=true&seed={seed}"
            
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.get(image_url)
                if resp.status_code == 200:
                    return resp.content
                logger.warning(f"⚠️ AI Image Gen Attempt {attempt+1} failed ({resp.status_code}).")
        except Exception as e:
            logger.warning(f"⚠️ AI Image Gen Exception {attempt+1}: {e}")
        await asyncio.sleep(2)

    # 2. PEXELS FALLBACK
    if PEXELS_API_KEY:
        logger.info(f"📸 Falling back to Pexels search for: {theme} birthday cake")
        try:
            query = f"{theme} birthday cake"
            # Get multiple results to allow randomness
            url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=15"
            headers = {"Authorization": PEXELS_API_KEY}
            
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    photos = data.get("photos", [])
                    if photos:
                        # Pick a random photo from the results
                        photo = random.choice(photos)
                        photo_url = photo["src"]["large"]
                        
                        logger.info(f"✅ Random Pexels image selected (out of {len(photos)})")
                        p_resp = await client.get(photo_url)
                        if p_resp.status_code == 200:
                            return p_resp.content
        except Exception as p_err:
            logger.error(f"❌ Pexels Fallback Error: {p_err}")

    return None

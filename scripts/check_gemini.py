import os
import httpx
import json
from dotenv import load_dotenv

# Load ENV
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

async def check_models():
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    print(f"🔍 Fetching available models for key: {api_key[:10]}...")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                print(f"❌ API Error ({resp.status_code}): {resp.text}")
                return
            
            data = resp.json()
            models = data.get("models", [])
            
            print(f"\n✅ Found {len(models)} models:")
            print("-" * 50)
            
            # Filter for generation models
            gen_models = [m for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
            
            for m in gen_models:
                name = m.get("name", "unknown")
                version = m.get("version", "unknown")
                display_name = m.get("displayName", "unknown")
                print(f"🚀 {name} | {display_name}")
            
            print("-" * 50)
            print("\n💡 Tip: Use the full 'models/...' string in your code.")
            
        except Exception as e:
            print(f"💥 Exception: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_models())

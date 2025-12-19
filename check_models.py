import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ API Key not found in .env")
else:
    genai.configure(api_key=api_key)
    print("✅ API Key found. Fetching models...")
    try:
        models = genai.list_models()
        available = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name)
        
        print("\n📝 Available Models for this Key:")
        for name in available:
            print(f"- {name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")

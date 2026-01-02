import os
import json

def create_env():
    print("\n🤖 Su6i Yar Environment Setup")
    print("==============================\n")

    token = input("1. Enter TELEGRAM_BOT_TOKEN: ").strip()
    gemini = input("2. Enter GEMINI_API_KEY: ").strip()
    admin_id = input("3. Enter Admin Numeric ID (e.g., 12345678): ").strip()
    
    settings = {"admin_id": int(admin_id) if admin_id.isdigit() else 0, "public_mode": False}

    with open(".env", "w") as f:
        f.write(f'TELEGRAM_BOT_TOKEN={token}\n')
        f.write(f'GEMINI_API_KEY={gemini}\n')
        f.write(f'SETTINGS={json.dumps(settings)}\n')
        
    print("\n✅ .env file created successfully!")

if __name__ == "__main__":
    create_env()

import asyncio
import os
from pyrogram import Client
from dotenv import load_dotenv
from pathlib import Path

# Load existing .env
load_dotenv()

async def main():
    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")
    
    if not api_id or not api_hash:
        print("❌ Please ensure TG_API_ID and TG_API_HASH are in your .env file.")
        return

    print("--- Manual Pyrogram Login ---")
    phone = input("Enter your phone number (full international format, e.g., +33775867726): ").strip()
    
    client = Client(
        name="manual_session",
        api_id=int(api_id),
        api_hash=api_hash,
        in_memory=True
    )
    
    await client.connect()
    print(f"📡 Requesting code for {phone}...")
    
    try:
        code_hash = await client.send_code(phone)
        print("✅ Code requested! NOW CHECK YOUR TELEGRAM APP.")
        print("(If it doesn't show up, wait 2 minutes or try logging into web.telegram.org first)")
        
        otp = input("Enter the code from Telegram: ").strip()
        
        try:
            await client.sign_in(phone, code_hash.phone_code_hash, otp)
        except Exception as e:
            if "SESSION_PASSWORD_NEEDED" in str(e):
                password = input("Enter your 2-Step Verification password: ").strip()
                await client.check_password(password)
            else:
                raise e
        
        session_string = await client.export_session_string()
        print("\n🏆 SUCCESS!")
        print(f"Your Session String: {session_string}")
        print("\nCopy the long string above and paste it into .env for TG_SESSION_STRING.")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

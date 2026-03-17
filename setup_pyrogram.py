"""
One-time setup: generate a Pyrogram session string and write it to .env

Run once:  uv run python3 setup_pyrogram.py

Prerequisites:
  1. Go to https://my.telegram.org → Log in → API development tools
  2. Create an app (any name, e.g. "su6i-yar")
  3. Copy the `api_id` (integer) and `api_hash` (hex string) shown there
"""

import os
import re
import sys
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"


def read_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    result: dict[str, str] = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def upsert_env(key: str, value: str) -> None:
    """Add or update a key=value pair in .env (preserves all other lines)."""
    text = ENV_FILE.read_text() if ENV_FILE.exists() else ""
    pattern = re.compile(rf"^{re.escape(key)}\s*=.*$", re.MULTILINE)
    new_line = f"{key}={value}"
    if pattern.search(text):
        text = pattern.sub(new_line, text)
    else:
        text = text.rstrip("\n") + f"\n{new_line}\n"
    ENV_FILE.write_text(text)
    print(f"  ✅ Written {key} to .env")


def main() -> None:
    env = read_env()

    api_id_str   = env.get("TG_API_ID",   "").strip()
    api_hash     = env.get("TG_API_HASH",  "").strip()
    session_str  = env.get("TG_SESSION_STRING", "").strip()

    if session_str:
        print("✅ TG_SESSION_STRING is already set in .env — nothing to do.")
        print("   Delete or empty TG_SESSION_STRING in .env to regenerate.")
        return

    print("🔑 Pyrogram Personal-Account Setup")
    print("=" * 50)
    print("You need api_id and api_hash from https://my.telegram.org\n")

    if not api_id_str or api_id_str == "0":
        api_id_str = input("  Enter your api_id (integer from my.telegram.org): ").strip()
    else:
        print(f"  Using TG_API_ID={api_id_str} from .env")

    if not api_hash:
        api_hash = input("  Enter your api_hash (hex string from my.telegram.org): ").strip()
    else:
        print(f"  Using TG_API_HASH=***{api_hash[-6:]} from .env")

    try:
        api_id = int(api_id_str)
    except ValueError:
        print(f"❌ api_id must be an integer, got: {api_id_str!r}")
        sys.exit(1)

    print("\n📲 Pyrogram will now ask for your phone number + OTP code…")
    print("  (Check your Telegram app for the code)\n")

    try:
        from pyrogram import Client
    except ImportError:
        print("❌ pyrogram not installed. Run:  uv add pyrogram")
        sys.exit(1)

    # Use a real (but temporary) session file name to ensure maximum stability
    session_name = "su6i_yar_temp_session"
    
    try:
        # Standard synchronous Client start with explicit device info to improve reliability
        client = Client(
            name=session_name,
            api_id=api_id,
            api_hash=api_hash,
            device_model="MacBook Pro",
            system_version="macOS 14.4",
            app_version="su6i-yar v1.0"
        )
        
        with client:
            generated_session = client.export_session_string()
            
        print(f"\n✅ Session string generated successfully (length={len(generated_session)})")

        # Persist to .env
        upsert_env("TG_API_ID",         str(api_id))
        upsert_env("TG_API_HASH",       api_hash)
        upsert_env("TG_SESSION_STRING", generated_session)
        
        print("\n🎉 Done! Restart the bot and large Telegram videos will be handled via your personal account.")

    except Exception as e:
        print(f"\n❌ Error during session generation: {e}")
        print("   If you didn't receive a code, wait 5 minutes and check all active Telegram sessions.")
    finally:
        # Cleanup session files
        for f in Path(".").glob(f"{session_name}.session*"):
            try:
                f.unlink()
            except:
                pass


if __name__ == "__main__":
    main()

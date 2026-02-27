from telegram import Update
from telegram.ext import ContextTypes
from langchain_google_genai import ChatGoogleGenerativeAI
from pathlib import Path
import json
import urllib.parse
import httpx

from src.core.config import SETTINGS, GEMINI_API_KEY
from src.core.database import BIRTHDAYS, save_birthdays
from src.core.logger import logger
from src.utils.telegram import safe_delete
from src.services.image_gen import generate_birthday_image
from src.features.birthday.utils import parse_smart_date, get_month_theme

async def cmd_birthday_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Manage Birthdays:
    /birthday add @user DD-MM-YYYY
    /birthday check
    /birthday scan (Admin Only)
    /birthday wish Name [Date]
    """
    user = update.effective_user
    chat = update.effective_chat
    is_private = chat.type == "private"
    
    async def smart_reply(text: str):
        """Replies in PV, logs only in Group."""
        if is_private:
            await context.bot.send_message(chat_id=chat.id, text=text, parse_mode='Markdown')
        else:
            logger.info(f"🤐 Silent Response: {text}")

    # 1. Delete command message ONLY if in Group (Keep in PV)
    if not is_private:
        await safe_delete(update.message)

    # 2. ALWAYS Log the attempt
    logger.info(f"🎂 Birthday CMD Triggered by User: {user.id} ({user.first_name}) | Private: {is_private}")

    # 3. Security Check: Only Admin executes logic
    if user.id != SETTINGS["admin_id"]:
        logger.warning(f"⛔ Ignore: User {user.id} is not Admin.")
        return

    args = context.args
    if not args:
        await smart_reply("🎂 استفاده: /birthday [add | check | scan | wish]")
        return

    subcmd = args[0].lower()
    
    # --- ADD ---
    if subcmd == "add":
        is_reply = bool(update.message.reply_to_message)
        min_args = 2
        
        if len(args) < min_args:
             await smart_reply("⚠️ قالب: /birthday add [@username] DD-MM-YYYY")
             return
            
        if is_reply and len(args) == 2:
            target_username = "Unknown"
            date_str = args[1]
        else:
            target_username = args[1]
            date_str = args[2]
        
        parsed = parse_smart_date(date_str)
        if not parsed:
             await smart_reply("🚫 فرمت تاریخ اشتباه است. (DD-MM-YYYY or YYYY-MM-DD)")
             return

        g_y, g_m, g_d, j_y, j_m, j_d, is_jalali = parsed
        target_id = None
            
        # Try to resolve user from reply
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_id = target_user.id
            target_username = f"@{target_user.username}" if target_user.username else target_user.first_name
        
        if not target_id:
            if target_username.isdigit():
                target_id = int(target_username)
                target_username = f"User {target_id}"
            else:
                # SMART LOOKUP
                clean_target = target_username.strip().replace("@", "").lower()
                found_real_id = None
                for uid, data in BIRTHDAYS.items():
                    if uid > 0:
                        db_uname = data.get("username", "").strip().replace("@", "").lower()
                        if db_uname == clean_target:
                            found_real_id = uid
                            break
                
                if found_real_id:
                    target_id = found_real_id
                else:
                    # Manual Add (Synthetic ID)
                    target_id = -abs(hash(target_username))
                    await smart_reply(f"⚠️ کاربر یافت نشد. استفاده از آیدی مجازی: {target_id}")

        # DEDUPLICATION
        if target_id > 0:
            clean_target_name = target_username.strip().replace("@", "").lower()
            keys_to_remove = [k for k, v in BIRTHDAYS.items() 
                              if k < 0 and v.get("username", "").strip().replace("@", "").lower() == clean_target_name]
            for k in keys_to_remove:
                del BIRTHDAYS[k]

        target_data = {
            "day": g_d, "month": g_m, "year": g_y,
            "username": target_username, "chat_id": chat_id, "is_jalali": is_jalali
        }
        
        if is_jalali:
            target_data["jalali_date"] = [j_y, j_m, j_d]
        else:
            import jdatetime
            j_date = jdatetime.date.fromgregorian(day=g_d, month=g_m, year=g_y)
            target_data["jalali_date"] = [j_date.year, j_date.month, j_date.day]

        BIRTHDAYS[target_id] = target_data
        save_birthdays()
        
        display_date = f"{j_y}/{j_m}/{j_d} (شمسی)" if is_jalali else f"{g_y}/{g_m}/{g_d} (میلادی)"
        await smart_reply(f"✅ تولد {target_username} ثبت شد: {display_date}")
            
    # --- CHECK ---
    elif subcmd == "check":
        if not BIRTHDAYS:
            await smart_reply("📭 لیست تولدها خالی است.")
            return

        msg_text = "🎂 **لیست تولدها:**\n\n"
        for uid, data in BIRTHDAYS.items():
            msg_text += f"👤 {data['username']}: {data['day']}/{data['month']}/{data['year']}\n"
        await smart_reply(f"📊 تولدهای ثبت شده:\n{msg_text}")

    # --- WISH (Manual) ---
    elif subcmd == "wish":
        if len(args) < 2:
            await smart_reply("⚠️ قالب: /birthday wish Name [DD-MM]")
            return
            
        target_name = args[1]
        from datetime import datetime
        now = datetime.now()
        
        parsed = parse_smart_date(args[2]) if len(args) >= 3 else None
        
        if parsed:
             g_y, g_m, g_d, j_y, j_m, j_d, is_jalali = parsed
             v_month = j_m if is_jalali else g_m
        else:
             is_jalali = False
             v_month = now.month
        
        await smart_reply(f"🎉 در حال آماده‌سازی جشن برای {target_name}...")
        
        try:
            month_names = {
                1: "Jan/Dey", 2: "Feb/Bahman", 3: "Mar/Esfand", 4: "Apr/Farvardin", 
                5: "May/Ordibehesht", 6: "Jun/Khordad", 7: "Jul/Tir", 8: "Aug/Mordad", 
                9: "Sep/Shahrivar", 10: "Oct/Mehr", 11: "Nov/Aban", 12: "Dec/Azar"
            }
            month_name = month_names.get(v_month, "Unknown")
            visual_theme = get_month_theme(v_month, is_jalali)
            
            caption = f"🎂 **تولدت مبارک {target_name}!** 🎉\n\n"
            english_name_for_img = target_name 
            
            # B) Generate Content (Gemini) - Shared Utility
            from src.features.birthday.utils import generate_birthday_wish
            wish_text, english_name_for_img = await generate_birthday_wish(target_name, month_name)
            
            caption = f"🎂 **تولدت مبارک {target_name}!** 🎉\n\n{wish_text}"


            # Generate Image
            image_bytes = await generate_birthday_image(english_name_for_img, visual_theme)
            if not image_bytes:
                 await smart_reply("⚠️ تصویر ساخته نشد (کندی سرور)، اما جشن ادامه دارد! 🕯")

            # Send Image or Text
            if image_bytes:
                await context.bot.send_photo(chat_id=chat.id, photo=image_bytes, caption=caption, parse_mode="Markdown")
            else:
                await context.bot.send_message(chat_id=chat.id, text=caption, parse_mode="Markdown")
            
            # 1. Send Static Audio (Consistent)
            try:
                static_audio = Path("assets/birthday_song.mp3")
                if static_audio.exists():
                     await context.bot.send_audio(
                        chat_id=chat.id,
                        audio=open(static_audio, "rb"),
                        title=f"Happy Birthday {english_name_for_img}",
                        performer="Su6i Yar"
                     )
            except Exception as static_err:
                logger.error(f"Static Audio Error: {static_err}")

            
        except Exception as e:
            await smart_reply(f"❌ خطا در جشن: {e}")
            logger.error(f"Manual Wish Error: {e}")

    # --- SCAN ---
    elif subcmd == "scan":
        # Scan logic placeholder (can be implemented if needed)
        pass

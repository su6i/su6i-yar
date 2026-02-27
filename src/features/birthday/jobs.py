from telegram.ext import ContextTypes
import jdatetime
from datetime import datetime
from pathlib import Path

from src.core.database import BIRTHDAYS
from src.core.logger import logger
from src.services.image_gen import generate_birthday_image
from src.features.birthday.utils import get_month_theme, generate_birthday_wish

async def check_birthdays_job(context: ContextTypes.DEFAULT_TYPE):
    """Daily job to check birthdays (Jalali & Gregorian)"""
    
    now = datetime.now()
    j_now = jdatetime.date.fromgregorian(date=now.date())
    
    logger.info(f"📅 Checking Birthdays for {now.date()} / {j_now}")

    # Iterate and Check
    for uid, data in BIRTHDAYS.items():
        is_match = False
        
        # Check Jalali
        if data.get("is_jalali"):
            jd = data.get("jalali_date", [0, 0, 0]) # [y, m, d]
            if jd[1] == j_now.month and jd[2] == j_now.day:
                is_match = True
        else:
            # Check Gregorian
            if data["month"] == now.month and data["day"] == now.day:
                is_match = True
        
        if is_match:
            try:
                chat_id = data.get("chat_id")
                target_name = data["username"]
                
                # Determine visual month
                if data.get("is_jalali"):
                    v_month = data.get("jalali_date", [0,0,0])[1]
                    is_jalali_flag = True
                else:
                    v_month = data["month"]
                    is_jalali_flag = False
                    
                visual_theme = get_month_theme(v_month, is_jalali=is_jalali_flag)
                
                month_names = {
                    1: "Jan/Dey", 2: "Feb/Bahman", 3: "Mar/Esfand", 4: "Apr/Farvardin", 
                    5: "May/Ordibehesht", 6: "Jun/Khordad", 7: "Jul/Tir", 8: "Aug/Mordad", 
                    9: "Sep/Shahrivar", 10: "Oct/Mehr", 11: "Nov/Aban", 12: "Dec/Azar"
                }
                month_name = month_names.get(v_month, "Unknown")
                
                # Prepare Caption with Mention
                mention_link = target_name
                if uid > 0:
                    mention_link = f"[{target_name}](tg://user?id={uid})"
                
                wish_text, english_name_for_img = await generate_birthday_wish(target_name, month_name)
                caption = f"🎂 **تولدت مبارک {mention_link}!** 🎉\n\n{wish_text}"

                # Image Generation
                image_bytes = await generate_birthday_image(english_name_for_img, visual_theme)

                # 1. SEND PRIVATE WISH (If Real User)
                if uid > 0:
                    try:
                         if image_bytes:
                            await context.bot.send_photo(chat_id=uid, photo=image_bytes, caption=caption, parse_mode="Markdown")
                         else:
                            await context.bot.send_message(chat_id=uid, text=caption, parse_mode="Markdown")
                         logger.info(f"✅ Private wish sent to {uid}")
                    except Exception as pv_err:
                        logger.warning(f"⚠️ Could not send private wish to {uid}: {pv_err}")

                # 2. SEND GROUP WISH (If Member)
                if chat_id:
                    should_send_group = True
                    if uid > 0:
                        try:
                            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=uid)
                            if member.status in ['left', 'kicked', 'restricted']:
                                should_send_group = False
                        except Exception:
                            should_send_group = False
                    
                    if should_send_group:
                        if image_bytes:
                             await context.bot.send_photo(chat_id=chat_id, photo=image_bytes, caption=caption, parse_mode="Markdown")
                        else:
                             await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown")
                        
                        # Audio (Robust)
                        # 1. Send Static Audio (Consistent)
                        try:
                            static_audio = Path("assets/birthday_song.mp3")
                            if static_audio.exists():
                                 await context.bot.send_audio(
                                    chat_id=chat_id,
                                    audio=open(static_audio, "rb"),
                                    title=f"Happy Birthday {english_name_for_img}",
                                    performer="Su6i Yar"
                                 )
                        except Exception as static_err:
                            logger.error(f"Job Static Audio Error: {static_err}")

                
            except Exception as e:
                logger.error(f"Birthday Job Error for {uid}: {e}")

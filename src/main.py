import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    JobQueue
)
from datetime import time

# Setup Logging first
# Note: Logger module acts on import-side if configured that way, 
# but usually we want to explicit setup if main.
# src.core.logger sets up basic logging on import.
from src.core.logger import logger 

from src.core.config import TELEGRAM_TOKEN, SETTINGS
from src.core.database import load_persistence, load_birthdays

# Handlers
from src.features.downloader import cmd_download_handler
from src.features.fact_check import cmd_check_handler
from src.features.birthday import cmd_birthday_handler, check_birthdays_job
from src.features.learning import cmd_learn_handler
from src.features.finance import cmd_price_handler
from src.features.voice import cmd_voice_handler
from src.features.amir import (
    amir_media_handler,
    amir_album_continuation_handler,
    cmd_qr_handler,
    cmd_pass_handler,
    cmd_weather_handler,
    cmd_amir_help_handler,
)
from src.features.utility import (
    cmd_start_handler, 
    cmd_help_handler, 
    cmd_status_handler, 
    cmd_close_handler,
    cmd_toggle_dl_handler,
    cmd_toggle_fc_handler,
    cmd_detail_handler,
    cmd_fun_handler,
    cmd_stop_bot_handler,
    channel_post_handler
)
from src.core.handlers import global_message_handler, error_handler

async def post_init(application):
    """Diagnostics on startup"""
    bot = application.bot
    logger.info("⏳ Diagnostics: Checking connection to Telegram API...")
    try:
        me = await bot.get_me()
        logger.info(f"✅ Connection OK! Bot: @{me.username} (ID: {me.id})")
        
        logger.info("🔄 Diagnostics: Clearing potential webhooks...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook Cleared. Ready to poll.")
        
        # Load Data
        load_persistence()
        load_birthdays()
        
    except Exception as e:
        logger.error(f"❌❌❌ CONNECTION ERROR ❌❌❌: {e}")


def main():
    if not TELEGRAM_TOKEN:
        logger.critical("❌ TELEGRAM_TOKEN not found in environment variables!")
        return

    logger.info("🚀 Starting Su6i Yar Core... (Modular Refactor v1.0)")

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .concurrent_updates(True)
        .job_queue(JobQueue()) 
        .post_init(post_init) 
        .build()
    )
    
    # Error Handler
    app.add_error_handler(error_handler)
    
    # Scheduled Jobs
    # Daily Birthday Check at 09:00
    app.job_queue.run_daily(check_birthdays_job, time(hour=9, minute=0))

    # --- Register Commands ---
    
    # Core/Utility
    app.add_handler(CommandHandler("start", cmd_start_handler))
    app.add_handler(CommandHandler("help", cmd_help_handler))
    app.add_handler(CommandHandler("status", cmd_status_handler))
    app.add_handler(CommandHandler("close", cmd_close_handler))
    app.add_handler(CommandHandler("detail", cmd_detail_handler))
    
    # Admin/Toggles
    # Toggle handlers were in su6i_yar.py but usually not exposed as /toggle_dl.
    # Ah, su6i_yar.py had toggle handlers but main registration list (lines 4443+) didn't show them explicitly? 
    # Let me check su6i_yar registration again.
    # It didn't list /toggle_dl explicitly in the view. Maybe they are hidden or accessed differently?
    # Wait, global_message_handler had buttons for them. 
    # But usually buttons send text instructions or callbacks.
    # The global handler checked text "📥" etc.
    # But let's add them as commands just in case admin wants to use them.
    # Or skip if they define logic only accessible via buttons in global handler?
    # Actually, global_handler calls logic directly. The handlers I created are for COMMANDS if mapped.
    # Let's map them for completeness if needed, or rely on global handler content check.
    # Since I exported them, I can use them.
    
    # Features
    app.add_handler(CommandHandler(["dl", "download"], cmd_download_handler))
    app.add_handler(CommandHandler("check", cmd_check_handler))
    app.add_handler(CommandHandler(["voice", "v"], cmd_voice_handler))
    app.add_handler(CommandHandler(["price", "p"], cmd_price_handler))
    app.add_handler(CommandHandler("birthday", cmd_birthday_handler))
    
    # Learning (Many aliases)
    app.add_handler(CommandHandler(["learn", "l", "t", "translate", "edu", "education"], cmd_learn_handler))
    
    # Fun (Admin)
    app.add_handler(CommandHandler("fun", cmd_fun_handler))
    app.add_handler(CommandHandler("stop", cmd_stop_bot_handler))
    
    # ── amir CLI tools ──────────────────────────────────────────────────────
    app.add_handler(CommandHandler(["amir", "tools"], cmd_amir_help_handler))
    app.add_handler(CommandHandler(["qr", "kqr"], cmd_qr_handler))
    app.add_handler(CommandHandler(["pass", "password", "passwd"], cmd_pass_handler))
    app.add_handler(CommandHandler(["weather", "wttr", "hava"], cmd_weather_handler))
    # Photos & image-documents → amir processing (caption intent detection)
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.Document.IMAGE) & filters.CaptionRegex(
            r"(?i)(pdf|پی.?دی.?اف|a4|کارت.?ملی|شناسنامه|resize|ریسایز|تغییر.?اندازه)"
        ),
        amir_media_handler,
    ))
    # Album continuation: uncaptioned photos that are part of a tracked media group
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.Document.IMAGE) & ~filters.CAPTION,
        amir_album_continuation_handler,
    ))
    # Album continuation: uncaptioned photos that are part of a tracked media group
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.Document.IMAGE) & ~filters.CAPTION,
        amir_album_continuation_handler,
    ))
    
    # --- Message Handlers ---
    
    # Channel Post (Fun Channel)
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post_handler))
    
    # Global Text Handler (Must be last)
    # Filter out commands to avoid double processing
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), global_message_handler))
    
    logger.info("✅ Bot Handlers Registered. Polling...")
    
    app.run_polling(
        allowed_updates=["message", "callback_query", "channel_post", "edited_channel_post"],
        drop_pending_updates=True,
        close_loop=False
    )

if __name__ == "__main__":
    main()

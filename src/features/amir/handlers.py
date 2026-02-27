"""
Telegram handlers that expose amir-cli tools to bot users.

Supported flows
───────────────
Photo / document + caption (single image):
  • "pdf" / "پی‌دی‌اف" / "a4" / "کارت ملی"  → amir pdf   → send PDF
  • "resize" / "ریسایز" / "a4 resize"         → amir img   → send resized image

Album (2+ photos) + caption "کارت ملی" / "id" / "شناسنامه" etc.:
  • stacks all images vertically → converts to A4 PDF
  • Use case: send front + back of ID card together as an album
  • How: در تلگرام چند عکس رو انتخاب کن، کپشن بنویس "کارت ملی"

Commands:
  • /qr  <text>          → amir qr    → send QR PNG
  • /pass [length]       → amir pass  → reply with password
  • /weather [city]      → amir weather → reply with weather
  • /amir                → show help card
"""
import asyncio
import os
from pathlib import Path
from telegram import Update, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.core.logger import logger
from src.utils.text_tools import get_msg

from .utils import (
    detect_photo_intent,
    run_pdf,
    run_qr,
    run_pass,
    run_weather,
    run_resize,
    run_stack,
    cleanup,
    _tmp,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

async def _download_media(msg: Message, suffix: str) -> str | None:
    """
    Download the largest available photo or document attached to a message.
    Returns local temp file path, or None on failure.
    """
    dest = _tmp(suffix)
    try:
        if msg.photo:
            file = await msg.photo[-1].get_file()
        elif msg.document:
            file = await msg.document.get_file()
        else:
            return None
        await file.download_to_drive(dest)
        return dest
    except Exception as e:
        logger.error(f"[amir] download_media failed: {e}")
        return None


def _ext_from_msg(msg: Message) -> str:
    """Guess file extension from message."""
    if msg.photo:
        return ".jpg"
    if msg.document and msg.document.file_name:
        return Path(msg.document.file_name).suffix or ".bin"
    return ".bin"


def _user_id(update: Update) -> int:
    return update.effective_user.id if update.effective_user else 0


# ── Media handler (photo / document + caption) ───────────────────────────────

# In-memory album accumulator: {media_group_id: {"msgs": [...], "chat_id": int, "caption": str}}
_album_buffer: dict = {}
_album_tasks: dict = {}


async def _process_album(media_group_id: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Called ~2s after the first photo of an album arrives.
    Downloads all collected photos, stacks them, sends A4 PDF.
    """
    await asyncio.sleep(2)  # wait for remaining album photos to arrive

    entry = _album_buffer.pop(media_group_id, None)
    _album_tasks.pop(media_group_id, None)
    if not entry:
        return

    msgs: list[Message] = entry["msgs"]
    chat_id: int = entry["chat_id"]
    caption: str = entry["caption"]

    intent = detect_photo_intent(caption)
    if intent not in ("pdf", None):
        return  # only stack for card/pdf intent
    # For albums, always treat as "id card stack → PDF" regardless of exact intent
    # (even if intent is None for non-captioned subsequent photos in the group)

    status_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"⏳ در حال ترکیب {len(msgs)} عکس روی یک صفحه A4..."
    )

    downloaded: list[str] = []
    try:
        for m in msgs:
            if m.photo:
                file = await m.photo[-1].get_file()
            elif m.document:
                file = await m.document.get_file()
            else:
                continue
            dest = _tmp(".jpg")
            await file.download_to_drive(dest)
            downloaded.append(dest)

        if len(downloaded) < 2:
            # Fallback to single-photo PDF
            if downloaded:
                code, text, output = run_pdf(downloaded[0])
                if code == 0 and output:
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=open(output, "rb"),
                        filename="document.pdf",
                        caption="📄 فایل PDF | توسط amir CLI",
                    )
                    cleanup(output)
            await status_msg.delete()
            return

        code, text, output = run_stack(downloaded, a4=True)
        if code == 0 and output:
            await context.bot.send_document(
                chat_id=chat_id,
                document=open(output, "rb"),
                filename="id_card_a4.pdf",
                caption=f"📄 {len(downloaded)} عکس روی یک صفحه A4 | توسط amir CLI",
            )
            await status_msg.delete()
            cleanup(output)
        else:
            await status_msg.edit_text(text)
    finally:
        cleanup(*downloaded)


async def amir_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Triggered whenever a user sends a photo or image-document.

    • Single photo: checks caption for intent, runs pdf/resize.
    • Album (media_group): collects all photos, stacks them → A4 PDF.
      User flow: select 2+ photos in Telegram → caption: "کارت ملی"
    """
    msg = update.effective_message
    if not msg:
        return

    caption = (msg.caption or "").strip()

    # ── Album handling ──────────────────────────────────────────────────────
    if msg.media_group_id:
        gid = msg.media_group_id
        if gid not in _album_buffer:
            _album_buffer[gid] = {
                "msgs": [],
                "chat_id": msg.chat_id,
                "caption": caption,  # caption is usually only on first message
            }
        _album_buffer[gid]["msgs"].append(msg)
        if caption:  # update caption if a later message has one
            _album_buffer[gid]["caption"] = caption

        # Cancel previous scheduled task and reschedule (debounce)
        if gid in _album_tasks:
            _album_tasks[gid].cancel()
        task = asyncio.create_task(_process_album(gid, context))
        _album_tasks[gid] = task
        return

    # ── Single photo ────────────────────────────────────────────────────────
    intent = detect_photo_intent(caption)
    if intent is None:
        return

    uid = _user_id(update)
    ext = _ext_from_msg(msg)

    status = await msg.reply_text("⏳ در حال پردازش با amir CLI...")

    input_path = await _download_media(msg, ext)
    if not input_path:
        await status.edit_text("❌ دانلود فایل ناموفق بود.")
        return

    try:
        if intent == "pdf":
            code, text, output = run_pdf(input_path)
            if code == 0 and output:
                await status.edit_text("📄 ارسال PDF...")
                await msg.reply_document(
                    document=open(output, "rb"),
                    filename=Path(output).name,
                    caption="📄 فایل PDF آماده‌ست | توسط amir CLI",
                )
                await status.delete()
                cleanup(output)
            else:
                await status.edit_text(text)

        elif intent == "resize":
            # Parse size from caption if present, e.g. "resize 1080" or "a4"
            import re
            size_match = re.search(r"(\d{3,4}x\d{3,4}|\d{3,4})", caption)
            size = size_match.group(1) if size_match else "1080"
            # "a4" keyword → A4 portrait at 150 dpi = 1240×1753
            if "a4" in caption.lower():
                size = "1240x1753"
            code, text, output = run_resize(input_path, size)
            if code == 0 and output:
                await status.edit_text("🖼 ارسال تصویر...")
                await msg.reply_photo(
                    photo=open(output, "rb"),
                    caption=f"🖼 ریسایز شد ({size}) | توسط amir CLI",
                )
                await status.delete()
                cleanup(output)
            else:
                await status.edit_text(text)

        else:
            await status.edit_text("⚠️ عملیات ناشناخته.")

    finally:
        cleanup(input_path)


# ── /qr command ───────────────────────────────────────────────────────────────

async def cmd_qr_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /qr <text>
    Generates a QR code PNG and sends it.
    """
    msg = update.effective_message
    text = " ".join(context.args).strip() if context.args else ""

    if not text:
        await msg.reply_text(
            "📌 **کیوآر کد**\n\nاستفاده: `/qr <متن یا لینک>`\n\nمثال:\n"
            "`/qr https://example.com`\n"
            "`/qr 09123456789`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    status = await msg.reply_text("⏳ در حال ساخت QR code...")
    code, reply_text, output = run_qr(text)

    if code == 0 and output:
        await msg.reply_photo(
            photo=open(output, "rb"),
            caption=f"📌 QR Code\n`{text}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        await status.delete()
        cleanup(output)
    else:
        await status.edit_text(reply_text)


# ── /pass command ─────────────────────────────────────────────────────────────

async def cmd_pass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /pass [length]
    Generates a secure random password.
    """
    msg = update.effective_message
    length = 16
    if context.args:
        try:
            length = max(8, min(128, int(context.args[0])))
        except ValueError:
            pass

    code, result = run_pass(length)
    await msg.reply_text(
        f"🔑 **پسورد تصادفی ({length} کاراکتر)**\n\n`{result}`",
        parse_mode=ParseMode.MARKDOWN,
    )


# ── /weather command ──────────────────────────────────────────────────────────

async def cmd_weather_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /weather [city]
    Returns weather info for a city.
    """
    msg = update.effective_message
    city = " ".join(context.args).strip() if context.args else "Tehran"

    status = await msg.reply_text(f"🌤 دریافت آب‌وهوای {city}...")
    code, result = run_weather(city)

    if result:
        await status.edit_text(f"```\n{result}\n```", parse_mode=ParseMode.MARKDOWN)
    else:
        await status.edit_text("❌ دریافت اطلاعات آب‌وهوا ناموفق بود.")


# ── /amir help card ───────────────────────────────────────────────────────────

AMIR_HELP = """\
🛠 **ابزارهای amir CLI**
━━━━━━━━━━━━━━

📄 **تبدیل عکس به PDF**
یه عکس بفرست + کپشن: `pdf` یا `پی‌دی‌اف` یا `a4`

🪪 **کارت ملی / شناسنامه روی یه صفحه A4**
دو طرف کارت رو **باهم** (به صورت آلبوم) انتخاب کن و بفرست
کپشن بنویس: `کارت ملی`
← ربات هر دو طرف رو روی یه صفحه A4 می‌چینه و PDF می‌ده

🖼 **ریسایز تصویر**
عکس بفرست + کپشن: `resize 1080` یا `a4`

📌 **QR code**
`/qr <متن یا لینک>`

🔑 **رمز عبور تصادفی**
`/pass [طول]`  (پیش‌فرض: ۱۶ کاراکتر)

🌤 **آب‌وهوا**
`/weather [شهر]`

━━━━━━━━━━━━━━
💡 برای آلبوم: توی تلگرام چند عکس رو باهم انتخاب کن، بفرست، کپشن بنویس.
"""


async def cmd_amir_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    await msg.reply_text(AMIR_HELP, parse_mode=ParseMode.MARKDOWN)


async def amir_album_continuation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Catches uncaptioned photos that are part of a media group already being tracked.
    Telegram sends album photos as separate updates; only the first has a caption.
    This handler forwards them to amir_media_handler so the album buffer gets filled.
    """
    msg = update.effective_message
    if msg and msg.media_group_id and msg.media_group_id in _album_buffer:
        await amir_media_handler(update, context)

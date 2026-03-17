import asyncio
import hashlib
import html
import os
import re
import shlex
import enum
import traceback
from pathlib import Path

from telegram import Update, ReplyKeyboardRemove
from telegram.error import BadRequest, NetworkError, TelegramError
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.core.config import SETTINGS, TEMP_DIR, AMIR_PATH, IS_DEV
from src.core.logger import logger
from src.utils.text_tools import get_msg, extract_link_from_text, smart_split
from src.utils.telegram import reply_and_delete, reply_with_countdown, safe_delete, report_error_to_admin
from src.features.downloader.utils import get_video_metadata, generate_thumbnail
from src.features.utility.utils import get_status_text, get_main_keyboard

ARMAGEDDON_CHANNEL_PROD = os.getenv("ARMAGEDDON_CHANNEL_PROD", "armageddon_war").strip().lstrip("@").lower()
ARMAGEDDON_CHANNEL_DEV = os.getenv("ARMAGEDDON_CHANNEL_DEV", "fin_ml").strip().lstrip("@").lower()
ARMAGEDDON_ZIP_TEXT = "Subtitle files and also the PDF transcript of the interview in Persian and English"
# Invisible signature to prevent infinite loops (Zero-Width Space)
BOT_SIGNATURE = "\u200b"

TG_API_ID = int(os.getenv("TG_API_ID", "0") or 0)
TG_API_HASH = os.getenv("TG_API_HASH", "").strip()
TG_SESSION = os.getenv("TG_SESSION_STRING", "").strip()


def _get_armageddon_target_channel() -> str:
    return ARMAGEDDON_CHANNEL_DEV if IS_DEV else ARMAGEDDON_CHANNEL_PROD


async def _download_large_video_pyrogram(chat_id: int, message_id: int, dest: Path) -> Path | None:
    """Download Telegram videos larger than Bot API practical limit via personal account."""
    if not TG_API_ID or not TG_API_HASH or not TG_SESSION:
        return None
    try:
        from pyrogram import Client

        async with Client(
            name=":memory:",
            api_id=TG_API_ID,
            api_hash=TG_API_HASH,
            session_string=TG_SESSION,
            no_updates=True,
        ) as user_client:
            pyro_msg = await user_client.get_messages(chat_id, message_id)
            if not pyro_msg or not pyro_msg.video:
                return None
            out = await user_client.download_media(pyro_msg.video, file_name=str(dest))
            if not out:
                return None
            result = Path(out)
            if not result.exists() or result.stat().st_size < 1024:
                result.unlink(missing_ok=True)
                return None
            return result
    except Exception as e:
        logger.error(f"Pyrogram download fallback failed: {e}")
        return None


async def _send_video_via_pyrogram(
    chat_id: int, 
    video_path: Path, 
    caption_html: str,
    width: int = 0,
    height: int = 0,
    duration: int = 0,
    thumb_path: Path | None = None
) -> bool:
    """Send large rendered videos to channel via personal account when Bot API rejects size."""
    logger.debug(f"[Pyrogram Fallback] 🚀 Starting manual upload process for chat_id={chat_id}")
    
    if not TG_API_ID or not TG_API_HASH or not TG_SESSION:
        logger.error("[Pyrogram Fallback] ❌ Missing TG_API credentials or Session String in .env!")
        return False
        
    try:
        from pyrogram import Client
        from pyrogram.enums import ParseMode as PyroParseMode
        import traceback
        logger.debug("[Pyrogram Fallback] 📦 Pyrogram library and enums imported successfully.")

        logger.debug(f"[Pyrogram Fallback] 🔄 Initializing Pyrogram Client for file: {video_path.name}")
        async with Client(
            name=":memory:",
            api_id=TG_API_ID,
            api_hash=TG_API_HASH,
            session_string=TG_SESSION,
            no_updates=True,
        ) as user_client:
            
            logger.debug("[Pyrogram Fallback] ✅ Authenticated successfully with personal account.")
            
            from src.core.config import SETTINGS
            
            upload_target = chat_id
            target_str = str(chat_id)
            
            if target_str == str(SETTINGS.get("armageddon_channel")) or target_str == "-1003185158962":
                upload_target = f"@{ARMAGEDDON_CHANNEL_DEV}" if IS_DEV else f"@{ARMAGEDDON_CHANNEL_PROD}"
                logger.info(f"[Pyrogram Fallback] 🔄 Overriding numeric ID {chat_id} with username: {upload_target}")
            else:
                try:
                    peer = await user_client.get_chat(chat_id)
                    logger.debug(f"[Pyrogram Fallback] 🎯 Entity resolved: {peer.title}")
                except Exception as e:
                    logger.warning(f"[Pyrogram Fallback] ⚠️ Direct chat_id resolution failed: {e}")

            logger.info(f"[Pyrogram Fallback] 📤 Uploading {video_path.name} to {upload_target}")
            
            async def progress(current, total):
                percent = (current / total) * 100
                if int(percent) % 25 == 0 and current > 0:
                    logger.debug(f"[Pyrogram Fallback] ⏳ Upload Progress: {percent:.1f}% ({current}/{total} bytes)")

            result = await user_client.send_video(
                chat_id=upload_target,
                video=str(video_path),
                caption=caption_html + BOT_SIGNATURE,
                parse_mode=PyroParseMode.HTML,
                supports_streaming=True,
                width=width if width > 0 else None,
                height=height if height > 0 else None,
                duration=duration if duration > 0 else None,
                thumb=str(thumb_path) if thumb_path and thumb_path.exists() else None,
                progress=progress
            )
            
            logger.info(f"[Pyrogram Fallback] 🏆 Upload COMPLETE! Message ID: {result.id}")
            return result.id
    except Exception as e:
        logger.error(f"[Pyrogram Fallback] ❌ FAILED for {video_path.name}: {e}")
        logger.debug(traceback.format_exc())
        return False
        return None


async def _send_with_fallback(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    reply_to_message_id: int | None,
    video_path: Path,
    quality_label: str,
    post_path: Path | None,
    low_quality_notice: bool = False,
) -> bool:
    """Send video via Bot API, fallback to Pyrogram if too large."""
    logger.info(f"📤 Attempting to send {quality_label} video: {video_path.name}")
    try:
        # Prepare caption once for both Bot API and Pyrogram
        _post_text = ""
        if low_quality_notice:
            res_val = 360 # Default fallback label helper
            _post_text = f"📦 Lower quality version for faster download ({res_val}p)"
        elif post_path and post_path.exists():
            _post_text = post_path.read_text(encoding="utf-8", errors="replace").strip()
            
        _caption_html, _overflow = smart_split(
            _post_text,
            header=f"<b>Quality:</b> {html.escape(quality_label)}",
            max_len=1024,
            overflow_suffix="Caption continues in the next message",
        )

        # Get metadata for high-quality display in Telegram
        meta = await get_video_metadata(video_path)
        width = int(meta.get("width", 0)) if meta else 0
        height = int(meta.get("height", 0)) if meta else 0
        duration = int(meta.get("duration", 0)) if meta else 0

        # Determine the best thumbnail (prefer pre-generated high-quality .jpg from amir-cli)
        thumb_path = None
        
        # 1. PRIORITY: Find the original YouTube thumb (it's the most professional one)
        # Search for .jpg files that are prefixes of the current video name
        video_stem = video_path.stem
        candidates = sorted(video_path.parent.glob("*.jpg"), key=lambda p: len(p.stem), reverse=True)
        for cand in candidates:
            # We want a candidate that is a prefix and doesn't look like a generated frame (no _subbed, no _q, no resolution)
            if cand.stem in video_stem:
                if "_subbed" not in cand.stem and "_q" not in cand.stem:
                    thumb_path = cand
                    logger.debug(f"[Thumbnail] 💎 High-quality original found: {cand.name}")
                    break

        # 2. FALLBACK: Try exact match (e.g. video_subbed.jpg)
        if not thumb_path:
            exact_thumb = video_path.with_suffix(".jpg")
            if exact_thumb.exists():
                thumb_path = exact_thumb
                logger.debug(f"[Thumbnail] 🔍 Using exact match: {thumb_path.name}")

        # 3. Last resort: generate on the fly
        if not thumb_path:
            logger.debug(f"[Thumbnail] ⚠️ No high-quality thumb found. Generating from video...")
            thumb_path = await generate_thumbnail(video_path)

        logger.info(f"[Metadata] 📊 {video_path.name}: {width}x{height} | {duration}s | Thumb: {thumb_path.name if thumb_path else 'None'}")

        await _send_armageddon_video(
            context=context,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            video_path=video_path,
            caption_html=_caption_html,
            overflow_text=_overflow,
            width=width,
            height=height,
            duration=duration,
            thumb_path=thumb_path,
        )
        logger.info(f"✅ {quality_label} sent successfully via Bot API.")
        return True
    except (BadRequest, NetworkError, TelegramError) as e:
        error_msg = str(e).lower()
        if "entity too large" not in error_msg and "413" not in error_msg:
            logger.error(f"❌ Bot API failure for {quality_label} (not size related): {e}")
            raise
        
        logger.warning(f"⚠️ {quality_label} is too large for Bot API ({e}). Falling back to Pyrogram...")
        
        # Pyrogram fallback with full metadata
        uploaded_id = await _send_video_via_pyrogram(
            chat_id=chat_id, 
            video_path=video_path, 
            caption_html=_caption_html,
            width=width,
            height=height,
            duration=duration,
            thumb_path=thumb_path
        )
        if uploaded_id:
            logger.info(f"✅ {quality_label} sent successfully via Pyrogram (ID: {uploaded_id}).")
            if _overflow.strip():
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=html.escape(_overflow.strip()),
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=uploaded_id,
                )
            return True
        else:
            logger.error(f"❌ Pyrogram fallback also FAILED for {quality_label}.")
            return False

async def cmd_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main keyboard."""
    logger.info(f"🚀 Command /start triggered by {update.effective_user.id}")
    user = update.effective_user
    text = get_msg("welcome", user.id).format(name=user.first_name)
    
    # Use reply_with_countdown for welcome message in group, or just reply in private
    # Original code used reply_with_countdown.
    # But wait, reply_with_countdown only counts down in groups.
    # In private chat it just replies (and returns msg).
    
    await reply_with_countdown(
        update, 
        context, 
        text, 
        delay=60, 
        parse_mode=ParseMode.MARKDOWN, 
        reply_markup=get_main_keyboard(user.id)
    )

async def cmd_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    user_id = update.effective_user.id
    # Use reply_and_delete to keep chat clean
    await reply_and_delete(
        update, 
        context, 
        get_msg("help_msg", user_id), 
        delay=60, 
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system status and user quota"""
    logger.info("📊 Command /status triggered")
    user_id = update.effective_user.id
    
    full_status = get_status_text(user_id)
    await reply_with_countdown(
        update, 
        context, 
        full_status, 
        delay=30, 
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_close_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove keyboard and close menu"""
    logger.info("❌ Command /close triggered")
    user_id = update.effective_user.id
    await reply_and_delete(
        update, 
        context, 
        get_msg("menu_closed", user_id), 
        delay=5, 
        reply_markup=ReplyKeyboardRemove()
    )

async def cmd_toggle_dl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle downloader feature (Admin/Global setting)"""
    logger.info("📥 Command /toggle_dl triggered")
    # Note: Authorization check should ideally be here if not handled by decorator
    # The original code just toggled. Assuming access control is separate or permissive for mechanics.
    # But wait, modifying global settings usually requires admin?
    # In original `su6i_yar.py`, there was no explicit admin check inside the handler, 
    # but maybe the handler was added with a filter?
    # Let's assume for now we port logic as is.
    
    SETTINGS["download"] = not SETTINGS["download"]
    state = get_msg("dl_on", update.effective_user.id) if SETTINGS["download"] else get_msg("dl_off", update.effective_user.id)
    await reply_and_delete(
        update, 
        context, 
        get_msg("action_dl", update.effective_user.id).format(state=state), 
        delay=10
    )

async def cmd_toggle_fc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle fact-check feature (Admin/Global setting)"""
    logger.info("🧠 Command /toggle_fc triggered")
    SETTINGS["fact_check"] = not SETTINGS["fact_check"]
    state = get_msg("fc_on", update.effective_user.id) if SETTINGS["fact_check"] else get_msg("fc_off", update.effective_user.id)
    await reply_and_delete(
        update, 
        context, 
        get_msg("action_fc", update.effective_user.id).format(state=state), 
        delay=10
    )

async def cmd_stop_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin only: Stop the bot process."""
    user_id = update.effective_user.id
    if user_id != SETTINGS["admin_id"]:
        await update.message.reply_text(get_msg("only_admin", user_id))
        return
        
    logger.info("🛑 Stop Button Triggered")
    await update.message.reply_text(get_msg("bot_stop", user_id), reply_markup=ReplyKeyboardRemove())
    
    import os, signal, asyncio
    await asyncio.sleep(1)
    os.kill(os.getpid(), signal.SIGKILL)

async def cmd_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches the cached detailed analysis."""
    from src.features.fact_check.utils import LAST_ANALYSIS_CACHE
    
    logger.info("🔍 Command /detail triggered")
    msg = update.effective_message
    user_id = update.effective_user.id
    
    # Check Cache
    detail_text = LAST_ANALYSIS_CACHE.get(user_id)
    
    if not detail_text:
        await msg.reply_text("⛔ No saved analysis found. Please analyze a text first.")
        return

    # Decide reply target
    reply_target_id = msg.message_id
    if msg.reply_to_message:
        reply_target_id = msg.reply_to_message.message_id

    # Chunking logic
    max_length = 3900
    if len(detail_text) <= max_length:
        await msg.reply_text(detail_text, parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_target_id)
    else:
        # Simple splitting
        parts = []
        while detail_text:
            if len(detail_text) <= max_length:
                parts.append(detail_text)
                break
            # Find nearest newline
            split_idx = detail_text.rfind('\n', 0, max_length)
            if split_idx == -1: split_idx = max_length
            parts.append(detail_text[:split_idx])
            detail_text = detail_text[split_idx:]
            
        for i, chunk in enumerate(parts):
            await msg.reply_text(f"📄 Part {i+1}/{len(parts)}\n\n{chunk}", parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_target_id)

async def cmd_fun_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process media/links for the Fun channel."""
    from src.utils.text_tools import extract_link_from_text
    from src.features.downloader.utils import download_instagram
    import os
    
    msg = update.effective_message
    user_id = update.effective_user.id
    is_target_channel = (msg.chat.username == "just_for_fun_persian")
    
    # Only Admin or Channel can use this
    if not is_target_channel and user_id != SETTINGS["admin_id"]:
        return

    # Determine Target (File or URL)
    target_file = msg.video or msg.animation or (msg.document if msg.document and msg.document.mime_type and msg.document.mime_type.startswith("video/") else None)
    target_url = None
    
    if not target_file:
        text_content = msg.caption or msg.text or ""
        target_url = extract_link_from_text(msg.caption_entities or msg.entities, text_content)
        
        # Check reply
        if not target_url and msg.reply_to_message:
            reply = msg.reply_to_message
            target_file = reply.video or reply.animation or (reply.document if reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/") else None)
            if not target_file:
                target_url = extract_link_from_text(reply.caption_entities or reply.entities, reply.caption or reply.text or "")

    if not target_url and not target_file:
        if msg.text and msg.text.startswith("/fun"):
             await msg.reply_text("❌ Error: No link or file found!", reply_to_message_id=msg.message_id)
        return

    target_channel_id = "@just_for_fun_persian"
    custom_header = "🎥 <b>Just For Fun</b> | @just_for_fun_persian"
    status_msg = None

    if is_target_channel:
        await safe_delete(msg)
    else:
        status_msg = await msg.reply_text("📥 Processing...", reply_to_message_id=msg.message_id)

    try:
        # Case 1: File
        if target_file:
            # Forward directly if possible or re-upload? 
            # Re-upload to add caption
            # For now, simplistic approach: Copy message
            await context.bot.copy_message(
                chat_id=target_channel_id,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id if msg.video else (msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id),
                caption=custom_header,
                parse_mode=ParseMode.HTML
            )
            if status_msg: await status_msg.edit_text(f"✅ Posted: {target_channel_id}")
            return

        # Case 2: URL
        if target_url:
            path = await download_instagram(target_url)
            if path and path.exists():
                await context.bot.send_video(
                    chat_id=target_channel_id,
                    video=open(path, 'rb'),
                    caption=custom_header,
                    parse_mode=ParseMode.HTML,
                    read_timeout=120, 
                    write_timeout=120, 
                    pool_timeout=120
                )
                path.unlink() # Cleanup
                if status_msg: await status_msg.edit_text(f"✅ Posted: {target_channel_id}")
            else:
                if status_msg: await status_msg.edit_text("❌ Download failed.")
                
    except Exception as e:
        logger.error(f"Fun Error: {e}")
        if status_msg: await status_msg.edit_text(f"❌ Error: {e}")


async def cmd_subtitle_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/subtitle in modular app: reply to a link/video, default source=auto target=fa."""
    msg = update.effective_message
    if not msg:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    if user_id != SETTINGS.get("admin_id"):
        await msg.reply_text("⛔ This command is only active for admins.")
        return

    if not msg.reply_to_message:
        await msg.reply_text("↩️ Reply this command to a link/video message.")
        return

    args = context.args or []
    if len(args) == 0:
        src_lang, tgt_lang = "auto", "fa"
    elif len(args) == 1:
        src_lang, tgt_lang = "auto", args[0].strip().lower()
    elif len(args) == 2:
        src_lang, tgt_lang = args[0].strip().lower(), args[1].strip().lower()
    else:
        await msg.reply_text("📝 Template: /subtitle [src] [tgt]\nExample: /subtitle auto fa")
        return

    if src_lang == tgt_lang:
        await msg.reply_text("⚠️ Source and target languages cannot be the same.")
        return

    reply = msg.reply_to_message
    text_content = reply.caption or reply.text or ""
    url = extract_link_from_text(reply.caption_entities or reply.entities, text_content)
    fallback_url = url

    target_video = reply.video or (
        reply.document
        if reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/")
        else None
    )

    if not url and not target_video:
        await msg.reply_text("❌ No link or video file found.")
        return

    content_key = url if url else getattr(target_video, "file_unique_id", f"msg-{reply.message_id}")
    content_id = hashlib.sha256(content_key.encode()).hexdigest()[:16]
    # Unified flat folder for manual jobs
    work_dir = Path(TEMP_DIR) / "manual_subtitles"
    work_dir.mkdir(parents=True, exist_ok=True)

    input_ref = url
    if target_video:
        ext = ".mp4"
        if getattr(target_video, "file_name", None):
            ext = Path(target_video.file_name).suffix or ".mp4"
        local_video = work_dir / f"reply_video{ext}"

        # Strategy 1: Bot API download (fast path for smaller files)
        try:
            tg_file = await target_video.get_file()
            await tg_file.download_to_drive(custom_path=local_video)
            input_ref = str(local_video)
        except Exception as _bot_dl_err:
            logger.warning(f"Bot API download failed, trying Pyrogram fallback: {_bot_dl_err}")
            # Strategy 2: Personal account via Pyrogram (large-file fallback)
            pyro_path = await _download_large_video_pyrogram(reply.chat_id, reply.message_id, local_video)
            if pyro_path and pyro_path.exists():
                input_ref = str(pyro_path)
            elif fallback_url:
                # Strategy 3: fallback to URL embedded in replied message, if any
                input_ref = fallback_url
            else:
                raise RuntimeError("Telegram video download failed (Bot API + Pyrogram).")

    status_msg = await msg.reply_text(
        f"⏳ Starting auto-subtitle\nSource: {src_lang}\nTarget: {tgt_lang}",
        reply_to_message_id=msg.message_id,
    )

    try:
        video_path, post_file, bundle_zip = await _run_armageddon_subtitle_job(
            status_msg=status_msg,
            url=input_ref,
            source_lang=src_lang,
            sub_langs=["auto", tgt_lang] if src_lang == "auto" else [src_lang, tgt_lang],
            work_dir=work_dir,
            quality_mode="720",
        )

        await _send_armageddon_video(
            context=context,
            chat_id=msg.chat_id,
            reply_to_message_id=msg.message_id,
            video_path=video_path,
            quality_label="720p",
            post_path=post_file,
        )

        if bundle_zip and bundle_zip.exists():
            with open(bundle_zip, "rb") as f:
                await context.bot.send_document(
                    chat_id=msg.chat_id,
                    document=f,
                    filename=bundle_zip.name,
                    caption=ARMAGEDDON_ZIP_TEXT,
                    reply_to_message_id=msg.message_id,
                    read_timeout=300,
                    write_timeout=300,
                    pool_timeout=300,
                )
        await safe_delete(status_msg)
    except Exception as e:
        logger.error(f"Subtitle command failed: {e}")
        try:
            await status_msg.edit_text(f"❌ Failed:\n{str(e)[:700]}")
        except Exception:
            pass
        await report_error_to_admin(context, user_id, "subtitle", str(e)[:1500])


def _parse_subtitle_directives(text_content: str) -> tuple[str, list[str]]:
    """Parse optional subtitle CLI-style overrides embedded alongside the URL.

    Supported examples:
      -s en
      --source en
      -t en fa
      --sub auto fa
    """
    source_lang = "auto"
    sub_langs = ["auto", "fa"]

    if not text_content:
        return source_lang, sub_langs

    try:
        tokens = shlex.split(text_content.replace("\n", " "))
    except Exception:
        tokens = text_content.replace("\n", " ").split()

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("-s", "--source") and i + 1 < len(tokens):
            candidate = tokens[i + 1].strip().lower()
            if re.fullmatch(r"[a-z]{2,5}|auto|detect", candidate):
                source_lang = candidate
            i += 2
            continue

        if tok in ("-t", "--sub"):
            parsed: list[str] = []
            j = i + 1
            while j < len(tokens):
                candidate = tokens[j].strip().lower()
                if candidate.startswith("-"):
                    break
                if not re.fullmatch(r"[a-z]{2,5}|auto|detect|source", candidate):
                    break
                parsed.append(candidate)
                j += 1
            if parsed:
                sub_langs = parsed
            i = j
            continue

        i += 1

    return source_lang, sub_langs


async def _run_armageddon_subtitle_job(
    status_msg,
    url: str,
    source_lang: str,
    sub_langs: list[str],
    work_dir: Path,
    quality_mode: str,
    extreme: bool = False,
) -> tuple[Path, Path | None, Path | None]:
    """Run amir subtitle with progress streaming and return video/post/zip outputs."""
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # -------------------------------------------------------------------------
    # SMART CACHING LOGIC: Check for marker file in the flat folder
    # -------------------------------------------------------------------------
    marker_file = work_dir / f".done_{hashlib.sha256(url.encode()).hexdigest()[:16]}_{quality_mode}"
    if marker_file.exists():
        try:
            import json
            cache_data = json.loads(marker_file.read_text())
            vid_path = Path(cache_data.get("video", ""))
            post_path = Path(cache_data.get("post", "")) if cache_data.get("post") else None
            zip_path = Path(cache_data.get("zip", "")) if cache_data.get("zip") else None
            
            # CRITICAL: Verify the cached video file is healthy and contains requested quality
            video_ok = vid_path.exists() and vid_path.stat().st_size > 1024 * 1024 and str(quality_mode) in vid_path.name
            
            # ALSO CRITICAL: If any output or sidecar file is missing, we must redo everything.
            # (Post text, Zip bundle, SRT, ASS, and PDF)
            post_ok = post_path and post_path.exists()
            zip_ok = zip_path and zip_path.exists()
            
            # Check for sidecar files in the work directory (SRTs, ASS, PDF)
            # We look for at least one of each to ensure the amir job finished correctly.
            srt_ok = any(work_dir.glob("*.srt"))
            ass_ok = any(work_dir.glob("*.ass"))
            pdf_ok = any(work_dir.glob("*.pdf"))

            if video_ok and post_ok and zip_ok and srt_ok and ass_ok and pdf_ok:
                logger.info(f"⏭️ [CACHE HIT] Marker found for {quality_mode} version: {vid_path.name}")
                if status_msg is not None:
                    try:
                        await status_msg.edit_text(f"⏭️ {quality_mode}p version already processed. Sending...")
                    except Exception:
                        pass
                return vid_path, post_path, zip_path
            else:
                missing_info = []
                if not video_ok: missing_info.append("Video")
                if not post_ok: missing_info.append("Post (.txt)")
                if not zip_ok: missing_info.append("Zip")
                if not srt_ok: missing_info.append("SRT")
                if not ass_ok: missing_info.append("ASS")
                if not pdf_ok: missing_info.append("PDF")
                logger.info(f"🔄 [CACHE MISS] Missing: {', '.join(missing_info)}. Re-running...")
        except Exception as e:
            logger.warning(f"Cache marker read failed: {e}")

    before_videos = {p.resolve() for p in work_dir.glob("*_subbed.mp4")}


    cmd = [
        "bash", AMIR_PATH, "video", "subtitle", url,
        "--browser", "none",
        "-s", source_lang,
        "-t", *sub_langs,
        "--post",
        "--save", "pdf",
        "--max-lines", "1",
        "--keep-thumb",
    ]
    if extreme:
        cmd.append("--extreme")
    elif quality_mode in ("720", "480", "360", "240"):
        cmd.extend(["--resolution", quality_mode])

    logger.info(f"🎬 [armageddon] Running: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=4 * 1024 * 1024,
        cwd=str(work_dir),
    )

    start_ts = asyncio.get_event_loop().time()
    out_lines: list[str] = []
    err_lines: list[str] = []
    last_progress_time = [start_ts]
    last_stage_text = [f"⏳ Starting processing of {quality_mode}p version..."]

    async def _handle_line(line: str):
        now = asyncio.get_event_loop().time()
        m = re.search(r'PROGRESS:(\d+):(.+)', line)
        if m:
            pct = min(100, max(0, int(m.group(1))))
            stage_clean = re.sub(r'\s*\(\d+%\)\s*$', '', m.group(2)).strip()
            elapsed = int(now - start_ts)
            elapsed_str = f"{elapsed // 60}:{elapsed % 60:02d}"
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            text = f"Version {quality_mode}p\n{stage_clean}\n{bar} {pct}%\n⏱ Elapsed: {elapsed_str}"
            last_progress_time[0] = now
            last_stage_text[0] = text
            if status_msg is not None:
                try:
                    await status_msg.edit_text(text[:4000])
                except Exception:
                    pass
        
        # Detailed logging for transparency in bot.log
        if not m:
            logger.info(f"🎞️ [amir-out] {line}")
        else:
             logger.debug(f"🎞️ [amir-progress] {line}")
             return

        mf = re.search(r'Run\s*\|\s*([\d.]+)%\s*\|.*?ETA:\s*(\S+)', line)
        if mf and (now - last_progress_time[0]) >= 5.0:
            render_pct = min(100, int(float(mf.group(1))))
            eta = mf.group(2)
            overall_pct = 88 + render_pct * 10 // 100
            elapsed = int(now - start_ts)
            elapsed_str = f"{elapsed // 60}:{elapsed % 60:02d}"
            bar = "█" * (overall_pct // 10) + "░" * (10 - overall_pct // 10)
            text = f"Version {quality_mode}p\n🎞️ Rendering final video\n{bar} {overall_pct}% (FFmpeg: {render_pct}%)\n⏱ Elapsed: {elapsed_str} | ETA: {eta}"
            last_progress_time[0] = now
            last_stage_text[0] = text
            if status_msg is not None:
                try:
                    await status_msg.edit_text(text[:4000])
                except Exception:
                    pass

    async def _drain(stream, acc: list[str]):
        buf = b""
        while True:
            chunk = await stream.read(65536)
            if not chunk:
                break
            buf += chunk
            parts = re.split(rb'[\r\n]+', buf)
            buf = parts.pop()
            for part in parts:
                line = part.decode(errors="replace").strip()
                if line:
                    acc.append(line)
                    await _handle_line(line)
        if buf:
            line = buf.decode(errors="replace").strip()
            if line:
                acc.append(line)
                await _handle_line(line)

    heartbeat_task = None
    async def _heartbeat():
        try:
            while True:
                await asyncio.sleep(60)
                since_last = asyncio.get_event_loop().time() - last_progress_time[0]
                if since_last >= 55:
                    elapsed = int(asyncio.get_event_loop().time() - start_ts)
                    elapsed_str = f"{elapsed // 60}:{elapsed % 60:02d}"
                    if status_msg is not None:
                        await status_msg.edit_text(f"{last_stage_text[0]}\n⌛ {elapsed_str} Processing...")
        except asyncio.CancelledError:
            pass

    heartbeat_task = asyncio.create_task(_heartbeat())
    try:
        await asyncio.gather(_drain(process.stdout, out_lines), _drain(process.stderr, err_lines))
        await process.wait()
    finally:
        heartbeat_task.cancel()

    if process.returncode != 0:
        err_out = ("\n".join(out_lines) + "\n" + "\n".join(err_lines))[-1000:]
        raise RuntimeError(f"amir video subtitle failed ({quality_mode}): {err_out[-800:]}")

    after_videos = sorted(work_dir.glob("*_subbed.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    # Strictly pick a video that matches the quality mode we requested
    # to avoid collisions when running multiple resolutions in a flat folder.
    picked_video = next((p for p in after_videos if str(quality_mode) in p.name and p.resolve() not in before_videos), None)
    
    if picked_video is None:
        # Fallback to any recent video containing the quality string
        picked_video = next((p for p in after_videos if str(quality_mode) in p.name), None)

    if picked_video is None:
        raise RuntimeError(f"No rendered video found for quality={quality_mode}")

    # Derived base name for finding related sidecar files (strip resolution and _subbed)
    # e.g. "VideoTitle_720p_subbed.mp4" -> "VideoTitle"
    base_prefix = picked_video.name.split('_' + str(quality_mode))[0]
    logger.debug(f"[Lookup] 🔍 Using prefix '{base_prefix}' for sidecar files.")

    post_file = None
    post_candidates = sorted(work_dir.glob(f"{base_prefix}*_fa_telegram.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if post_candidates:
        post_file = post_candidates[0]

    zip_file = None
    zip_candidates = sorted(work_dir.glob(f"{base_prefix}*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if zip_candidates:
        zip_file = zip_candidates[0]

    # Write marker file for future cache hits in flat folder
    try:
        import json
        marker_data = {
            "url": url,
            "video": str(picked_video),
            "post": str(post_file) if post_file else None,
            "zip": str(zip_file) if zip_file else None,
            "timestamp": asyncio.get_event_loop().time()
        }
        marker_file.write_text(json.dumps(marker_data))
    except Exception as e:
        logger.error(f"Failed to write cache marker: {e}")

    return picked_video, post_file, zip_file


async def _send_armageddon_video(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    reply_to_message_id: int | None,
    video_path: Path,
    caption_html: str,
    overflow_text: str = "",
    width: int = 0,
    height: int = 0,
    duration: int = 0,
    thumb_path: Path | None = None,
):
    if not (width and height and duration):
        meta = await get_video_metadata(video_path)
        duration = int(meta.get("duration", 0)) if meta else duration
        width = int(meta.get("width", 0)) if meta else width
        height = int(meta.get("height", 0)) if meta else height
    
    if not thumb_path or not thumb_path.exists():
        thumb_path = await generate_thumbnail(video_path)
    
    thumb_file = open(thumb_path, "rb") if thumb_path and thumb_path.exists() else None
    try:
        with open(video_path, "rb") as f:
            sent = await context.bot.send_video(
                chat_id=chat_id,
                video=f,
                caption=caption_html + BOT_SIGNATURE,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=reply_to_message_id,
                duration=duration,
                width=width,
                height=height,
                thumbnail=thumb_file,
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300,
                pool_timeout=300,
            )
    finally:
        if thumb_file:
            thumb_file.close()

    if overflow_text.strip():
        await context.bot.send_message(
            chat_id=chat_id,
            text=html.escape(overflow_text.strip()),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=sent.message_id,
        )


async def _process_armageddon_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if not msg:
        return
    chat_username = (msg.chat.username or "").strip().lstrip("@")

    text_content = msg.caption or msg.text or ""
    
    # --- CRITICAL ANTI-LOOP GUARD (DO NOT REMOVE) ---
    # Pyrogram uploads via personal account appear as regular channel posts.
    # Standard bot uploads also trigger channel_post updates.
    # We use an invisible Zero-Width Space signature (\u200b) to identify our own posts.
    # Removing this will cause an INFINITE LOOP of processing and deletion.
    if text_content.endswith(BOT_SIGNATURE):
        logger.debug("Omitted channel post (identified as bot output via invisible signature).")
        return
        
    url = extract_link_from_text(msg.caption_entities or msg.entities, text_content)
    if not url:
        return

    # Mirror @just_for_fun_persian behavior: remove source link post immediately,
    # keep channel clean and publish only processed subtitle outputs.
    await safe_delete(msg)

    source_lang, sub_langs = _parse_subtitle_directives(text_content)
    content_id = hashlib.sha256(url.encode()).hexdigest()[:16]
    # Unified flat folder for Armageddon jobs as requested
    work_dir = Path(TEMP_DIR) / "armageddon_subtitles"
    work_dir.mkdir(parents=True, exist_ok=True)

    reply_target_id = None

    # System/progress updates must stay out of public channel.
    status_msg = None
    admin_id = SETTINGS.get("admin_id")
    if admin_id:
        try:
            status_msg = await context.bot.send_message(
                chat_id=admin_id,
                text=f"⏳ Starting auto-subtitle processing\nChannel: @{chat_username}\nLink: {url}",
            )
        except Exception:
            status_msg = None

    try:
        if status_msg is not None:
             await status_msg.edit_text("⏳ Processing 360p (Extreme) first, then 720p...")

        # Sequential processing (User requested 360p first for speed optimization)
        # 1. Extreme 360p (Fastest, generates Whisper cache)
        res_360 = await _run_armageddon_subtitle_job(
            status_msg=status_msg,
            url=url,
            source_lang=source_lang,
            sub_langs=sub_langs,
            work_dir=work_dir,
            quality_mode="360",
            extreme=True,
        )
        video_360, _, bundle_zip = res_360

        # 2. HQ 720p (Will reuse f140.m4a audio stream kept by previous job)
        res_720 = await _run_armageddon_subtitle_job(
            status_msg=status_msg,
            url=url,
            source_lang=source_lang,
            sub_langs=sub_langs,
            work_dir=work_dir,
            quality_mode="720",
        )
        video_720, post_file, _ = res_720
        
        # Send 720p
        sent_720 = await _send_with_fallback(
            context=context,
            chat_id=msg.chat_id,
            reply_to_message_id=reply_target_id,
            video_path=video_720,
            quality_label="720p",
            post_path=post_file,
        )

        if not sent_720:
            if status_msg is not None:
                await status_msg.edit_text("⚠️ 720p delivery failed; generating 480p version...")
                
            video_480, post_file_480, _ = await _run_armageddon_subtitle_job(
                status_msg=status_msg,
                url=url,
                source_lang=source_lang,
                sub_langs=sub_langs,
                work_dir=work_dir,
                quality_mode="480",
            )
            await _send_with_fallback(
                context=context,
                chat_id=msg.chat_id,
                reply_to_message_id=reply_target_id,
                video_path=video_480,
                quality_label="480p",
                post_path=post_file_480 or post_file,
            )

        # Send 360p
        await _send_with_fallback(
            context=context,
            chat_id=msg.chat_id,
            reply_to_message_id=reply_target_id,
            video_path=video_360,
            quality_label="360p",
            post_path=None,
            low_quality_notice=True,
        )

        if bundle_zip and bundle_zip.exists():
            with open(bundle_zip, "rb") as f:
                await context.bot.send_document(
                    chat_id=msg.chat_id,
                    document=f,
                    filename=bundle_zip.name,
                    caption=ARMAGEDDON_ZIP_TEXT,
                    reply_to_message_id=reply_target_id,
                    read_timeout=300,
                    write_timeout=300,
                    pool_timeout=300,
                )

        await safe_delete(status_msg)
    except Exception as e:
        logger.error(f"Armageddon subtitle flow failed: {e}")
        try:
            await status_msg.edit_text(f"❌ Auto-processing failed:\n{str(e)[:700]}")
        except Exception:
            pass
        await report_error_to_admin(context, 0, "armageddon_channel_subtitle", str(e)[:1500])
    finally:
        # User has requested to NOT delete any files. 
        # A separate cleanup task handles old files.
        pass

async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-process posts in @just_for_fun_persian"""
    msg = update.channel_post
    if not msg: return

    # Reply posts are bot outputs in our automation flows — skip to avoid loops.
    if msg.reply_to_message:
        return

    chat_username = (msg.chat.username or "").strip().lstrip("@").lower()
    if chat_username == _get_armageddon_target_channel():
        await _process_armageddon_channel_post(update, context)
        return
    
    if msg.chat.username != "just_for_fun_persian":
        return
        
    text_content = msg.caption or msg.text or ""
    if "Just For Fun" in text_content:
        return # Loop protection

    # Check media/link
    has_media = msg.video or msg.animation or (msg.document and msg.document.mime_type and msg.document.mime_type.startswith("video/"))
    has_link = "http" in text_content
    
    if has_media or has_link:
        await cmd_fun_handler(update, context)


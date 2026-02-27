from pathlib import Path
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from src.core.config import SETTINGS, STORAGE_DIR, TEMP_DIR
from src.core.database import USER_LANG
from src.core.logger import logger
from src.utils.text_tools import get_msg
from src.utils.telegram import reply_and_delete, safe_delete
from src.features.downloader.utils import (
    download_instagram,
    download_video,
    detect_platform,
    download_instagram_batch,
    compress_video,
    get_video_metadata,
    generate_thumbnail
)

async def cmd_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force download manual override"""
    logger.info("📥 Command /dl triggered")
    msg = update.message
    if not msg: return
    user_id = update.effective_user.id
    
    # 1. Determine Target (Link & Reply ID)
    target_link = ""
    reply_to_id = msg.message_id
    target_video = None
    
    if context.args:
        target_link = context.args[0]
    elif msg.reply_to_message:
        r = msg.reply_to_message
        if r.video: target_video = r.video
        elif r.document and r.document.mime_type and r.document.mime_type.startswith("video/"):
            target_video = r.document
            
        target_link = r.text or r.caption or ""
        reply_to_id = r.message_id
    
    # 2. Handle Video File Processing (File -> Compress -> Send)
    if target_video:
        file_size_mb = target_video.file_size / (1024 * 1024)
        if file_size_mb > 19.5:
            await reply_and_delete(update, context, 
                get_msg("err_too_large", user_id),
                delay=15
            )
            return

        status_msg = await msg.reply_text(get_msg("downloading", user_id), reply_to_message_id=reply_to_id)
        try:
            timestamp = int(asyncio.get_event_loop().time())
            filename = Path(TEMP_DIR) / f"dl_file_{timestamp}.mp4"
            
            new_file = await target_video.get_file()
            await new_file.download_to_drive(custom_path=filename)
            
            if await compress_video(filename):
                logger.info(f"✅ Video processed: {filename}")
            
            await send_video_file(context.bot, msg.chat.id, filename, caption="🎥 Processed Video", reply_to=reply_to_id)
            await safe_delete(status_msg)
            
        except Exception as e:
            logger.error(f"DL File Error: {e}")
            await status_msg.edit_text(get_msg("err_dl", user_id))
        finally:
            if filename.exists(): filename.unlink()
        return

    # 3. Handle Link
    if not target_link:
        await reply_and_delete(update, context, get_msg("dl_usage_error", user_id), delay=10)
        return

    # Check if Batch Download (Instagram Profile only)
    platform = detect_platform(target_link)
    if platform == "instagram" and ("/reels/" not in target_link and "/p/" not in target_link and "/reel/" not in target_link):
        # Additional args: [link, count, filter]
        count = 5
        title_filter = None
        reverse_order = False # Default: Oldest-to-Newest (Series)
        
        if len(context.args) > 1:
            arg1 = context.args[1].lower()
            if arg1 == "all":
                count = 999
            elif arg1 == "last":
                reverse_order = True
                if len(context.args) > 2:
                    try:
                        count = int(context.args[2])
                        if len(context.args) > 3:
                            title_filter = " ".join(context.args[3:])
                    except ValueError:
                        count = 5
                        title_filter = " ".join(context.args[2:])
            else:
                try:
                    count = int(arg1)
                except ValueError:
                    title_filter = " ".join(context.args[1:])
                
        if not reverse_order and len(context.args) > 2 and title_filter is None:
            title_filter = " ".join(context.args[2:])

        await handle_instagram_batch(update, context, target_link, count, title_filter, reverse_order)
    else:
        await handle_video_link(update, context, target_link, reply_to_id)

async def handle_instagram_batch(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, count: int, title_filter: str, reverse_order: bool = False):
    """Batch download logic"""
    msg = update.message
    user_id = update.effective_user.id
    
    order_label = "جدیدترین‌ها" if reverse_order else "قدیمی‌ترین‌ها (سریالی)"
    status_msg = await msg.reply_text(f"📂 در حال استخراج لیست {order_label} (حداکثر {count} مورد)...")
    
    try:
        urls = await download_instagram_batch(url, count, title_filter, reverse_order=reverse_order)
        
        if not urls:
            await status_msg.edit_text("❌ هیچ ویدیویی برای دانلود پیدا نشد.")
            return
            
        await status_msg.edit_text(f"✅ {len(urls)} ویدیو پیدا شد. در حال ارسال...")
        
        for i, video_url in enumerate(urls):
            # Update status for progress
            if i > 0:
                await status_msg.edit_text(f"📥 در حال دانلود و ارسال {i+1} از {len(urls)}...")
            
            # Use existing single-link handler for each URL
            # We don't want to reply to the original message for every single one if it's a batch?
            # Actually, let's just send them one by one.
            try:
                logger.info(f"⬇️ Downloading batch item {i+1}/{len(urls)}: {video_url}")
                video_path = await download_instagram(video_url)
                
                if video_path and video_path.exists():
                    await compress_video(video_path)
                    
                    # 📝 Fetch Metadata (Caption) from yt-dlp's .info.json
                    full_caption = ""
                    # Check multiple possible naming schemes
                    info_files = [
                        video_path.with_suffix(".mp4.info.json"),
                        video_path.with_suffix(".info.json"),
                        Path(str(video_path).replace(".mp4", ".info.json"))
                    ]
                    
                    for info_file in info_files:
                        if info_file.exists():
                            try:
                                import json
                                info_data = json.loads(info_file.read_text(encoding="utf-8"))
                                full_caption = info_data.get("description", "") or info_data.get("title", "")
                                info_file.unlink() # Clean up
                                break
                            except Exception as e:
                                logger.error(f"⚠️ Failed to read .info.json ({info_file.name}): {e}")
                    
                    # ✂️ Smart Paragraph-Aware Splitting
                    base_footer = f"\n\n#ویدیو_{i+1}\n📥 @Su6i_Yar_Bot"
                    limit = 1024 - len(base_footer) - 10 # Buffer
                    
                    final_caption = ""
                    extra_text = ""
                    
                    if not full_caption:
                        final_caption = f"🎬 {title_filter or 'قسمت'} {i+1}{base_footer}"
                    else:
                        # Split by paragraphs
                        paragraphs = full_caption.split('\n') # Simple split for now, refine if needed
                        
                        current_batch = []
                        current_len = 0
                        split_happened = False
                        
                        for p in paragraphs:
                            p_len = len(p) + 1 # +1 for newline
                            if not split_happened and (current_len + p_len <= limit):
                                current_batch.append(p)
                                current_len += p_len
                            else:
                                split_happened = True
                                extra_text += p + "\n"
                        
                        main_text = "\n".join(current_batch).strip()
                        final_caption = f"{main_text}{base_footer}"
                    
                    # Check file size (Telegram Bot API limit is 50MB for sendVideo unless local API is used)
                    file_size = video_path.stat().st_size
                    is_large = file_size > 49 * 1024 * 1024 # 49MB safety margin
                    # 📐 Extract Post-Processing Metadata
                    meta = await get_video_metadata(video_path)
                    width = meta.get("width") if meta else None
                    height = meta.get("height") if meta else None
                    duration = int(meta.get("duration", 0)) if meta else None
                    
                    thumbnail_path = await generate_thumbnail(video_path)
                    
                    try:
                        is_large = file_size > 48 * 1024 * 1024 # Buffer
                        if is_large:
                            logger.warning(f"⚠️ File is large ({file_size / (1024*1024):.1f}MB). Sending as document.")
                            msg_vid = await context.bot.send_document(
                                chat_id=update.effective_chat.id,
                                document=open(video_path, "rb"),
                                caption=final_caption,
                                thumbnail=open(thumbnail_path, "rb") if thumbnail_path and thumbnail_path.exists() else None,
                                reply_to_message_id=update.message.message_id
                            )
                        else:
                            msg_vid = await context.bot.send_video(
                                chat_id=update.effective_chat.id,
                                video=open(video_path, "rb"),
                                caption=final_caption,
                                width=width,
                                height=height,
                                duration=duration,
                                thumbnail=open(thumbnail_path, "rb") if thumbnail_path and thumbnail_path.exists() else None,
                                supports_streaming=True,
                                reply_to_message_id=update.message.message_id
                            )
                        
                        # Cleanup thumbnail
                        if thumbnail_path and thumbnail_path.exists():
                            thumbnail_path.unlink()
                            
                    except Exception as e:
                         logger.error(f"❌ Failed to send video/document: {e}")
                         if thumbnail_path and thumbnail_path.exists():
                             thumbnail_path.unlink()
                         raise e
                    
                    # Send extra caption part if needed
                    if extra_text and msg_vid:
                        # Split again if extra_text is > 4096 (Telegram message limit)
                        chunk_size = 4000
                        for j in range(0, len(extra_text), chunk_size):
                             await context.bot.send_message(
                                chat_id=msg.chat.id,
                                text=extra_text[j:j+chunk_size],
                                reply_to_message_id=msg_vid.message_id
                            )
                    
                    logger.info(f"✅ Batch item {i+1} sent successfully.")
                    
                    # Clean up
                    video_path.unlink()
                    thumb = video_path.with_suffix(".jpg")
                    if thumb.exists(): thumb.unlink()
                else:
                    logger.error(f"❌ Batch item {i+1} download returned no file: {video_url}")
                    await context.bot.send_message(
                        chat_id=msg.chat.id,
                        text=f"❌ دانلود ویدیو شماره {i+1} ناموفق بود: {video_url}",
                        disable_web_page_preview=True
                    )
                    
            except Exception as inner_e:
                logger.error(f"❌ Batch Item Error ({video_url}): {inner_e}")
                await context.bot.send_message(
                        chat_id=msg.chat.id,
                        text=f"❌ خطا در دانلود ویدیو {i+1}: {str(inner_e)}",
                        disable_web_page_preview=True
                )
                continue
        
        await status_msg.edit_text("✨ دانلود دسته‌ای با موفقیت تمام شد!")
        
    except Exception as e:
        logger.error(f"Insta Batch Error: {e}")
        await status_msg.edit_text("❌ خطا در فرآیند دانلود دسته‌ای.")


async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, reply_to_id: int):
    """Reusable download logic for any supported platform (Instagram, YouTube, Aparat, ...)"""
    msg = update.message
    user_id = update.effective_user.id
    platform = detect_platform(url)
    platform_label = {"instagram": "Instagram", "youtube": "YouTube", "aparat": "Aparat"}.get(platform, "video")
    logger.info(f"📥 handle_video_link: platform={platform_label} url={url[:60]}")

    status_msg = await msg.reply_text(get_msg("downloading", user_id), reply_to_message_id=reply_to_id)

    video_path = None
    try:
        video_path = await download_video(url)

        if not video_path or not video_path.exists():
            await status_msg.edit_text(get_msg("err_dl", user_id))
            return

        await compress_video(video_path)

        caption = f"📥 {platform_label} | @Su6i_Yar_Bot"
        await send_video_file(context.bot, msg.chat.id, video_path, caption=caption, reply_to=reply_to_id)
        await safe_delete(status_msg)

    except Exception as e:
        logger.error(f"{platform_label} DL Error: {e}")
        await status_msg.edit_text(get_msg("err_dl", user_id))
    finally:
        if video_path and video_path.exists():
            video_path.unlink()
            thumb = video_path.with_suffix(".jpg")
            if thumb.exists(): thumb.unlink()


async def handle_instagram_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, reply_to_id: int):
    """Backward-compat alias → delegates to handle_video_link."""
    await handle_video_link(update, context, url, reply_to_id)

async def send_video_file(bot, chat_id, file_path, caption, reply_to=None):
    """Helper to send video with thumbnail"""
    thumb_path = await generate_thumbnail(file_path)
    meta = await get_video_metadata(file_path)
    
    width = meta.get("width") if meta else None
    height = meta.get("height") if meta else None
    duration = meta.get("duration") if meta else None
    
    with open(file_path, "rb") as video_file:
        if thumb_path:
            with open(thumb_path, "rb") as thumb_file:
                 await bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    caption=caption,
                    thumbnail=thumb_file,
                    width=width,
                    height=height,
                    duration=int(duration) if duration else None,
                    reply_to_message_id=reply_to
                )
        else:
            await bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=caption,
                width=width,
                height=height,
                duration=int(duration) if duration else None,
                reply_to_message_id=reply_to
            )

import os
import json
import httpx
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

from src.core.config import STORAGE_DIR, TEMP_DIR
logger = logging.getLogger(__name__)

async def get_video_metadata(file_path: Union[Path, str]) -> dict:
    """Extract width, height, duration from video file using ffprobe."""
    if str(file_path).startswith("http"):
        logger.debug(f"⚠️ get_video_metadata called with URL: {file_path}. Skipping ffprobe.")
        return None
        
    try:
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-select_streams", "v:0", 
            "-show_entries", "stream=width,height,duration,component_name,pix_fmt,codec_name", 
            "-of", "json", 
            str(file_path)
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"❌ ffprobe failed: {stderr.decode()}")
            return None
            
        data = json.loads(stdout)
        if "streams" in data and len(data["streams"]) > 0:
            stream = data["streams"][0]
            return {
                "width": int(stream.get("width", 0)),
                "height": int(stream.get("height", 0)),
                "duration": float(stream.get("duration", 0)),
                "pix_fmt": stream.get("pix_fmt", ""),
                "codec_name": stream.get("codec_name", "")
            }
        return None
    except Exception as e:
        logger.error(f"💥 Metadata Extraction Failed: {e}")
        return None

async def compress_video(input_path: Path) -> bool:
    """
    Smart Compression Logic:
    1. If Size > 10MB AND Resolution > 720p: Compress (Scale to 720p + Re-encode).
    2. Else: Remux only (Copy Codec) to fix Mac compatibility without reducing quality/size.
    """
    output_path = input_path.with_name(f"compressed_{input_path.name}")
    
    # 1. Check File Size
    try:
        input_size_mb = input_path.stat().st_size / (1024 * 1024)
    except FileNotFoundError:
        return False
    
    # 2. Check Resolution
    meta = await get_video_metadata(input_path)
    should_compress = False
    
    if not meta:
        logger.warning(f"⚠️ Could not read metadata for {input_path.name}, defaulting to Remux.")
    else:
        width = meta.get("width", 0)
        height = meta.get("height", 0)
        pix_fmt = meta.get("pix_fmt", "")
        codec = meta.get("codec_name", "")
        min_dim = min(width, height)
        
        # Condition 1: High Res/Size -> Compress
        high_res_huge = (input_size_mb > 10) and (min_dim > 720)
        
        # Condition 2: Incompatible Format/Codec (Apple/Telegram needs h264 + yuv420p)
        is_bad_pix = pix_fmt not in ["yuv420p"] 
        is_bad_codec = codec != "h264"
        
        should_compress = high_res_huge or is_bad_pix or is_bad_codec

    if should_compress:
        current_reason = "High Res/Size" if meta and high_res_huge else "Format Fix"
        logger.info(f"📉 Processing {input_path.name} Reason: {current_reason}...")
        
        # 🧪 Two-Pass Strategy:
        # Pass 1: Keep quality, just fix format and maybe lower CRF if near limit
        crf = "24"
        if input_size_mb > 45:
            crf = "28" # More aggressive to fit 50MB
            
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-c:v", "libx264", "-crf", crf, "-preset", "faster",
            "-vf", "format=yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output_path)
        ]
    else:
        logger.info(f"⚡️ Remuxing {input_path.name} (Size: {input_size_mb:.1f}MB)...")
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-c", "copy", "-movflags", "+faststart",
            str(output_path)
        ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, stderr = await process.communicate()
        
        if process.returncode == 0 and output_path.exists():
            final_size = output_path.stat().st_size / (1024*1024)
            
            # 🛡️ Emergency Second Pass: If still > 49MB, force scale down
            if final_size > 49:
                logger.warning(f"☢️ File still too large ({final_size:.1f}MB). Applying Emergency Scaling...")
                emergency_path = output_path.with_name(f"emergency_{output_path.name}")
                
                # Scale to 720p (at most) and use very aggressive CRF
                emergency_cmd = [
                    "ffmpeg", "-y", "-i", str(output_path),
                    "-vf", "scale='if(gt(iw,ih),-2,720)':'if(gt(iw,ih),720,-2)',format=yuv420p",
                    "-c:v", "libx264", "-crf", "32", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "96k",
                    str(emergency_path)
                ]
                
                eproc = await asyncio.create_subprocess_exec(*emergency_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                await eproc.communicate()
                
                if emergency_path.exists():
                    output_path.unlink()
                    emergency_path.rename(output_path)
                    final_size = output_path.stat().st_size / (1024*1024)
            
            logger.info(f"✅ Process successful: {input_size_mb:.1f}MB -> {final_size:.1f}MB")
            input_path.unlink()
            output_path.rename(input_path)
            return True
        else:
            logger.error(f"❌ ffmpeg failed: {stderr.decode()[:200]}")
            if output_path.exists(): output_path.unlink()
            return False
    except Exception as e:
        logger.error(f"💥 ffmpeg Exception: {e}")
        if output_path.exists(): output_path.unlink()
        return False

async def generate_thumbnail(video_path: Path) -> Optional[Path]:
    """Generate a JPG thumbnail from video at t=1s."""
    thumb_path = video_path.with_suffix(".jpg")
    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-ss", "00:00:01", "-vframes", "1", "-q:v", "5",
            str(thumb_path)
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        await process.communicate()
        if thumb_path.exists():
            return thumb_path
        return None
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        return None

async def download_instagram_cobalt(url: str, filename: Path) -> bool:
    """Download video using Cobalt API as fallback"""
    logger.info("🛡️ Falling back to Cobalt API...")
    instances = [
        "https://coapi.kelig.me/api/json", "https://cobalt.meowing.de",
        "https://cobalt.pub", "https://api.cobalt.kwiatekmiki.pl",
        "https://cobalt.hyperr.net", "https://cobalt.kuba2k2.com"
    ]
    
    headers = {
        "Accept": "application/json", "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://cobalt.tools", "Referer": "https://cobalt.tools/"
    }

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for base_url in instances:
            base = base_url.rstrip("/")
            api_url = base if base.endswith("/api/json") else base 
            
            logger.info(f"🛡️ Trying Cobalt: {api_url}")
            payloads = [
                {"url": url, "videoQuality": "max", "audioFormat": "mp3", "filenameStyle": "basic"}, # v10
                {"url": url, "vCodec": "h264", "vQuality": "max", "aFormat": "mp3", "filenamePattern": "basic"} # v7
            ]

            dl_url = None
            for p in payloads:
                try:
                    resp = await client.post(api_url, json=p, headers=headers)
                    if resp.status_code not in [200, 201]: continue
                    data = resp.json()
                    if data.get("status") in ["error", "redirect"]: continue
                    
                    dl_url = data.get("url") or (data.get("picker")[0]["url"] if data.get("picker") else None)
                    if dl_url: break
                except Exception: continue

            if dl_url:
                try:
                    async with client.stream("GET", dl_url) as dl_resp:
                        dl_resp.raise_for_status()
                        with open(filename, "wb") as f:
                            async for chunk in dl_resp.aiter_bytes(): f.write(chunk)
                    return True
                except Exception: continue

    logger.error("❌ All Cobalt instances failed.")
    return False

def convert_cookies_json_to_netscape(json_path: Path, txt_path: Path):
    """Convert Chrome-style JSON cookies to Netscape format for yt-dlp."""
    try:
        import json
        cookies = json.loads(json_path.read_text())
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# This file is generated by Su6i Yar. Do not edit.\n\n")
            for c in cookies:
                domain = c.get("domain", "")
                # Netscape format: domain, flag, path, secure, expiration, name, value
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = c.get("path", "/")
                secure = "TRUE" if c.get("secure") else "FALSE"
                # expirationDate is usually a float timestamp
                expires = int(c.get("expirationDate", 0))
                name = c.get("name", "")
                value = c.get("value", "")
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
        logger.info(f"💾 Converted {json_path.name} to {txt_path.name}")
    except Exception as e:
        logger.error(f"❌ Cookie conversion failed: {e}")

SUPPORTED_DOMAINS = {
    "instagram.com": "instagram",
    "youtu.be":       "youtube",
    "youtube.com":    "youtube",
    "aparat.com":     "aparat",
}

def detect_platform(url: str) -> str:
    """Return platform key ('instagram', 'youtube', 'aparat') or 'unknown'."""
    for domain, platform in SUPPORTED_DOMAINS.items():
        if domain in url:
            return platform
    return "unknown"

async def download_video(url: str) -> Optional[Path]:
    """Generic video download via yt-dlp with multi-stage fallback (Anonymous -> Cookies -> Cobalt).
    Supports Instagram, YouTube, Aparat and any other yt-dlp-supported site."""
    platform = detect_platform(url)
    logger.info(f"📥 download_video: platform={platform} url={url[:60]}")

    # Strip query params only for Instagram (YouTube needs ?v=...)
    if platform == "instagram" and "?" in url:
        url = url.split("?")[0]

    timestamp = int(asyncio.get_event_loop().time())
    filename = Path(TEMP_DIR) / f"video_{timestamp}.mp4"

    # 1. Setup yt-dlp
    import sys
    import shutil
    venv_bin = Path(sys.executable).parent
    yt_dlp_path = venv_bin / "yt-dlp"
    executable = str(yt_dlp_path) if yt_dlp_path.exists() else "yt-dlp"

    # 2. Handle Cookies — check project root first, then STORAGE_DIR
    json_cookies = Path(STORAGE_DIR) / "cookies.json"
    netscape_cookies = Path(STORAGE_DIR) / "cookies.txt"
    # Also check project root cookies.txt (deployed manually on server)
    project_root_cookies = Path(__file__).parent.parent.parent.parent / "cookies.txt"
    if project_root_cookies.exists() and not netscape_cookies.exists():
        netscape_cookies = project_root_cookies
    if json_cookies.exists():
        convert_cookies_json_to_netscape(json_cookies, netscape_cookies)

    # 3. JS runtime detection (needed for YouTube n-challenge via deno/node)
    node_bin = shutil.which("node") or shutil.which("nodejs") or "/usr/bin/node" or "/usr/local/bin/node"
    if not Path(node_bin).exists():
        node_bin = None
        # Try playwright bundled node
        playwright_node = venv_bin.parent / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages" / "playwright" / "driver" / "node"
        if playwright_node.exists():
            node_bin = str(playwright_node)
            
    deno_bin = None
    if not node_bin:
        deno_paths = [
            shutil.which("deno"),
            str(Path.home() / ".deno" / "bin" / "deno"),
            "/home/su6i/.deno/bin/deno",
            "/usr/bin/deno",
            "/usr/local/bin/deno"
        ]
        for p in deno_paths:
            if p and Path(p).exists():
                deno_bin = p
                break
    if node_bin:
        js_runtime_args = ["--js-runtimes", f"node:{node_bin}"]
    elif deno_bin:
        js_runtime_args = ["--js-runtimes", f"deno:{deno_bin}"]
    else:
        js_runtime_args = []

    # 4. YouTube-specific args (remote EJS solver for n-challenge)
    yt_extra_args = []
    if platform == "youtube":
        yt_extra_args = ["--remote-components", "ejs:github"] + js_runtime_args

    # Prepare base command
    cmd_base = [
        executable,
        "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", str(filename),
        "--write-info-json", "--no-playlist",
    ] + yt_extra_args + [url]

    # --- ATTEMPT STRATEGIES ---

    # Attempt 1: Explicit Cookies File (Priority)
    if netscape_cookies.exists():
        cmd_cookies = list(cmd_base)
        cmd_cookies.insert(1, str(netscape_cookies))
        cmd_cookies.insert(1, "--cookies")
        logger.info(f"📥 Attempt 1: yt-dlp with explicit cookies.txt...")
        proc = await asyncio.create_subprocess_exec(*cmd_cookies, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout1, stderr1 = await proc.communicate()
        if filename.exists(): return filename
        logger.warning(f"⚠️ Attempt 1 failed. stderr: {stderr1.decode()[-800:]}")

    # Attempt 2: Extract Cookies from Browsers (Fallback for YouTube Sign-in)
    for browser in ["brave", "chrome", "safari"]:
        cmd_browser = list(cmd_base)
        cmd_browser.insert(1, browser)
        cmd_browser.insert(1, "--cookies-from-browser")
        logger.info(f"📥 Attempt 2 ({browser}): yt-dlp extracting cookies from {browser}...")
        proc = await asyncio.create_subprocess_exec(*cmd_browser, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout2, stderr2 = await proc.communicate()
        if filename.exists(): return filename
        err_out = stderr2.decode()
        if "Could not find Chrome" not in err_out and "Keychain" not in err_out:
             logger.warning(f"⚠️ Attempt 2 ({browser}) failed. stderr: {err_out[-400:]}")

    # Attempt 3: Anonymous
    logger.info(f"📥 Attempt 3: yt-dlp anonymous...")
    proc = await asyncio.create_subprocess_exec(*cmd_base, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if filename.exists(): return filename
    logger.error(f"❌ yt-dlp attempt 3 (anonymous) failed. stderr: {stderr.decode()[-800:]}")

    # Attempt 3: Cobalt fallback (works for Instagram, YouTube, and many others)
    if await download_instagram_cobalt(url, filename):
        return filename

    return None


async def download_instagram(url: str) -> Optional[Path]:
    """Backward-compat alias → delegates to download_video."""
    return await download_video(url)

async def download_instagram_batch(url: str, count: int, title_filter: str = None, reverse_order: bool = False) -> list[str]:
    """Helper to get list of Instagram reel URLs from a profile/hashtag."""
    logger.info(f"📂 Extracting batch from: {url} (Limit: {count}, Filter: {title_filter})")
    
    # Clean username from URL
    username = url.rstrip("/").split("/")[-1]
    if "?" in username: username = username.split("?")[0]
    
    # Try different URL variations
    test_urls = [
        f"https://www.instagram.com/{username}/",
        f"instagram:user:{username}"
    ]

    # Strategy 1: Playwright (God-Tier) - Most reliable for "viewing" public profiles
    logger.info(f"🕵️ Attempting Playwright Scraper first for {username}...")
    try:
        urls = await scrape_instagram_reels_playwright(username, count, reverse_order=reverse_order)
        if urls:
            logger.info(f"✅ Playwright found {len(urls)} videos.")
            return urls
    except Exception as e:
        logger.error(f"❌ Playwright attempt failed: {e}")
        # Auto-healing for missing browsers
        if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
             logger.warning("🛠️ Playwright browsers missing. Attempting auto-install...")
             import subprocess
             import sys
             try:
                 subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium", "chromium-headless-shell"])
                 logger.info("✅ Playwright browsers installed! Retrying...")
                 return await scrape_instagram_reels_playwright(username, count)
             except Exception as install_error:
                 logger.error(f"❌ Auto-install failed: {install_error}")

    # Strategy 2: Instaloader (Fallback)
    logger.warning("⚠️ Playwright failed. Falling back to Instaloader...")
    try:
        try:
            import instaloader
        except ImportError:
            logger.warning("📦 Instaloader not found. Attempting auto-install...")
            import subprocess
            import sys
            try:
                # Try standard pip first
                subprocess.check_call([sys.executable, "-m", "pip", "install", "instaloader"])
            except subprocess.CalledProcessError:
                # Fallback to uv if pip is missing/fails
                logger.info("⚡ pip failed, trying uv...")
                subprocess.check_call(["uv", "pip", "install", "instaloader"])
            
            import instaloader
            logger.info("✅ Instaloader installed successfully!")

        # Initialize Instaloader
        L = instaloader.Instaloader()
        
        # Get profile
        profile = instaloader.Profile.from_username(L.context, username)
        
        urls = []
        posts = profile.get_posts()
        
        for post in posts:
            if post.is_video:
                url = f"https://www.instagram.com/p/{post.shortcode}/"
                urls.append(url)
                if len(urls) >= count:
                    break
        
        if urls:
            logger.info(f"✅ Instaloader found {len(urls)} videos.")
            return urls
            
    except ImportError:
        logger.error("❌ Instaloader not installed/installable.")
    except Exception as e:
        logger.error(f"❌ Instaloader failed: {e}")

    logger.error("❌ All extraction strategies failed (Playwright & Instaloader).")
    return []


async def scrape_instagram_reels_playwright(username: str, count: int, reverse_order: bool = False) -> list[str]:
    """Fallback scraper using Playwright to bypass yt-dlp extraction blocks."""
    from playwright.async_api import async_playwright
    
    url = f"https://www.instagram.com/{username}/reels/"
    logger.info(f"🌐 Playwright: Opening {url}")
    
    async with async_playwright() as p:
        # Use a real browser context
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        
        # 🍪 Load Cookies if available (God Mode)
        # Use standardized storage for cookies
        cookie_file = Path(STORAGE_DIR) / "cookies.json"
        if cookie_file.exists():
            try:
                import json
                cookies = json.loads(cookie_file.read_text())
                valid_cookies = []
                for c in cookies:
                    # Adapt fields for Playwright
                    if "expirationDate" in c:
                        c["expires"] = c.pop("expirationDate")
                    if "sameSite" in c:
                        if c["sameSite"] == "no_restriction":
                            c["sameSite"] = "None"
                        elif c["sameSite"] == "unspecified":
                            del c["sameSite"]
                        else:
                             # Playwright expects Title Case (Lax, Strict) but Chrome exports lowercase
                             c["sameSite"] = c["sameSite"].title()
                    
                    # Remove unknown fields
                    c.pop("hostOnly", None)
                    c.pop("session", None)
                    c.pop("storeId", None)
                    c.pop("id", None)
                    
                    valid_cookies.append(c)
                
                await context.add_cookies(valid_cookies)
                logger.info("🍪 Loaded cookies from cookies.json")
            except Exception as e:
                logger.error(f"⚠️ Failed to load cookies: {e}")

        page = await context.new_page()
        
        try:
            # wait_until="networkidle" can hang on Instagram due to tracking requests. Use "domcontentloaded".
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Check for immediate redirect to login
            if "/accounts/login/" in page.url:
                 logger.warning(f"🔐 Redirected to Login Page: {page.url}")
                 # Maybe we can still scrape? Often not without cookies.
                 # Let's wait a bit longer just in case content loads dynamically
            
            # Wait for some reels to appear (30s timeout)
            try:
                await page.wait_for_selector("a[href*='/reel/']", timeout=30000)
            except Exception:
                 logger.warning("⏱️ Timeout waiting for reels. Checking page structure...")
                 # Fallback: maybe we are on main profile? Check general posts
                 if await page.query_selector("a[href*='/p/']"):
                     logger.info("Found general posts, looking for videos there...")
                 else:
                     logger.error("❌ Standard selectors failed. Saving debug dump...")
                     try:
                         # import datetime is missing, adding it here
                         timestamp = int(datetime.now().timestamp())
                         # Save debug dumps to standardized temp folder
                         debug_file = Path(TEMP_DIR) / f"debug_insta_{timestamp}.html"
                         content = await page.content()
                         debug_file.write_text(content, encoding="utf-8")
                         logger.info(f"💾 Saved debug dump to {debug_file}")
                     except Exception as dump_err:
                         logger.error(f"Failed to save debug dump: {dump_err}")
                     raise # Re-raise to trigger failure log
            
            
            # Scroll and Extract Loop
            ordered_hrefs = []
            unique_hrefs = set()
            no_new_content_count = 0
            
            import time
            while len(ordered_hrefs) < count:
                # Extract current hrefs
                hrefs = await page.eval_on_selector_all(
                    "a[href*='/reel/']", 
                    "elements => elements.map(el => el.href)"
                )
                
                new_items = 0
                for h in hrefs:
                    if h not in unique_hrefs:
                         unique_hrefs.add(h)
                         ordered_hrefs.append(h)
                         new_items += 1
                
                logger.info(f"📜 Scrolled... Found {len(ordered_hrefs)}/{count} videos so far.")
                
                if len(ordered_hrefs) >= count:
                    break
                
                if new_items == 0:
                    no_new_content_count += 1
                    if no_new_content_count >= 5: # Be more patient
                        logger.warning("🛑 No new videos found after scrolling. Stopping.")
                        break
                else:
                    no_new_content_count = 0
                
                # Scroll down
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2500) # Wait for load
            
            # Order Fix: 
            # If reverse_order is True (for "last N"), keep Newest first.
            # Otherwise (for "all"/series), reverse to Oldest first.
            if not reverse_order:
                ordered_hrefs.reverse() 
            
            final_urls = []
            for h in ordered_hrefs[:count]:
                vid_id = h.rstrip("/").split("/")[-1]
                final_urls.append(f"https://www.instagram.com/reels/{vid_id}/")
                
            return final_urls
            
            
        except Exception as e:
            logger.error(f"❌ Playwright Error: {e}")
            return []
        finally:
            await browser.close()

import asyncio
import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.features.downloader.utils import download_instagram_cobalt
from src.core.logger import setup_logger
import logging

setup_logger()

async def main():
    url = "https://youtube.com/shorts/LrQ7NM7dAjQ"
    print(f"Testing Cobalt with({url})...")
    path = Path("cobalt_test.mp4")
    success = await download_instagram_cobalt(url, path)
    if success and path.exists():
        print(f"SUCCESS: {path}, size: {path.stat().st_size} bytes")
        path.unlink()
    else:
        print("FAILED to download via Cobalt!")

asyncio.run(main())

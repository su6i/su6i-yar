import asyncio

# Global State
LEARN_WAITERS = []
LEARN_LOCK = asyncio.Lock()
SEARCH_FILE_ID = None
SEARCH_GIF_FALLBACK = "CgACAgQAAxkBAAIBZGX9..." # Placeholder, need real ID or URL if available

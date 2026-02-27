from src.features.learning.state import LEARN_WAITERS
from src.utils.text_tools import get_msg
from src.utils.telegram import safe_delete

async def refresh_learn_queue():
    """Update waiting users with their position in queue"""
    for index, waiter in enumerate(LEARN_WAITERS):
        if index == 0: continue # Currently processing
        
        user_id = waiter["user_id"]
        status_msg = waiter["status_msg"]
        
        # Calculate Position (1-based, excluding current)
        pos = index
        notification = get_msg("learn_designing", user_id) + get_msg("learn_queue_pos", user_id).format(pos=pos)
        
        if status_msg.caption != notification:
            try:
                await status_msg.edit_caption(caption=notification)
            except Exception:
                pass

import aiosqlite
import json
from utils.db import DB_PATH
from utils.logger import logger

async def track(user_id: int, event_type: str, data: dict = None):
    """
    Lightweight event tracker.
    Example event_type: 'bot_start', 'menu_action', 'trial_exhausted'
    """
    try:
        event_data = json.dumps(data) if data else None
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO analytics_events (user_id, event_type, event_data)
                VALUES (?, ?, ?)
            """, (user_id, event_type, event_data))
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to track event {event_type} for user {user_id}: {e}")

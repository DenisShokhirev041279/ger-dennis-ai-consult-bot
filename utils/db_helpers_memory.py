import aiosqlite
import time
from utils.db import DB_PATH
from utils.logger import logger

async def save_message(user_id: int, session_id: str, role: str, content: str, tokens: int = 0):
    """Save a message to the conversation history."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO conversation_history (user_id, session_id, role, content, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, session_id, role, content, tokens))
        await db.commit()

async def get_conversation_history(user_id: int, session_id: str, limit: int = 20):
    """Get the last N messages for the given session."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT role, content FROM conversation_history
            WHERE user_id = ? AND session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (user_id, session_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [{"role": row[0], "content": row[1]} for row in rows]

async def clear_session_history(user_id: int, session_id: str):
    """Delete conversation history for a specific session."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM conversation_history
            WHERE user_id = ? AND session_id = ?
        """, (user_id, session_id))
        await db.commit()

async def get_current_session_id(user_id: int) -> str:
    """
    Get or create a simple session ID. 
    For now, we can use a timestamp of the start of the current day or 
    a more complex ID if sessions have explicit lifetimes.
    """
    # Simple implementation: use current date as session ID if no session management is active.
    # But the bot has a 'sessions' table. Let's use the start_time from there.
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT start_time FROM sessions WHERE user_id = ? AND is_active = 1", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return str(row[0])
            return "trial_" + time.strftime("%Y-%m-%d")

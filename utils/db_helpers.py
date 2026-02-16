import aiosqlite
import time
from utils.db import DB_PATH
from utils.logger import logger

async def create_payment_claim(user_id: int, package_key: str, payment_method: str) -> int:
    """Create a new payment claim and return claim_id"""
    created_at = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO payment_claims (user_id, package_key, payment_method, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (user_id, package_key, payment_method, created_at))
        await db.commit()
        return cursor.lastrowid

async def get_payment_claim(claim_id: int):
    """Get payment claim by claim_id"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT claim_id, user_id, package_key, payment_method, status, created_at, admin_note
            FROM payment_claims WHERE claim_id = ?
        """, (claim_id,)) as cursor:
            return await cursor.fetchone()

async def approve_payment_claim(claim_id: int, admin_note: str = ""):
    """Approve a payment claim"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE payment_claims 
            SET status = 'approved', admin_note = ?
            WHERE claim_id = ?
        """, (admin_note, claim_id))
        await db.commit()

async def reject_payment_claim(claim_id: int, admin_note: str = ""):
    """Reject a payment claim"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE payment_claims 
            SET status = 'rejected', admin_note = ?
            WHERE claim_id = ?
        """, (admin_note, claim_id))
        await db.commit()

async def get_trial_usage_today(user_id: int):
    """Get trial usage for user today"""
    today = time.strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT message_count, photo_count 
            FROM trial_usage 
            WHERE user_id = ? AND date = ?
        """, (user_id, today)) as cursor:
            row = await cursor.fetchone()
            return row if row else (0, 0)

async def increment_trial_messages(user_id: int):
    """Increment trial message count for user today"""
    today = time.strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO trial_usage (user_id, date, message_count, photo_count)
            VALUES (?, ?, 1, 0)
            ON CONFLICT(user_id, date) DO UPDATE SET
                message_count = message_count + 1
        """, (user_id, today))
        await db.commit()

async def increment_trial_photos(user_id: int):
    """Increment trial photo count for user today"""
    today = time.strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO trial_usage (user_id, date, message_count, photo_count)
            VALUES (?, ?, 0, 1)
            ON CONFLICT(user_id, date) DO UPDATE SET
                photo_count = photo_count + 1
        """, (user_id, today))
        await db.commit()

async def count_active_sessions() -> int:
    """Count currently active sessions"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

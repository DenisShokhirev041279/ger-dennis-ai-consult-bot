import aiosqlite
from utils.db import DB_PATH
from utils.logger import logger

async def add_referral(referrer_id: int, referred_id: int):
    """Register a new referral."""
    if referrer_id == referred_id:
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO referrals (referrer_id, referred_id)
                VALUES (?, ?)
            """, (referrer_id, referred_id))
            await db.commit()
            
            # Grant Bonus
            from utils.db_helpers import update_bonus_credits
            await update_bonus_credits(referrer_id, 1)
            
            logger.info(f"Referral registered: {referrer_id} -> {referred_id}. Bonus granted.")
        except aiosqlite.IntegrityError:
            # User already referred or registered
            pass

async def get_referrer(referred_id: int):
    """Get the ID of the person who referred this user."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT referrer_id FROM referrals WHERE referred_id = ?", (referred_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def is_bonus_granted(referred_id: int) -> bool:
    """Check if bonus for this referral was already granted."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT bonus_granted FROM referrals WHERE referred_id = ?", (referred_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else False

async def mark_bonus_granted(referred_id: int):
    """Mark bonus as granted for this referral."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE referrals SET bonus_granted = 1 WHERE referred_id = ?", (referred_id,))
        await db.commit()

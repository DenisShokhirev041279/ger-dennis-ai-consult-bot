import aiosqlite
from utils.db import DB_PATH
from utils.logger import logger

async def add_referral(referrer_id: int, referred_id: int):
    """Register a new referral. Bonus is NOT granted here — only after referred user pays."""
    if referrer_id == referred_id:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO referrals (referrer_id, referred_id)
                VALUES (?, ?)
            """, (referrer_id, referred_id))
            await db.commit()
            logger.info(f"Referral registered: {referrer_id} -> {referred_id}. Bonus pending payment.")
        except aiosqlite.IntegrityError:
            pass


async def grant_referral_bonus_on_payment(referred_id: int, bot=None):
    """Call this when referred user makes first payment. Grants bonus to referrer."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT referrer_id, bonus_granted FROM referrals WHERE referred_id = ?
        """, (referred_id,)) as cursor:
            row = await cursor.fetchone()

        if not row or row[1]:  # No referral or bonus already granted
            return

        referrer_id = row[0]

        # Mark bonus as granted + update referred_subscribed flag
        await db.execute("""
            UPDATE referrals SET bonus_granted = 1, referred_subscribed = 1
            WHERE referred_id = ?
        """, (referred_id,))
        await db.commit()

    # Grant bonus credit to referrer
    from utils.db_helpers import update_bonus_credits
    await update_bonus_credits(referrer_id, 10)  # 10 bonus messages for successful referral
    logger.info(f"Referral bonus granted to {referrer_id} after {referred_id} paid.")

    # Notify referrer if bot instance provided
    if bot:
        try:
            await bot.send_message(
                referrer_id,
                "🎉 Your referral just subscribed! You got +10 bonus messages."
            )
        except Exception:
            pass

async def get_referral_stats(referrer_id: int) -> dict:
    """Get referral stats for a user: total invited, how many paid, bonus earned."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*), SUM(referred_subscribed), SUM(bonus_granted)
            FROM referrals WHERE referrer_id = ?
        """, (referrer_id,)) as cursor:
            row = await cursor.fetchone()
    total = row[0] or 0
    paid = row[1] or 0
    bonuses_granted = row[2] or 0
    return {"total": total, "paid": paid, "bonuses_granted": bonuses_granted}

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

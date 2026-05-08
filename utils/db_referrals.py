import aiosqlite
from utils.db import DB_PATH
from utils.logger import logger
from utils.config import REFERRAL_ACTIVATION_BONUS_MESSAGES, REFERRAL_PAYMENT_BONUS_MESSAGES

async def add_referral(referrer_id: int, referred_id: int):
    """Register a new referral and grant a small activation bonus once."""
    if referrer_id == referred_id:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cursor = await db.execute("""
                INSERT OR IGNORE INTO referrals (referrer_id, referred_id, activation_bonus_granted)
                VALUES (?, ?, 0)
            """, (referrer_id, referred_id))
            inserted = cursor.rowcount > 0
            if inserted and REFERRAL_ACTIVATION_BONUS_MESSAGES > 0:
                await db.execute("""
                    UPDATE users SET bonus_credits = COALESCE(bonus_credits, 0) + ?
                    WHERE user_id = ?
                """, (REFERRAL_ACTIVATION_BONUS_MESSAGES, referrer_id))
                await db.execute("""
                    UPDATE referrals SET activation_bonus_granted = 1
                    WHERE referred_id = ?
                """, (referred_id,))
            await db.commit()
            if inserted:
                logger.info(
                    f"Referral registered: {referrer_id} -> {referred_id}. "
                    f"Activation bonus +{REFERRAL_ACTIVATION_BONUS_MESSAGES}; payment bonus pending."
                )
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
    await update_bonus_credits(referrer_id, REFERRAL_PAYMENT_BONUS_MESSAGES)
    logger.info(f"Referral bonus granted to {referrer_id} after {referred_id} paid.")

    # Notify referrer if bot instance provided
    if bot:
        try:
            await bot.send_message(
                referrer_id,
                f"🎉 Your referral just subscribed! You got +{REFERRAL_PAYMENT_BONUS_MESSAGES} bonus messages."
            )
        except Exception:
            pass

async def get_referral_stats(referrer_id: int) -> dict:
    """Get referral stats for a user: total invited, how many paid, bonus earned."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*), SUM(referred_subscribed), SUM(bonus_granted), SUM(activation_bonus_granted)
            FROM referrals WHERE referrer_id = ?
        """, (referrer_id,)) as cursor:
            row = await cursor.fetchone()
    total = row[0] or 0
    paid = row[1] or 0
    bonuses_granted = row[2] or 0
    activation_bonuses_granted = row[3] or 0
    return {
        "total": total,
        "paid": paid,
        "bonuses_granted": bonuses_granted,
        "activation_bonuses_granted": activation_bonuses_granted,
    }

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

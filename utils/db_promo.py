import aiosqlite
import time
from utils.db import DB_PATH
import secrets
import string

async def create_promo_code(creator_id: int, reward_type: str, reward_amount: int, max_uses: int = 1, days_valid: int = 30) -> str:
    """Generate a random promo code and store it in the database."""
    alphabet = string.ascii_uppercase + string.digits
    # Format: GIFT-XXXXXX
    code = "GIFT-" + "".join(secrets.choice(alphabet) for i in range(6))
    
    expires_at = None
    if days_valid > 0:
        expires_at = int(time.time()) + (days_valid * 86400)
        
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO promo_codes (code, creator_id, reward_type, reward_amount, max_uses, expires_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', ? || ' days'))
        """, (code, creator_id, reward_type, reward_amount, max_uses, days_valid if days_valid > 0 else 0))
        # Note: datetime('now', '+X days') is string format from SQLite. Our time might be int, 
        # let's use the current timestamp offset correctly
        await db.commit()
    return code

async def get_promo_stats():
    """Returns basic stats about promo codes"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*), SUM(times_used) FROM promo_codes") as cursor:
            row = await cursor.fetchone()
            return {"total": row[0] or 0, "used": row[1] or 0}

async def use_promo_code(user_id: int, code: str) -> dict:
    """Attempt to use a promo code, return result dict {"success": bool, "message": str, "reward": dict}"""
    code = code.strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT reward_type, reward_amount, max_uses, times_used, expires_at 
            FROM promo_codes WHERE code = ?
        """, (code,)) as cursor:
            promo = await cursor.fetchone()
            
        if not promo:
            return {"success": False, "message": "Промокод не найден."}
            
        reward_type, reward_amount, max_uses, times_used, expires_at_str = promo
        
        # Check uses
        if times_used >= max_uses:
            return {"success": False, "message": "Этот промокод больше не действителен."}
            
        # Check expiration (expires_at can be int or string)
        # Using simple checks since created via datetime('now', x days)
        # Let's verify string via sql
        async with db.execute("SELECT CASE WHEN ? IS NULL THEN 1 WHEN ? > CURRENT_TIMESTAMP THEN 1 ELSE 0 END", (expires_at_str, expires_at_str)) as cursor:
            is_valid = (await cursor.fetchone())[0]
            if not is_valid:
                return {"success": False, "message": "Срок действия промокода истёк."}
                
        # Check if already used
        async with db.execute("SELECT 1 FROM promo_code_uses WHERE code = ? AND user_id = ?", (code, user_id)) as cursor:
            if await cursor.fetchone():
                return {"success": False, "message": "Вы уже использовали этот промокод."}
                
        # Apply reward
        if reward_type == 'trial_messages':
            today = time.strftime("%Y-%m-%d")
            # We add a negative message count to trial_usage to essentially increase the limit
            # Or better, we can just edit their users.bonus_credits which is safer
            await db.execute("""
                UPDATE users SET bonus_credits = COALESCE(bonus_credits, 0) + ? WHERE user_id = ?
            """, (reward_amount, user_id))
            msg = f"Вам начислено {reward_amount} бонусных запросов!"
            
        elif reward_type == 'premium_days':
            from bot.config.plans import PLANS
            # Assign starter plan for N days
            duration_days = reward_amount
            daily_limit = PLANS["starter"]["daily_ai_limit"]
            # Mark existing active subs as expired
            await db.execute("UPDATE subscriptions SET status = 'expired' WHERE user_id = ? AND status = 'active'", (user_id,))
            await db.execute("""
                INSERT INTO subscriptions (user_id, plan, status, daily_limit, expires_at)
                VALUES (?, 'starter', 'active', ?, datetime('now', ? || ' days'))
            """, (user_id, daily_limit, duration_days))
            msg = f"Вам активирован тариф Starter на {reward_amount} дней!"
            
        # Mark used
        await db.execute("INSERT INTO promo_code_uses (code, user_id) VALUES (?, ?)", (code, user_id))
        await db.execute("UPDATE promo_codes SET times_used = times_used + 1 WHERE code = ?", (code,))
        
        await db.commit()
        return {"success": True, "message": msg}

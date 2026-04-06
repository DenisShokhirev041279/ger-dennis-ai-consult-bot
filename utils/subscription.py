import aiosqlite
import time
from utils.db import DB_PATH
from bot.config.plans import PLANS
from utils.logger import logger

async def check_subscription(user_id: int) -> dict:
    """
    Check active subscription for a user.
    Returns:
    {
        "has_subscription": bool,
        "plan": "starter" | "pro" | "business" | None,
        "daily_remaining": int,
        "features": ["basic_ai_consult", "advanced_cv", ...]
    }
    """
    result = {
        "has_subscription": False,
        "plan": None,
        "daily_remaining": 0,
        "features": [],
        "expires_at": None,
    }
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check active non-expired subscription
        async with db.execute("""
            SELECT id, plan, daily_limit, expires_at 
            FROM subscriptions 
            WHERE user_id = ? AND status = 'active' AND expires_at > CURRENT_TIMESTAMP
            ORDER BY expires_at DESC LIMIT 1
        """, (user_id,)) as cursor:
            active_sub = await cursor.fetchone()

        if active_sub:
            sub_id, plan_key, daily_limit, expires_at = active_sub
            
            # Check daily usage
            today = time.strftime("%Y-%m-%d")
            async with db.execute("SELECT message_count FROM trial_usage WHERE user_id = ? AND date = ?", (user_id, today)) as usage_cur:
                usage_row = await usage_cur.fetchone()
                used_today = usage_row[0] if usage_row else 0
            
            plan_details = PLANS.get(plan_key, PLANS["starter"])
            
            result["has_subscription"] = True
            result["plan"] = plan_key
            result["daily_remaining"] = max(0, plan_details["daily_ai_limit"] - used_today)
            result["features"] = plan_details["features"]
            result["expires_at"] = expires_at
        else:
            # Mark expired if needed
            await db.execute("""
                UPDATE subscriptions SET status = 'expired' 
                WHERE user_id = ? AND status = 'active' AND expires_at <= CURRENT_TIMESTAMP
            """, (user_id,))
            await db.commit()

    return result

async def activate_subscription(user_id: int, plan_key: str):
    """Activate or renew a subscription."""
    plan = PLANS.get(plan_key)
    if not plan:
        logger.error(f"Cannot activate unknown plan: {plan_key}")
        return
        
    duration_days = plan["duration_days"]
    daily_limit = plan["daily_ai_limit"]
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Mark existing active subs as expired (or we could extend them)
        await db.execute("UPDATE subscriptions SET status = 'expired' WHERE user_id = ? AND status = 'active'", (user_id,))
        
        await db.execute("""
            INSERT INTO subscriptions (user_id, plan, status, daily_limit, expires_at)
            VALUES (?, ?, 'active', ?, datetime('now', ? || ' days'))
        """, (user_id, plan_key, daily_limit, duration_days))
        await db.commit()
        logger.info(f"Activated subscription {plan_key} for user {user_id}")

    # Grant referral bonus to whoever invited this user (if not already granted)
    from utils.db_referrals import grant_referral_bonus_on_payment
    await grant_referral_bonus_on_payment(user_id)

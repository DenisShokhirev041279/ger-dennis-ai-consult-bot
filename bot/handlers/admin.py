from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import activate_session, get_user_lang
from utils.i18n import get_text
from utils.config import ADMIN_IDS
from utils.db_helpers import get_payment_claim, approve_payment_claim, reject_payment_claim
from utils.logger import logger

router = Router()

from bot.config.packages import PACKAGES

@router.callback_query(F.data.startswith("approve_"))
async def admin_approve_claim(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return
    
    # Data: approve_{claim_id}
    claim_id = int(callback.data.split("_")[1])
    
    # Get claim details
    claim = await get_payment_claim(claim_id)
    if not claim:
        await callback.answer("Claim not found", show_alert=True)
        return
    
    claim_id, user_id, pkg_key, payment_method, status, created_at, admin_note = claim
    
    if status != "pending":
        await callback.answer(f"Claim already {status}", show_alert=True)
        return
    
    # Approve claim
    await approve_payment_claim(claim_id, callback.from_user.id, f"Approved by {callback.from_user.id}")
    
    # Activate session
    duration = PACKAGES.get(pkg_key, PACKAGES["pkg_30"])["duration"]
    await activate_session(user_id, duration)
    
    # Notify user
    user_lang = await get_user_lang(user_id)
    try:
        await bot.send_message(user_id, get_text(user_lang, "payment_approved"))
        await bot.send_message(user_id, get_text(user_lang, "session_unlocked"))
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")
    
    await callback.message.edit_text(
        f"✅ Claim #{claim_id} APPROVED\n"
        f"User {user_id} activated for {duration} min"
    )
    await callback.answer("Approved!")

@router.callback_query(F.data.startswith("reject_"))
async def admin_reject_claim(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Not authorized", show_alert=True)
        return
    
    # Data: reject_{claim_id}
    claim_id = int(callback.data.split("_")[1])
    
    # Get claim details
    claim = await get_payment_claim(claim_id)
    if not claim:
        await callback.answer("Claim not found", show_alert=True)
        return
    
    claim_id, user_id, pkg_key, payment_method, status, created_at, admin_note = claim
    
    if status != "pending":
        await callback.answer(f"Claim already {status}", show_alert=True)
        return
    
    # Reject claim
    await reject_payment_claim(claim_id, callback.from_user.id, f"Rejected by {callback.from_user.id}")
    
    # Notify user
    user_lang = await get_user_lang(user_id)
    try:
        await bot.send_message(
            user_id, 
            get_text(user_lang, "payment_rejected")
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")
    
    await callback.message.edit_text(
        f"❌ Claim #{claim_id} REJECTED\n"
        f"User {user_id} notified"
    )
    await callback.answer("Rejected")

from aiogram.filters import Command
from aiogram.types import Message
from utils.db_helpers import reset_user_data
import aiosqlite
from utils.db import DB_PATH


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        # Total users
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]

        # New users this week
        async with db.execute("""
            SELECT COUNT(DISTINCT user_id) FROM analytics_events
            WHERE event_type = 'bot_start'
            AND created_at >= datetime('now', '-7 days')
        """) as c:
            new_week = (await c.fetchone())[0]

        # Active subscriptions by plan
        async with db.execute("""
            SELECT plan, COUNT(*) FROM subscriptions
            WHERE status = 'active' AND expires_at > CURRENT_TIMESTAMP
            GROUP BY plan
        """) as c:
            subs_by_plan = await c.fetchall()

        total_subs = sum(r[1] for r in subs_by_plan)

        # Messages today
        async with db.execute("""
            SELECT COUNT(*) FROM analytics_events
            WHERE event_type = 'consultation_message'
            AND created_at >= date('now')
        """) as c:
            msgs_today = (await c.fetchone())[0]

        # Messages this week
        async with db.execute("""
            SELECT COUNT(*) FROM analytics_events
            WHERE event_type = 'consultation_message'
            AND created_at >= datetime('now', '-7 days')
        """) as c:
            msgs_week = (await c.fetchone())[0]

        # Top features this week
        async with db.execute("""
            SELECT event_type, COUNT(*) as cnt FROM analytics_events
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY event_type ORDER BY cnt DESC LIMIT 5
        """) as c:
            top_events = await c.fetchall()

        # Referrals
        async with db.execute("SELECT COUNT(*) FROM referrals") as c:
            total_refs = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM referrals WHERE referred_subscribed = 1") as c:
            paid_refs = (await c.fetchone())[0]

        # Pending payment claims
        async with db.execute("SELECT COUNT(*) FROM payment_claims WHERE status = 'pending'") as c:
            pending_claims = (await c.fetchone())[0]

    # Build subs line
    subs_line = "  ".join([f"{p}: {n}" for p, n in subs_by_plan]) if subs_by_plan else "0"

    # Build top events line
    events_lines = "\n".join([f"  • {e}: {n}" for e, n in top_events]) or "  нет данных"

    text = (
        f"📊 *Статистика бота*\n\n"
        f"👥 *Пользователи*\n"
        f"  Всего: {total_users} | +{new_week} за неделю\n\n"
        f"💳 *Подписки*: {total_subs} активных\n"
        f"  {subs_line}\n\n"
        f"💬 *Сообщения*\n"
        f"  Сегодня: {msgs_today} | Неделя: {msgs_week}\n\n"
        f"🔥 *Топ событий (7 дней)*\n"
        f"{events_lines}\n\n"
        f"🔗 *Рефералы*: {total_refs} всего / {paid_refs} оплатили\n"
        f"⏳ *Ожидают оплаты*: {pending_claims}"
    )

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("reset_user"))
async def cmd_reset_user(message, command):
    if message.from_user.id not in ADMIN_IDS:
        return

    # Check args
    if not command.args:
        await message.answer("Usage: /reset_user <user_id>")
        return
    
    try:
        target_user_id = int(command.args)
        await reset_user_data(target_user_id)
        await message.answer(f"✅ User {target_user_id} fully reset (Session ended, Trial cleared, Claims deleted).")
    except ValueError:
        await message.answer("Invalid User ID")
    except Exception as e:
        logger.error(f"Reset user failed: {e}")
        await message.answer(f"❌ Error: {e}")

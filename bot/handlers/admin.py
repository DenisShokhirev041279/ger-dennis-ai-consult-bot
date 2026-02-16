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

PACKAGES = {
    "pkg_30": {"duration": 30},
    "pkg_60": {"duration": 60},
    "pkg_audit": {"duration": 120}
}

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

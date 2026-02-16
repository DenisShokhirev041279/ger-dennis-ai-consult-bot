from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from utils.db import activate_session, get_user_lang
from utils.i18n import get_text
from utils.config import ADMIN_ID

router = Router()

@router.callback_query(F.data.startswith("approve_"))
async def admin_approve(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Not authorized")
        return

    # Data: approve_{user_id}_{ref}
    parts = callback.data.split("_")
    user_id = int(parts[1])
    ref = parts[2]
    
    # Determine duration from ref or default to 30
    duration = 30
    if "pkg_60" in ref: duration = 60
    elif "pkg_audit" in ref: duration = 120
    
    await activate_session(user_id, duration)
    
    # Notify User
    user_lang = await get_user_lang(user_id)
    try:
        await bot.send_message(user_id, get_text(user_lang, "session_unlocked"))
    except:
        pass # User might have blocked bot
        
    await callback.message.edit_text(f"Approved {user_id} for {duration} mins.")

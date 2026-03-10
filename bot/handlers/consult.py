import time
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import get_session_info, end_session, get_user_lang
from utils.i18n import get_text
from bot.ai.openai_client import get_ai_response

router = Router()

from aiogram.fsm.state import default_state

@router.message(default_state)
@router.message(UserStates.CONSULT_MODE)
async def consult_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if not message.text:
        return
    
    # Rate Limiter
    from utils.rate_limiter import is_rate_limited
    from utils.config import ADMIN_IDS
    if is_rate_limited(user_id) and user_id not in ADMIN_IDS:
        await message.answer("⚠️ Too many messages. Please wait a minute.")
        return

    # Get user language early
    user_lang = await get_user_lang(user_id)

    # Check Subscription
    from utils.subscription import check_subscription
    sub_data = await check_subscription(user_id)
    is_paid = sub_data["has_subscription"] or user_id in ADMIN_IDS
    mode = "paid" if is_paid else "trial"
    
    msg_count, _ = await get_trial_usage_today(user_id)
    
    # PROGRESSIVE TRIAL LOGIC
    if not is_paid:
        from utils.config import TRIAL_MAX_MESSAGES
        
        # Determine if we should allow based on total msg count and bonuses
        # Assume base trial is 10 messages (1-5 full, 6-10 short)
        # 11+ requires upsell OR bonus credit
        from utils.db_helpers import get_bonus_credits, update_bonus_credits
        bonus = await get_bonus_credits(user_id)
        
        total_allowed = 10 + bonus
        
        if msg_count >= total_allowed:
            # Upsell
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Subscribe / My Plan", callback_data="subscribe_menu")],
                [InlineKeyboardButton(text="🤝 Refer a Friend (+1 msg)", callback_data="menu_referrals")]
            ])
            await message.answer("TRIAL EXHAUSTED. Please subscribe or refer a friend.", reply_markup=kb)
            return
            
        if msg_count >= 10:
            # Using bonus credit
            await update_bonus_credits(user_id, -1)
            from utils.analytics import track
            await track(user_id, "bonus_credit_used")
        
        await increment_trial_messages(user_id)
        
    # Check Security
    from utils.security import is_prompt_injection, sanitize_user_input
    user_input = sanitize_user_input(message.text)
    if is_prompt_injection(user_input):
        await message.answer("⚠️ Security Alert: Valid consultation topic required.")
        return

    # Conversation Memory
    from utils.db_helpers_memory import save_message, get_conversation_history, get_current_session_id
    session_id = await get_current_session_id(user_id)
    
    # Get history
    history = await get_conversation_history(user_id, session_id, limit=20)
    
    # Add current message to DB
    await save_message(user_id, session_id, "user", message.text)
    
    # Prepare history for AI
    current_messages = history + [{"role": "user", "content": message.text}]

    processing_msg = await message.answer(get_text(user_lang, "processing"))
    
    # Call AI with mode and history
    # Progressive trial system for AI prompt
    if not is_paid and msg_count >= 5: # (0-indexed effectively since we just incremented, actually msg_count was fetched BEFORE increment)
        mode = "trial_short"
    
    response = await get_ai_response(lang=user_lang, mode=mode, messages=current_messages)
    
    # Watermark for non-subscribers
    if not is_paid:
        response += "\n\n— Powered by Ger Dennis AI | @ger_dennis_ai"
        
    # Save Assistant Response
    await save_message(user_id, session_id, "assistant", response)

    # Analytics
    from utils.analytics import track
    await track(user_id, "consultation_message", {"mode": mode, "is_paid": is_paid})

    await processing_msg.edit_text(response)

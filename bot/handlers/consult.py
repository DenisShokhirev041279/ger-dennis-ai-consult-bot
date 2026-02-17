import time
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import get_session_info, end_session, get_user_lang
from utils.i18n import get_text
from bot.ai.openai_client import get_ai_response

router = Router()

@router.message()
async def consult_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if not message.text:
        await message.answer("Please send text.")
        return
    
    # Get user language early
    user_lang = await get_user_lang(user_id)

    # Check Session
    session = await get_session_info(user_id)
    # session: (start_time, duration_minutes, is_active)
    
    is_paid = False
    
    if session and session[2]:
        start_time = session[0]
        duration_minutes = session[1]
        elapsed_minutes = (int(time.time()) - start_time) / 60
        
        if elapsed_minutes >= duration_minutes:
            await end_session(user_id)
            await message.answer(get_text(user_lang, "session_ended"))
            await state.clear()
            # Fallthrough to trial check? No, session just ended.
            # But user might want to continue in trial if available? 
            # Request says "HARD STOP" if trial exhausted. 
            # Let's treat ended session as "no active session" for next message.
            # For THIS message, just say ended.
            return
        
        is_paid = True
        remaining = int(duration_minutes - elapsed_minutes)
    
    # TRIAL MODE LOGIC
    if not is_paid:
        from utils.config import TRIAL_LIMIT_PER_DAY, TRIAL_MAX_MESSAGES
        from utils.db_helpers import get_trial_usage_today, increment_trial_messages
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        msg_count, _ = await get_trial_usage_today(user_id)
        
        if msg_count >= TRIAL_MAX_MESSAGES:
            # Hard stop + Upsell
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_text(user_lang, "menu_book"), callback_data="book_start")],
                [InlineKeyboardButton(text=get_text(user_lang, "menu_portfolio"), callback_data="portfolio")],
                [InlineKeyboardButton(text=get_text(user_lang, "menu_channel"), url="https://t.me/ger_dennis")] 
            ])
            await message.answer(get_text(user_lang, "trial_ended"), reply_markup=kb)
            return
            
        # Increment usage
        await increment_trial_messages(user_id)
        
    # Check Security
    from utils.security import is_prompt_injection, sanitize_user_input
    
    user_input = sanitize_user_input(message.text)
    
    if is_prompt_injection(user_input):
        await message.answer("⚠️ Security Alert: Valid consultation topic required.")
        return

    processing_msg = await message.answer(get_text(user_lang, "processing") if user_lang else "...")
    
    # Call AI with mode
    mode = "paid" if is_paid else "trial"
    response = await get_ai_response(user_input, user_lang, mode=mode)
    
    # Append time notice if low (only paid)
    if is_paid and remaining <= 5 and remaining > 0:
        response += f"\n\n⏳ {get_text(user_lang, 'time_left', minutes=remaining)}"
    
    # Append upsell if trial (maybe on last message?)
    if not is_paid:
        # Check if this was the last allowed message
        if msg_count + 1 >= TRIAL_MAX_MESSAGES: # +1 because we just incremented
             # Actually we incremented in DB but local var msg_count is old.
             # Let's just add a footer seeing as they used a trial slot.
             pass 

    await processing_msg.edit_text(response)

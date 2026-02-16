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
        return
    
    # Check Session
    session = await get_session_info(user_id)
    # session: (start_time, duration_minutes, is_active)
    
    if not session or not session[2]:
        user_lang = await get_user_lang(user_id)
        await message.answer(get_text(user_lang, "access_denied"))
        return

    start_time = session[0]
    duration_minutes = session[1]
    elapsed_minutes = (int(time.time()) - start_time) / 60
    
    if elapsed_minutes >= duration_minutes:
        await end_session(user_id)
        user_lang = await get_user_lang(user_id)
        await message.answer(get_text(user_lang, "session_ended"))
        await state.clear()
        return
    
    # Get user language early
    user_lang = await get_user_lang(user_id)
        
    # Valid Session -> Check Security
    from utils.security import is_prompt_injection, sanitize_user_input
    
    user_input = sanitize_user_input(message.text)
    
    if is_prompt_injection(user_input):
        await message.answer("⚠️ Security Alert: Valid consultation topic required. Please focus on AI Systems Architecture or Viral Content strategies.")
        return

    # Calculate remaining time
    remaining = int(duration_minutes - elapsed_minutes)
    
    processing_msg = await message.answer(get_text(user_lang, "processing") if user_lang else "...")
    
    response = await get_ai_response(user_input, user_lang)
    
    # Append time notice if low
    if remaining <= 5 and remaining > 0:
        response += f"\n\n⏳ {get_text(user_lang, 'time_left', minutes=remaining)}"
    
    await processing_msg.edit_text(response)

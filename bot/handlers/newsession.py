from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.db_helpers_memory import clear_session_history, get_current_session_id
from utils.db import get_user_lang
from utils.i18n import get_text
from utils.analytics import track

router = Router()

@router.message(Command("newsession"))
async def cmd_newsession(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)
    
    session_id = await get_current_session_id(user_id)
    await clear_session_history(user_id, session_id)
    
    await track(user_id, "new_session_command")
    
    msg = "✅ Контекст беседы очищен. Начнем с чистого листа!" if user_lang == "ru" else "✅ Conversation context cleared. Let's start fresh!"
    if user_lang == "de":
        msg = "✅ Gesprächskontext gelöscht. Fangen wir von vorne an!"
        
    await message.answer(msg)

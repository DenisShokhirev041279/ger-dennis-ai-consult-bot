from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.states import UserStates
from aiogram.fsm.context import FSMContext
from utils.i18n import get_text
from utils.db import set_user_lang

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Reset state
    await state.clear()
    
    # Language Keyboard Only
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")],
        [InlineKeyboardButton(text="Deutsch 🇩🇪", callback_data="lang_de")]
    ])
    
    await message.answer(
        "Please select your language / Выберите язык / Bitte wählen Sie Ihre Sprache:",
        reply_markup=kb
    )
    await state.set_state(UserStates.LANGUAGE_SELECT)

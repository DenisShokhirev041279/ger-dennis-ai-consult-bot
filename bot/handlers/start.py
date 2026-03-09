from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.states import UserStates
from aiogram.fsm.context import FSMContext
from utils.i18n import get_text
from utils.db import set_user_lang

router = Router()

from aiogram.filters import CommandStart, CommandObject
from utils.db_referrals import add_referral

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    # Capture referral
    referrer_id = None
    if command.args and command.args.startswith("ref_"):
        try:
            referrer_id = int(command.args.split("_")[1])
        except (ValueError, IndexError):
            pass

    if referrer_id:
        await add_referral(referrer_id, message.from_user.id)

    # Reset state
    await state.clear()
    
    user_id = message.from_user.id
    # Check if user exists/has lang
    # Actually, let's always offer lang selection on /start for simplicity?
    # Or if user is known, show menu? 
    # Requirement: "Show on /start and language selection".
    
    # Let's show language selection inline, but ALSO show the keyboard?
    # No, usually lang select -> then menu.
    # But if they type /start later, maybe they want menu.
    
    # Hybrid: Show Lang, and if they pick one, show menu. 
    # But if they already HAVE a language set?
    
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
    
    # Also attempt to show menu if they ignore lang? 
    # The request says "Show persistent menu... on /start".
    # Creating a reply keyboard AND inline keyboard in one message is impossible.
    # So we send Inline for lang, then maybe text with Reply?
    # Or just wait for lang selection.
    
    # Let's just rely on lang selection to trigger menu show.
    # And if they are an old user, they can re-select lang to get menu.

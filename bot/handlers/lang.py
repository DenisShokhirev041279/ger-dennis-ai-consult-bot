from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import set_user_lang
from utils.i18n import get_text

router = Router()

@router.callback_query(F.data.startswith("lang_"))
async def lang_selected(callback: CallbackQuery, state: FSMContext):
    lang_code = callback.data.split("_")[1]
    user_id = callback.from_user.id
    username = callback.from_user.username
    
    # Save to DB
    await set_user_lang(user_id, lang_code, username)
    # Save to FSM
    await state.update_data(lang=lang_code)
    
    # Show Persistent Menu
    from bot.handlers.menu import show_main_menu
    await show_main_menu(callback.message, user_id)
    await callback.answer()

async def show_main_menu(message, lang_code, state):
    text = get_text(lang_code, "welcome")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang_code, "menu_book"), callback_data="menu_book")],
        [InlineKeyboardButton(text=get_text(lang_code, "menu_services"), callback_data="menu_services")],
        [InlineKeyboardButton(text=get_text(lang_code, "menu_portfolio"), callback_data="menu_portfolio")],
        [InlineKeyboardButton(text=get_text(lang_code, "menu_portfolio"), callback_data="menu_portfolio")]
    ])
    
    await message.answer(text, reply_markup=kb)
    await state.set_state(UserStates.MAIN_MENU)

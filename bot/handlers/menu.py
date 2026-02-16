from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.db import get_user_lang
from utils.i18n import get_text
from bot.states import UserStates

router = Router()

@router.callback_query(F.data == "menu_services")
async def show_services(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    # For now just show text, maybe back button
    await callback.message.answer(get_text(lang, "pkg_audit") + "\n" + get_text(lang, "pkg_60"))
    await callback.answer()

@router.callback_query(F.data == "menu_portfolio")
async def show_portfolio(callback: CallbackQuery, state: FSMContext):
    # Placeholder
    await callback.message.answer("Portfolio: https://t.me/ger_dennis_ai")
    await callback.answer()

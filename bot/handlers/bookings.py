from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import get_user_lang
from utils.i18n import get_text
from bot.payments.stars import create_stars_invoice

router = Router()

@router.callback_query(F.data == "menu_book")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "pkg_30"), callback_data="pkg_30")],
        [InlineKeyboardButton(text=get_text(lang, "pkg_60"), callback_data="pkg_60")],
        [InlineKeyboardButton(text=get_text(lang, "pkg_audit"), callback_data="pkg_audit")]
    ])
    
    await callback.message.answer(get_text(lang, "book_select_package"), reply_markup=kb)
    await state.set_state(UserStates.BOOKING_PACKAGE)
    await callback.answer()

@router.callback_query(F.data.startswith("pkg_"))
async def select_payment(callback: CallbackQuery, state: FSMContext):
    pkg = callback.data
    await state.update_data(selected_package=pkg)
    
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "pay_stars"), callback_data="pay_stars")],
        [InlineKeyboardButton(text=get_text(lang, "pay_fiat"), callback_data="pay_fiat")],
        [InlineKeyboardButton(text=get_text(lang, "pay_crypto"), callback_data="pay_crypto")]
    ])
    
    await callback.message.answer(get_text(lang, "payment_method"), reply_markup=kb)
    await state.set_state(UserStates.BOOKING_PAYMENT)
    await callback.answer()

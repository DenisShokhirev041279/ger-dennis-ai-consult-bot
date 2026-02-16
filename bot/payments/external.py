from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import get_user_lang
from utils.i18n import get_text
from utils.config import IBAN, WISE_DETAILS, USDT_WALLET, TON_WALLET, ADMIN_ID

router = Router()

@router.callback_query(F.data.in_({"pay_fiat", "pay_crypto"}))
async def pay_external_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    method = callback.data
    
    data = await state.get_data()
    pkg_key = data.get("selected_package", "pkg_30")
    
    # Simple logic to determine amount (mocking value for external based on stars ratio or fixed)
    # Let's just say 100 Stars ~= 2 USD for simplicity in this mock, or provided in real env.
    # The prompt didn't specify fiat prices, so I'll genericize.
    amount = "CONTACT ADMIN" 
    
    if pkg_key == "pkg_30": amount = "50 USD / 45 EUR"
    elif pkg_key == "pkg_60": amount = "90 USD / 80 EUR"
    elif pkg_key == "pkg_audit": amount = "250 USD / 230 EUR"
    
    ref = f"REF-{user_id}-{pkg_key}"
    await state.update_data(payment_ref=ref, payment_amount=amount)
    
    text_key = "fiat_instruct" if method == "pay_fiat" else "crypto_instruct"
    
    instruct_text = get_text(lang, text_key, 
        amount=amount, 
        iban=IBAN, 
        wise=WISE_DETAILS, 
        usdt=USDT_WALLET, 
        ton=TON_WALLET, 
        ref=ref
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "i_paid"), callback_data="i_paid")]
    ])
    
    await callback.message.answer(instruct_text, reply_markup=kb)
    await state.set_state(UserStates.WAIT_FOR_PAYMENT)
    await callback.answer()

@router.callback_query(F.data == "i_paid")
async def i_paid_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    username = callback.from_user.username
    lang = await get_user_lang(user_id)
    data = await state.get_data()
    
    ref = data.get("payment_ref", "UNKNOWN")
    amount = data.get("payment_amount", "UNKNOWN")
    
    # Notify Admin
    if ADMIN_ID:
        admin_text = get_text("en", "admin_alert", 
            user_id=user_id, 
            username=username, 
            ref=ref, 
            amount=amount
        )
        # Add Approve Button
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"Approve {user_id}", callback_data=f"approve_{user_id}_{ref}")]
        ])
        await bot.send_message(ADMIN_ID, admin_text, reply_markup=kb)
        
    await callback.message.answer("Payment claim sent. Waiting for admin approval.")
    await callback.answer()

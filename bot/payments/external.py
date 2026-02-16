from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import get_user_lang
from utils.i18n import get_text
from utils.config import IBAN, WISE_DETAILS, USDT_WALLET, TON_WALLET, ADMIN_IDS
from utils.db_helpers import create_payment_claim
from utils.logger import logger

router = Router()

PACKAGES = {
    "pkg_30": {"amount_usd": 50, "amount_eur": 45, "duration": 30},
    "pkg_60": {"amount_usd": 90, "amount_eur": 80, "duration": 60},
    "pkg_audit": {"amount_usd": 250, "amount_eur": 230, "duration": 120}
}

@router.callback_query(F.data.in_({"pay_fiat", "pay_crypto"}))
async def pay_external_choose_method(callback: CallbackQuery, state: FSMContext):
    """Show specific payment method buttons"""
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    method_type = callback.data
    
    if method_type == "pay_fiat":
        buttons = []
        if IBAN:
            buttons.append([InlineKeyboardButton(text="IBAN", callback_data="pay_iban")])
        if WISE_DETAILS:
            buttons.append([InlineKeyboardButton(text="Wise", callback_data="pay_wise")])
        
        if not buttons:
            await callback.answer("Payment method temporarily unavailable", show_alert=True)
            return
        
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer("Select fiat payment method:", reply_markup=kb)
    
    elif method_type == "pay_crypto":
        buttons = []
        if USDT_WALLET:
            buttons.append([InlineKeyboardButton(text="USDT (TRC20)", callback_data="pay_usdt")])
        if TON_WALLET:
            buttons.append([InlineKeyboardButton(text="TON", callback_data="pay_ton")])
        
        if not buttons:
            await callback.answer("Payment method temporarily unavailable", show_alert=True)
            return
        
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer("Select crypto payment method:", reply_markup=kb)
    
    await callback.answer()

@router.callback_query(F.data.in_({"pay_iban", "pay_wise", "pay_usdt", "pay_ton"}))
async def pay_external_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    payment_method = callback.data.replace("pay_", "")  # iban, wise, usdt, ton
    
    data = await state.get_data()
    pkg_key = data.get("selected_package", "pkg_30")
    pkg = PACKAGES.get(pkg_key, PACKAGES["pkg_30"])
    
    amount = f"{pkg['amount_usd']} USD / {pkg['amount_eur']} EUR"
    ref = f"REF-{user_id}-{pkg_key}"
    
    await state.update_data(payment_ref=ref, payment_amount=amount, payment_method=payment_method)
    
    # Build instructions based on method
    if payment_method == "iban":
        instruct_text = f"Please send {amount} to:\nIBAN: {IBAN}\n\nReference: {ref}\n\nClick 'I Paid' when done."
    elif payment_method == "wise":
        instruct_text = f"Please send {amount} to:\nWise: {WISE_DETAILS}\n\nReference: {ref}\n\nClick 'I Paid' when done."
    elif payment_method == "usdt":
        instruct_text = f"Please send {amount} worth of USDT to:\nAddress (TRC20): {USDT_WALLET}\n\nComment: {ref}\n\nClick 'I Paid' when done."
    elif payment_method == "ton":
        instruct_text = f"Please send {amount} worth of TON to:\nAddress: {TON_WALLET}\n\nComment: {ref}\n\nClick 'I Paid' when done."
    else:
        instruct_text = "Payment method not configured."
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "i_paid"), callback_data="i_paid")]
    ])
    
    await callback.message.answer(instruct_text, reply_markup=kb)
    await state.set_state(UserStates.WAIT_FOR_PAYMENT)
    await callback.answer()

@router.callback_query(F.data == "i_paid")
async def i_paid_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    username = callback.from_user.username or "unknown"
    lang = await get_user_lang(user_id)
    data = await state.get_data()
    
    pkg_key = data.get("selected_package", "pkg_30")
    ref = data.get("payment_ref", "UNKNOWN")
    amount = data.get("payment_amount", "UNKNOWN")
    method = data.get("payment_method", "unknown")
    
    # Create payment claim with full details
    claim_id = await create_payment_claim(
        user_id=user_id,
        package_key=pkg_key,
        payment_method=method,
        ref=ref,
        amount_text=amount,
        chat_id=callback.message.chat.id
    )
    
    # Notify ALL admins
    if ADMIN_IDS:
        admin_text = (
            f"💰 Payment Claim #{claim_id}\n\n"
            f"User: @{username} (ID: {user_id})\n"
            f"Package: {pkg_key}\n"
            f"Amount: {amount}\n"
            f"Method: {method.upper()}\n"
            f"Reference: {ref}"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{claim_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{claim_id}")
            ]
        ])
        
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, admin_text, reply_markup=kb)
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    await callback.message.answer(get_text(lang, "payment_pending"))
    await callback.answer()

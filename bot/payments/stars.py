from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, ContentType, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import activate_session, get_user_lang, set_user_lang
from utils.i18n import get_text
from utils.logger import logger

router = Router()

PACKAGES = {
    "pkg_30": {"amount": 4950, "duration": 30, "title": "30 min Consult"},
    "pkg_60": {"amount": 8950, "duration": 60, "title": "60 min Strategy"},
    "pkg_audit": {"amount": 24950, "duration": 120, "title": "Full Audit"} # Assuming 2 hours for audit
}

@router.callback_query(F.data == "pay_stars")
async def pay_stars_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pkg_key = data.get("selected_package")
    pkg = PACKAGES.get(pkg_key)
    
    if not pkg:
        await callback.answer("Error: Package not found")
        return

    prices = [LabeledPrice(label=pkg["title"], amount=pkg["amount"])]
    await callback.message.answer_invoice(
        title=pkg["title"],
        description=f"Unlocks {pkg['duration']} minutes of AI consultation.",
        payload=f"stars:{pkg_key}:{callback.from_user.id}",
        provider_token=None,
        currency="XTR",
        prices=prices
    )
    await callback.answer()

@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def stars_success(message: Message, state: FSMContext):
    payload = message.successful_payment.invoice_payload
    parts = payload.split(":")
    
    if len(parts) < 3:
        logger.error(f"Malformed payload: {payload}")
        return
    
    pkg_key = parts[1]
    pkg = PACKAGES.get(pkg_key)
    
    if pkg:
        await activate_session(message.from_user.id, pkg["duration"])
        user_lang = await get_user_lang(message.from_user.id)
        
        await message.answer(get_text(user_lang, "payment_success"))
        await message.answer(get_text(user_lang, "session_unlocked"))
        await state.set_state(UserStates.CONSULT_MODE)
        
        logger.info(f"Stars payment success user={message.from_user.id} amount={message.successful_payment.total_amount}")

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, Message, ContentType
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from bot.config.plans import PLANS
from utils.db import get_user_lang
from utils.i18n import get_text
from utils.subscription import activate_subscription, check_subscription
from utils.analytics import track
from utils.logger import logger

router = Router()

@router.callback_query(F.data == "subscribe_menu")
async def show_subscribe_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    
    # Check current sub
    sub_data = await check_subscription(user_id)
    
    _header = {"ru": "⭐ *Тарифные планы*", "de": "⭐ *Abonnement-Pläne*"}.get(lang, "⭐ *Subscription Plans*")
    msg = f"{_header}\n\n"
    if sub_data["has_subscription"]:
        plan_title = PLANS[sub_data["plan"]][f"title_{lang}"] if f"title_{lang}" in PLANS[sub_data["plan"]] else PLANS[sub_data["plan"]]["title_en"]
        _current = {"ru": "Ваш текущий план", "de": "Ihr aktueller Plan"}.get(lang, "Your current plan")
        msg += f"{_current}: *{plan_title}*\n\n"
    
    # Simple inline keyboard for plans
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Starter ({PLANS['starter']['price_stars']}🌟/mo)", callback_data="buy_plan_starter")],
        [InlineKeyboardButton(text=f"Pro ({PLANS['pro']['price_stars']}🌟/mo)", callback_data="buy_plan_pro")],
        [InlineKeyboardButton(text=f"Business ({PLANS['business']['price_stars']}🌟/mo)", callback_data="buy_plan_business")]
    ])
    
    await callback.message.answer(msg, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("buy_plan_"))
async def buy_plan_start(callback: CallbackQuery, state: FSMContext):
    plan_key = callback.data.split("buy_plan_")[1]
    plan = PLANS.get(plan_key)
    
    if not plan:
        await callback.answer("Plan not found.", show_alert=True)
        return
        
    user_id = callback.from_user.id
    lang = await get_user_lang(user_id)
    title = plan.get(f"title_{lang}", plan["title_en"])

    # For simplicity, we just use Stars here natively, or we can offer External
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text={"ru": "⭐ Оплатить Stars", "de": "⭐ Mit Stars bezahlen"}.get(lang, "⭐ Pay with Stars"), callback_data=f"stars_plan_{plan_key}")],
        [InlineKeyboardButton(text=get_text(lang, "pay_fiat"), callback_data="pay_fiat")],
        [InlineKeyboardButton(text=get_text(lang, "pay_crypto"), callback_data="pay_crypto")]
    ])
    
    await state.update_data(selected_package=plan_key, is_subscription=True)
    _choose = {"ru": f"Выбран: *{title}*\nСпособ оплаты:", "de": f"Gewählt: *{title}*\nZahlungsmethode:"}.get(lang, f"Selected: *{title}*\nPayment method:")
    await callback.message.answer(_choose, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("stars_plan_"))
async def stars_plan_buy(callback: CallbackQuery):
    plan_key = callback.data.split("stars_plan_")[1]
    plan = PLANS.get(plan_key)
    
    if not plan:
        return
        
    prices = [LabeledPrice(label=plan["title_en"], amount=plan["price_stars"])]
    
    await callback.message.answer_invoice(
        title=plan["title_en"],
        description=f"Monthly subscription: {plan['title_en']}",
        payload=f"sub:{plan_key}:{callback.from_user.id}",
        provider_token=None,
        currency="XTR",
        prices=prices
    )
    await callback.answer()

@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def stars_sub_success(message: Message, state: FSMContext, bot: Bot):
    payload = message.successful_payment.invoice_payload
    parts = payload.split(":")
    
    if len(parts) >= 3 and parts[0] == "sub":
        plan_key = parts[1]
        user_id = int(parts[2])
        
        await activate_subscription(user_id, plan_key, bot=bot)
        await track(user_id, "subscription_purchased", {"plan": plan_key, "method": "stars"})
        
        # Note: In a real production app, we would notify admins and update the active sessions 
        # (remove duration limits from active sessions).
        lang = await get_user_lang(user_id)
        msg_success = {"ru": "✅ Подписка успешно активирована! Спасибо!", "de": "✅ Abonnement erfolgreich aktiviert! Danke!"}.get(lang, "✅ Subscription activated! Thank you!")
        await message.answer(msg_success)

        from bot.handlers.menu import show_main_menu
        await show_main_menu(message, user_id)
        
        from utils.config import ADMIN_IDS
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, f"💰 Sub Purchased: User {user_id} bought {plan_key} via Stars.")
            except:
                pass
        
        # We might need to call Stars normal package handler if this is not a sub
    else:
        # Fallback to older package logic if needed 
        pass

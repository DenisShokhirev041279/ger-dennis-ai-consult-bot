from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from bot.states import UserStates
from utils.db import get_user_lang
from utils.i18n import get_text
from utils.config import ADMIN_IDS, TRIAL_MAX_MESSAGES
from utils.db_helpers import get_trial_usage_today, get_trial_usage_total, increment_trial_messages, get_bonus_credits, update_bonus_credits
from utils.config import FREE_DAILY_MESSAGES
from utils.subscription import check_subscription
from utils.security import is_prompt_injection, sanitize_user_input
from utils.db_helpers_memory import save_message, get_conversation_history, get_current_session_id
from utils.analytics import track
from bot.ai.openai_client import get_ai_response

router = Router()


@router.message(default_state)
@router.message(UserStates.CONSULT_MODE)
async def consult_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if not message.text:
        return

    # Get language first — needed for all user-facing messages
    user_lang = await get_user_lang(user_id)

    # Admin full bypass — no checks, no watermark, full response
    if user_id in ADMIN_IDS:
        session_id = await get_current_session_id(user_id)
        history = await get_conversation_history(user_id, session_id, limit=20)
        await save_message(user_id, session_id, "user", message.text)
        current_messages = history + [{"role": "user", "content": message.text}]
        processing_msg = await message.answer(get_text(user_lang, "processing"))
        response = await get_ai_response(lang=user_lang, mode="paid", messages=current_messages)
        await save_message(user_id, session_id, "assistant", response)
        await processing_msg.edit_text(response)
        return

    # Rate Limiter
    from utils.rate_limiter import is_rate_limited
    if is_rate_limited(user_id):
        _rate_msg = {
            "ru": "⚠️ Слишком много сообщений. Подождите минуту.",
            "de": "⚠️ Zu viele Nachrichten. Bitte warten Sie eine Minute.",
        }.get(user_lang, "⚠️ Too many messages. Please wait a minute.")
        await message.answer(_rate_msg)
        return

    # Check Subscription
    sub_data = await check_subscription(user_id)
    is_paid = sub_data["has_subscription"]
    mode = "paid" if is_paid else "trial"

    # Trial logic — daily limit
    if not is_paid:
        msg_today, _ = await get_trial_usage_today(user_id)
        bonus = await get_bonus_credits(user_id)
        daily_allowed = FREE_DAILY_MESSAGES + bonus

        if msg_today >= daily_allowed:
            _trial_texts = {
                "ru": f"🔒 Дневной лимит исчерпан ({FREE_DAILY_MESSAGES} сообщений/день на Free).\n\nОформите подписку или пригласите друга (+3 сообщения):",
                "de": f"🔒 Tageslimit erreicht ({FREE_DAILY_MESSAGES} Nachrichten/Tag kostenlos).\n\nAbonnieren Sie oder laden Sie einen Freund ein (+3 Nachrichten):",
            }
            _sub_btn = {"ru": "⭐ Оформить подписку", "de": "⭐ Abonnieren"}.get(user_lang, "⭐ Subscribe")
            _ref_btn = {"ru": "🤝 Пригласить друга (+10 сообщений)", "de": "🤝 Freund einladen (+10)"}.get(user_lang, "🤝 Refer a Friend (+10 msgs)")
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=_sub_btn, callback_data="subscribe_menu")],
                [InlineKeyboardButton(text=_ref_btn, callback_data="menu_referrals")]
            ])
            await message.answer(_trial_texts.get(user_lang, f"🔒 Daily limit reached ({FREE_DAILY_MESSAGES} messages/day on Free). Please subscribe or refer a friend."), reply_markup=kb)
            return

        if msg_today >= FREE_DAILY_MESSAGES:
            await update_bonus_credits(user_id, -1)
            await track(user_id, "bonus_credit_used")

        await increment_trial_messages(user_id)

    # Security check
    user_input = sanitize_user_input(message.text)
    if is_prompt_injection(user_input):
        _sec_msg = {
            "ru": "⚠️ Пожалуйста, задайте корректный вопрос для консультации.",
            "de": "⚠️ Bitte stellen Sie eine gültige Beratungsfrage.",
        }.get(user_lang, "⚠️ Please provide a valid consultation question.")
        await message.answer(_sec_msg)
        return

    # Conversation memory
    session_id = await get_current_session_id(user_id)
    history = await get_conversation_history(user_id, session_id, limit=20)
    await save_message(user_id, session_id, "user", message.text)
    current_messages = history + [{"role": "user", "content": message.text}]

    processing_msg = await message.answer(get_text(user_lang, "processing"))
    response = await get_ai_response(lang=user_lang, mode=mode, messages=current_messages)

    await save_message(user_id, session_id, "assistant", response)
    await track(user_id, "consultation_message", {"mode": mode, "is_paid": is_paid})

    # Split long responses (Telegram 4096 char limit)
    MAX_LEN = 4000
    if len(response) <= MAX_LEN:
        await processing_msg.edit_text(response)
    else:
        await processing_msg.delete()
        chunks = [response[i:i+MAX_LEN] for i in range(0, len(response), MAX_LEN)]
        for idx, chunk in enumerate(chunks):
            suffix = f"\n\n_{idx+1}/{len(chunks)}_" if len(chunks) > 1 else ""
            await message.answer(chunk + suffix, parse_mode=None)

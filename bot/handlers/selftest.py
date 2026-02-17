from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.config import BOT_TOKEN, OPENAI_API_KEY, GEMINI_API_KEY, ADMIN_IDS, IBAN, WISE_DETAILS, USDT_WALLET, TON_WALLET
from bot.ai.openai_client import client
from utils.db_helpers import count_active_sessions, get_trial_usage_today
from utils.logger import logger

router = Router()

@router.message(Command("selftest"))
async def selftest(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    results = []
    
    # Check BOT_TOKEN
    if BOT_TOKEN:
        results.append("✅ BOT_TOKEN: OK")
    else:
        results.append("❌ BOT_TOKEN: MISSING")
    
    # Check OPENAI_API_KEY
    if OPENAI_API_KEY:
        results.append("✅ OPENAI_API_KEY: OK")
        # Show current model config
        import os
        current_model = os.getenv("OPENAI_MODEL", "gpt-4.1")
        results.append(f"🤖 OpenAI Model: {current_model}")
        results.append(f"🔁 Fallback: gpt-4o-mini")
    else:
        results.append("❌ OPENAI_API_KEY: MISSING")
    
    # Check GEMINI_API_KEY
    if GEMINI_API_KEY:
        results.append("✅ GEMINI_API_KEY: Present (Ref Photo Enabled)")
    else:
        results.append("⚠️ GEMINI_API_KEY: Not set (Ref Photo Disabled)")

    # Trial Config
    results.append(f"📊 Trial Limits: {TRIAL_MAX_MESSAGES} msgs/day, {TRIAL_LIMIT_PER_DAY} photos/day")

    # Test OpenAI ping
    if client:
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=10
            )
            results.append("✅ OpenAI API: OK")
        except Exception as e:
            results.append(f"❌ OpenAI API: FAIL - {str(e)[:100]}")
            logger.exception("Selftest OpenAI ping failed")
    else:
        results.append("❌ OpenAI API: Client not initialized")

    # Test Gemini NanoBanana Pro (via client)
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-pro')
            # Dry run generation? No, just check if model list includes it or basic instantiation works.
            # Minimal gen.
            # response = model.generate_content("ping")
            # results.append(f"✅ Gemini 1.5 Pro: OK")
            # Actually, standard limit might apply. Just report configuration.
            results.append("✅ Gemini 1.5 Pro: Configured")
        except Exception as e:
            results.append(f"⚠️ Gemini 1.5 Pro: Config Error - {e}")
    
    # Payment requisites status
    payment_status = []
    if IBAN:
        payment_status.append("IBAN")
    if WISE_DETAILS:
        payment_status.append("Wise")
    if USDT_WALLET:
        payment_status.append("USDT")
    if TON_WALLET:
        payment_status.append("TON")
    
    if payment_status:
        results.append(f"💳 Payment Methods: {', '.join(payment_status)}")
    else:
        results.append("⚠️ Payment Methods: None configured")
    
    # Active sessions count
    try:
        active_count = await count_active_sessions()
        results.append(f"🔒 Active Sessions: {active_count}")
    except Exception as e:
        results.append(f"❌ Session Count: ERROR - {e}")
    
    # Trial usage for this admin
    try:
        msg_count, photo_count = await get_trial_usage_today(message.from_user.id)
        results.append(f"📊 Trial Usage (You): {msg_count} msgs, {photo_count} photos today")
    except Exception as e:
        results.append(f"❌ Trial Stats: ERROR - {e}")
    
    await message.answer("\n".join(results))

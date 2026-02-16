from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.config import BOT_TOKEN, OPENAI_API_KEY, ADMIN_ID
from bot.ai.openai_client import client
from utils.logger import logger

router = Router()

@router.message(Command("selftest"))
async def selftest(message: Message):
    if message.from_user.id != ADMIN_ID:
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
    else:
        results.append("❌ OPENAI_API_KEY: MISSING")
    
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
    
    await message.answer("\n".join(results))

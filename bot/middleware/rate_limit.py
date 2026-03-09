from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from utils.rate_limiter import is_rate_limited
from utils.db import get_user_lang
from utils.i18n import get_text

class RateLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Check rate limit using existing helper
        if is_rate_limited(event.from_user.id):
            user_lang = await get_user_lang(event.from_user.id)
            # Send warning
            msg = "Подождите немного! Максимум 15 сообщений в минуту." if user_lang == "ru" else "Please wait! Maximum 15 messages per minute."
            if user_lang == "de":
                msg = "Bitte warten! Maximal 15 Nachrichten pro Minute."
            await event.answer(msg)
            return
            
        return await handler(event, data)

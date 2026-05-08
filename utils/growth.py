from urllib.parse import quote

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from utils.config import REFERRAL_ACTIVATION_BONUS_MESSAGES, REFERRAL_PAYMENT_BONUS_MESSAGES
from utils.db import get_user_lang


async def send_growth_loop(message: Message, feature: str = "consult") -> None:
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    if lang == "ru":
        title = {
            "brand_audit": "📤 Поделиться Brand Audit",
            "style_art": "📤 Поделиться арт-инструментом",
            "safe_motion": "📤 Поделиться Safe Motion",
        }.get(feature, "📤 Поделиться ботом")
        text = (
            f"{title}\n\n"
            "Если результат полезен — отправьте ссылку автору, владельцу канала или коллеге.\n\n"
            f"Ваша ссылка:\n{ref_link}\n\n"
            f"Бонусы: +{REFERRAL_ACTIVATION_BONUS_MESSAGES} сообщений за запуск друга "
            f"и +{REFERRAL_PAYMENT_BONUS_MESSAGES} за его оплату."
        )
        share_text = "Попробуй AI Consultant: консультации, Brand Audit Pro, арт по стилю фото и Safe Motion."
        sub_text = "⭐ Подписка"
    else:
        text = (
            "📤 Share this bot\n\n"
            "If the result is useful, send your link to a creator, channel owner or colleague.\n\n"
            f"Your link:\n{ref_link}\n\n"
            f"Bonuses: +{REFERRAL_ACTIVATION_BONUS_MESSAGES} messages when a friend starts "
            f"and +{REFERRAL_PAYMENT_BONUS_MESSAGES} after their payment."
        )
        share_text = "Try AI Consultant: strategy chat, Brand Audit Pro, photo style art and Safe Motion."
        sub_text = "⭐ Subscribe"

    share_url = f"https://t.me/share/url?url={quote(ref_link)}&text={quote(share_text)}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Share / Переслать", url=share_url)],
        [InlineKeyboardButton(text=sub_text, callback_data="subscribe_menu")],
    ])
    await message.answer(text, reply_markup=kb)

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from utils.db import get_user_lang
from utils.i18n import get_text
from utils.config import GEMINI_API_KEY, REFERRAL_ACTIVATION_BONUS_MESSAGES, REFERRAL_PAYMENT_BONUS_MESSAGES

router = Router()

async def get_main_keyboard(user_lang):
    sub_text = "⭐ Подписка" if user_lang == "ru" else "⭐ Subscribe / My Plan"
    tools_text = "🎨 AI Инструменты" if user_lang == "ru" else ("🎨 KI Werkzeuge" if user_lang == "de" else "🎨 AI Tools")
    ref_btn_text = "🤝 Рефералы" if user_lang == "ru" else "🤝 Referrals"
    concept_text = "🎨 Арт по стилю фото" if user_lang == "ru" else ("🎨 Foto-Stil-Art" if user_lang == "de" else "🎨 Photo Style Art")

    status_text = "📊 Мой статус" if user_lang == "ru" else ("📊 Mein Status" if user_lang == "de" else "📊 My Status")

    buttons = [
        [KeyboardButton(text=sub_text), KeyboardButton(text=status_text)],
    ]
    if GEMINI_API_KEY:
        buttons.append([KeyboardButton(text=concept_text), KeyboardButton(text=tools_text)])
    else:
        buttons.append([KeyboardButton(text=tools_text)])
    info_text = "ℹ️ Информация" if user_lang == "ru" else ("ℹ️ Information" if user_lang == "de" else "ℹ️ Info")
    buttons.append([KeyboardButton(text=ref_btn_text), KeyboardButton(text="Help / Помощь")])
    buttons.append([KeyboardButton(text=info_text)])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=False)

async def show_main_menu(message: Message, user_id: int):
    user_lang = await get_user_lang(user_id)
    kb = await get_main_keyboard(user_lang)
    await message.answer(get_text(user_lang, "welcome"), reply_markup=kb)

# Handle Menu Clicks
@router.message(F.text.in_({"📊 Мой статус", "📊 My Status", "📊 Mein Status"}))
async def menu_status(message: Message):
    from bot.handlers.start import cmd_mystatus
    await cmd_mystatus(message)

@router.message(F.text.contains("Help") | F.text.contains("Помощь"))
async def menu_help(message: Message):
    lang = await get_user_lang(message.from_user.id)
    if lang == "ru":
        text = (
            "🆘 *Помощь*\n\n"
            "📌 Команды:\n"
            "• /mystatus — ваша подписка и остаток сообщений\n"
            "• /newsession — начать новый диалог\n"
            "• /start — главное меню\n\n"
            "💬 Нужна живая консультация? @ger\\_denis\\_sh"
        )
    else:
        text = (
            "🆘 *Help*\n\n"
            "📌 Commands:\n"
            "• /mystatus — your subscription & messages left\n"
            "• /newsession — start a new conversation\n"
            "• /start — main menu\n\n"
            "💬 Need a live consultation? @ger\\_denis\\_sh"
        )
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text.in_({"ℹ️ Информация", "ℹ️ Info", "ℹ️ Information"}))
async def menu_info(message: Message):
    lang = await get_user_lang(message.from_user.id)
    if lang == "ru":
        text = (
            "ℹ️ *Информация*\n\n"
            "📄 [Политика конфиденциальности](https://telegra.ph/Politika-konfidencialnosti-04-01-26)\n"
            "📄 [Пользовательское соглашение](https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19)\n\n"
            "📧 Поддержка и обращения по оплате: u9475307309@gmail.com\n"
            "💬 Персональная консультация: @ger\\_denis\\_sh"
        )
    elif lang == "de":
        text = (
            "ℹ️ *Information*\n\n"
            "📄 [Datenschutzrichtlinie](https://telegra.ph/Politika-konfidencialnosti-04-01-26)\n"
            "📄 [Nutzungsvereinbarung](https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19)\n\n"
            "📧 Support and payment requests: u9475307309@gmail.com\n"
            "💬 Personal consultation: @ger\\_denis\\_sh"
        )
    else:
        text = (
            "ℹ️ *Information*\n\n"
            "📄 [Privacy Policy](https://telegra.ph/Politika-konfidencialnosti-04-01-26)\n"
            "📄 [Terms of Service](https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19)\n\n"
            "📧 Support and payment requests: u9475307309@gmail.com\n"
            "💬 Personal consultation: @ger\\_denis\\_sh"
        )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)


@router.message(F.text.in_({"⭐ Подписка", "⭐ Subscribe / My Plan"}))
async def menu_subscribe_btn(message: Message, state):
    # Route to the inline handler logic
    from bot.handlers.subscribe import show_subscribe_menu
    # We need to simulate a callback query or refactor.
    # Refactoring show_subscribe_menu to support Message as well.
    # Quick wrapper:
    class MockCallback:
        def __init__(self, msg):
            self.from_user = msg.from_user
            self.message = msg
            
        async def answer(self, *args, **kwargs):
            pass
            
    await show_subscribe_menu(MockCallback(message))

@router.message(F.text.in_({"🤝 Рефералы", "🤝 Referrals"}))
async def menu_referrals(message: Message):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)

    from utils.db_referrals import get_referral_stats
    from utils.db_helpers import get_bonus_credits

    stats = await get_referral_stats(user_id)
    bonus = await get_bonus_credits(user_id)
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    activation_bonus_total = stats.get("activation_bonuses_granted", 0) * REFERRAL_ACTIVATION_BONUS_MESSAGES
    payment_bonus_total = stats.get("bonuses_granted", 0) * REFERRAL_PAYMENT_BONUS_MESSAGES
    earned_total = activation_bonus_total + payment_bonus_total

    if user_lang == "ru":
        msg = (
            f"🤝 *Реферальная программа*\n\n"
            f"📊 *Ваша статистика:*\n"
            f"• Приглашено: *{stats['total']}*\n"
            f"• Оплатили подписку: *{stats['paid']}*\n"
            f"• Бонусов заработано: *{earned_total}* сообщений\n"
            f"• Бонусов осталось: *{bonus}*\n\n"
            f"💡 За запуск друга: *+{REFERRAL_ACTIVATION_BONUS_MESSAGES} сообщений*.\n"
            f"💡 За оплату друга: *+{REFERRAL_PAYMENT_BONUS_MESSAGES} сообщений*.\n\n"
            f"🔗 Ваша ссылка:\n`{ref_link}`"
        )
    elif user_lang == "de":
        msg = (
            f"🤝 *Empfehlungsprogramm*\n\n"
            f"📊 *Ihre Statistik:*\n"
            f"• Eingeladen: *{stats['total']}*\n"
            f"• Haben abonniert: *{stats['paid']}*\n"
            f"• Verdiente Boni: *{earned_total}* Nachrichten\n"
            f"• Verbleibende Boni: *{bonus}*\n\n"
            f"💡 Für einen gestarteten Freund erhalten Sie *+{REFERRAL_ACTIVATION_BONUS_MESSAGES} Nachrichten*.\n"
            f"💡 Für einen zahlenden Freund erhalten Sie *+{REFERRAL_PAYMENT_BONUS_MESSAGES} Nachrichten*.\n\n"
            f"🔗 Ihr Link:\n`{ref_link}`"
        )
    else:
        msg = (
            f"🤝 *Referral Program*\n\n"
            f"📊 *Your stats:*\n"
            f"• Invited: *{stats['total']}*\n"
            f"• Subscribed: *{stats['paid']}*\n"
            f"• Bonuses earned: *{earned_total}* messages\n"
            f"• Bonuses remaining: *{bonus}*\n\n"
            f"💡 Friend starts: *+{REFERRAL_ACTIVATION_BONUS_MESSAGES} messages*.\n"
            f"💡 Friend pays: *+{REFERRAL_PAYMENT_BONUS_MESSAGES} messages*.\n\n"
            f"🔗 Your link:\n`{ref_link}`"
        )

    await message.answer(msg, parse_mode="Markdown")


@router.callback_query(F.data == "menu_referrals")
async def callback_menu_referrals(call):
    class MockMessage:
        def __init__(self, callback):
            self.from_user = callback.from_user
            self.bot = callback.bot

        async def answer(self, *args, **kwargs):
            return await call.message.answer(*args, **kwargs)

    await menu_referrals(MockMessage(call))
    await call.answer()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.message(F.text.in_({"🎨 AI Инструменты", "🎨 AI Tools", "🎨 KI Werkzeuge"}))
async def menu_ai_tools(message: Message):
    lang = await get_user_lang(message.from_user.id)
    if lang == "ru":
        text = "🎨 *AI Инструменты*\n\nВыберите инструмент:"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✂️ Удалить фон (Remove.bg)", callback_data="cv_product_photo")],
            [InlineKeyboardButton(text="📐 Social Media Kit (1:1, 4:5, 9:16)", callback_data="cv_social_kit")],
            [InlineKeyboardButton(text="🔍 Brand Audit Pro (оценка 0-100)", callback_data="cv_brand_audit")],
            [InlineKeyboardButton(text="🎬 Safe Motion (анимация фото)", callback_data="cv_ai_video")],
        ])
    elif lang == "de":
        text = "🎨 *KI Werkzeuge*\n\nWählen Sie ein Werkzeug:"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✂️ Hintergrund entfernen (Remove.bg)", callback_data="cv_product_photo")],
            [InlineKeyboardButton(text="📐 Social Media Kit (1:1, 4:5, 9:16)", callback_data="cv_social_kit")],
            [InlineKeyboardButton(text="🔍 Brand Audit Pro (Score 0-100)", callback_data="cv_brand_audit")],
            [InlineKeyboardButton(text="🎬 Safe Motion (Fotoanimation)", callback_data="cv_ai_video")],
        ])
    else:
        text = "🎨 *AI Tools*\n\nChoose a tool:"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✂️ Remove Background (Remove.bg)", callback_data="cv_product_photo")],
            [InlineKeyboardButton(text="📐 Social Media Kit (1:1, 4:5, 9:16)", callback_data="cv_social_kit")],
            [InlineKeyboardButton(text="🔍 Brand Audit Pro (score 0-100)", callback_data="cv_brand_audit")],
            [InlineKeyboardButton(text="🎬 Safe Motion (photo animation)", callback_data="cv_ai_video")],
        ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

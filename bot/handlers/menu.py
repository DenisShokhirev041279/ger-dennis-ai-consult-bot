from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from utils.db import get_user_lang
from utils.i18n import get_text
from utils.config import GEMINI_API_KEY
from bot.handlers.bookings import booking_start

router = Router()

async def get_main_keyboard(user_lang):
    sub_text = "⭐ Подписка" if user_lang == "ru" else "⭐ Subscribe / My Plan"
    tools_text = "🎨 AI Инструменты" if user_lang == "ru" else ("🎨 KI Werkzeuge" if user_lang == "de" else "🎨 AI Tools")
    ref_btn_text = "🤝 Рефералы" if user_lang == "ru" else "🤝 Referrals"
    concept_text = "🎨 AI Концепт" if user_lang == "ru" else ("🎨 AI Konzept" if user_lang == "de" else "🎨 AI Concept")

    buttons = [
        [KeyboardButton(text=sub_text)],
        [KeyboardButton(text=get_text(user_lang, "menu_book")), KeyboardButton(text=get_text(user_lang, "menu_services"))],
    ]
    if GEMINI_API_KEY:
        buttons.append([KeyboardButton(text=concept_text)])
    buttons.append([KeyboardButton(text=ref_btn_text), KeyboardButton(text=tools_text)])
    buttons.append([KeyboardButton(text="Help / Помощь")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=False)

async def show_main_menu(message: Message, user_id: int):
    user_lang = await get_user_lang(user_id)
    kb = await get_main_keyboard(user_lang)
    await message.answer(get_text(user_lang, "welcome"), reply_markup=kb)

# Handle Menu Clicks
@router.message(F.text.in_({"Забронировать", "Book Consultation", "Buchen"}))
async def menu_book(message: Message, state):
    # Trigger existing booking flow
    await booking_start(message, state)

@router.message(F.text.in_({"Услуги", "Services", "Dienstleistungen"}))
async def menu_services(message: Message, state):
    await booking_start(message, state)

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

    if user_lang == "ru":
        msg = (
            f"🤝 *Реферальная программа*\n\n"
            f"📊 *Ваша статистика:*\n"
            f"• Приглашено: *{stats['total']}*\n"
            f"• Оплатили подписку: *{stats['paid']}*\n"
            f"• Бонусов заработано: *{stats['bonuses_granted'] * 10}* сообщений\n"
            f"• Бонусов осталось: *{bonus}*\n\n"
            f"💡 За каждого оплатившего друга вы получаете *+10 сообщений*.\n\n"
            f"🔗 Ваша ссылка:\n`{ref_link}`"
        )
    elif user_lang == "de":
        msg = (
            f"🤝 *Empfehlungsprogramm*\n\n"
            f"📊 *Ihre Statistik:*\n"
            f"• Eingeladen: *{stats['total']}*\n"
            f"• Haben abonniert: *{stats['paid']}*\n"
            f"• Verdiente Boni: *{stats['bonuses_granted'] * 10}* Nachrichten\n"
            f"• Verbleibende Boni: *{bonus}*\n\n"
            f"💡 Für jeden zahlenden Freund erhalten Sie *+10 Nachrichten*.\n\n"
            f"🔗 Ihr Link:\n`{ref_link}`"
        )
    else:
        msg = (
            f"🤝 *Referral Program*\n\n"
            f"📊 *Your stats:*\n"
            f"• Invited: *{stats['total']}*\n"
            f"• Subscribed: *{stats['paid']}*\n"
            f"• Bonuses earned: *{stats['bonuses_granted'] * 10}* messages\n"
            f"• Bonuses remaining: *{bonus}*\n\n"
            f"💡 For each friend who subscribes you get *+10 messages*.\n\n"
            f"🔗 Your link:\n`{ref_link}`"
        )

    await message.answer(msg, parse_mode="Markdown")


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.message(F.text.in_({"🎨 AI Инструменты", "🎨 AI Tools", "🎨 KI Werkzeuge"}))
async def menu_ai_tools(message: Message):
    lang = await get_user_lang(message.from_user.id)
    if lang == "ru":
        text = "🎨 *AI Инструменты*\n\nВыберите инструмент:"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✂️ Удалить фон (Remove.bg)", callback_data="cv_product_photo")],
            [InlineKeyboardButton(text="📐 Social Media Kit (1:1, 4:5, 9:16)", callback_data="cv_social_kit")],
            [InlineKeyboardButton(text="🔍 Brand Audit (анализ визуала)", callback_data="cv_brand_audit")],
            [InlineKeyboardButton(text="🎬 AI Анимация (MagicHour)", callback_data="cv_ai_video")],
        ])
    elif lang == "de":
        text = "🎨 *KI Werkzeuge*\n\nWählen Sie ein Werkzeug:"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✂️ Hintergrund entfernen (Remove.bg)", callback_data="cv_product_photo")],
            [InlineKeyboardButton(text="📐 Social Media Kit (1:1, 4:5, 9:16)", callback_data="cv_social_kit")],
            [InlineKeyboardButton(text="🔍 Brand Audit (visuelle Analyse)", callback_data="cv_brand_audit")],
            [InlineKeyboardButton(text="🎬 KI Animation (MagicHour)", callback_data="cv_ai_video")],
        ])
    else:
        text = "🎨 *AI Tools*\n\nChoose a tool:"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✂️ Remove Background (Remove.bg)", callback_data="cv_product_photo")],
            [InlineKeyboardButton(text="📐 Social Media Kit (1:1, 4:5, 9:16)", callback_data="cv_social_kit")],
            [InlineKeyboardButton(text="🔍 Brand Audit (visual analysis)", callback_data="cv_brand_audit")],
            [InlineKeyboardButton(text="🎬 AI Animation (MagicHour)", callback_data="cv_ai_video")],
        ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

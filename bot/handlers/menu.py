from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from utils.db import get_user_lang
from utils.i18n import get_text
from utils.config import GEMINI_API_KEY
from bot.handlers.bookings import booking_start

router = Router()

async def get_main_keyboard(user_lang):
    # Row 1: Book, Services
    row1 = [KeyboardButton(text=get_text(user_lang, "menu_book")), KeyboardButton(text=get_text(user_lang, "menu_services"))]
    # Row 2: Portfolio, Channel
    row2 = [KeyboardButton(text=get_text(user_lang, "menu_portfolio")), KeyboardButton(text=get_text(user_lang, "menu_channel"))]
    
    buttons = [row1, row2]
    
    # Reference Photo Button (Row 2 middle or Row 3?)
    if GEMINI_API_KEY:
        ref_btn_text = "🧩 Референс-Фото" if user_lang == "ru" else "🧩 Reference Photo"
        # Insert in new row or append
        buttons.insert(1, [KeyboardButton(text=ref_btn_text)])
    
    # Referral button
    ref_btn_text = "🤝 Рефералы" if user_lang == "ru" else "🤝 Referrals"
    
    # Subscribe / My Plan
    sub_text = "⭐ Подписка" if user_lang == "ru" else "⭐ Subscribe / My Plan"
    
    # AI Tools
    tools_text = "🎨 AI Tools" if user_lang != "de" else "🎨 KI Werkzeuge" # Basic DE support
    if user_lang == "ru": tools_text = "🎨 AI Инструменты"

    buttons.insert(0, [KeyboardButton(text=sub_text)])
    buttons.append([KeyboardButton(text=ref_btn_text), KeyboardButton(text=tools_text)])
    
    # Help row
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
            "📩 Поддержка: @ger_dennis"
        )
    else:
        text = (
            "🆘 *Help*\n\n"
            "📌 Commands:\n"
            "• /mystatus — your subscription & messages left\n"
            "• /newsession — start a new conversation\n"
            "• /start — main menu\n\n"
            "📩 Support: @ger_dennis"
        )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text.in_({"Портфолио", "Portfolio"}))
async def menu_portfolio(message: Message):
    await message.answer("Portfolio: https://t.me/ger_dennis_ai")

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
            f"• Бонусов заработано: *{stats['bonuses_granted'] * 3}* сообщений\n"
            f"• Бонусов осталось: *{bonus}*\n\n"
            f"💡 За каждого оплатившего друга вы получаете *+3 сообщения*.\n\n"
            f"🔗 Ваша ссылка:\n`{ref_link}`"
        )
    elif user_lang == "de":
        msg = (
            f"🤝 *Empfehlungsprogramm*\n\n"
            f"📊 *Ihre Statistik:*\n"
            f"• Eingeladen: *{stats['total']}*\n"
            f"• Haben abonniert: *{stats['paid']}*\n"
            f"• Verdiente Boni: *{stats['bonuses_granted'] * 3}* Nachrichten\n"
            f"• Verbleibende Boni: *{bonus}*\n\n"
            f"💡 Für jeden zahlenden Freund erhalten Sie *+3 Nachrichten*.\n\n"
            f"🔗 Ihr Link:\n`{ref_link}`"
        )
    else:
        msg = (
            f"🤝 *Referral Program*\n\n"
            f"📊 *Your stats:*\n"
            f"• Invited: *{stats['total']}*\n"
            f"• Subscribed: *{stats['paid']}*\n"
            f"• Bonuses earned: *{stats['bonuses_granted'] * 3}* messages\n"
            f"• Bonuses remaining: *{bonus}*\n\n"
            f"💡 For each friend who subscribes you get *+3 messages*.\n\n"
            f"🔗 Your link:\n`{ref_link}`"
        )

    await message.answer(msg, parse_mode="Markdown")

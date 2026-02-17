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
    await message.answer("Support: @ger_dennis\nEmail: contact@example.com")

@router.message(F.text.in_({"Портфолио", "Portfolio"}))
async def menu_portfolio(message: Message):
    await message.answer("Portfolio: https://t.me/ger_dennis_ai")

@router.message(F.text.in_({"Канал", "Channel", "Kanal"}))
async def menu_channel(message: Message):
    await message.answer("Channel: https://t.me/ger_dennis")

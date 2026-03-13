from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.states import UserStates
from aiogram.fsm.context import FSMContext
from utils.i18n import get_text
from utils.db import set_user_lang, has_user, get_user_lang

router = Router()

from aiogram.filters import CommandStart, CommandObject
from utils.db_referrals import add_referral

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    # Capture referral
    referrer_id = None
    if command.args and command.args.startswith("ref_"):
        try:
            referrer_id = int(command.args.split("_")[1])
        except (ValueError, IndexError):
            pass

    if referrer_id:
        await add_referral(referrer_id, message.from_user.id)

    # Reset state
    await state.clear()
    
    user_id = message.from_user.id
    # Check if user exists/has lang
    # Actually, let's always offer lang selection on /start for simplicity?
    # Or if user is known, show menu? 
    # Requirement: "Show on /start and language selection".
    
    # Let's show language selection inline, but ALSO show the keyboard?
    # No, usually lang select -> then menu.
    # But if they type /start later, maybe they want menu.
    
    # Hybrid: Show Lang, and if they pick one, show menu. 
    # But if they already HAVE a language set?
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")],
        [InlineKeyboardButton(text="Deutsch 🇩🇪", callback_data="lang_de")]
    ])
    
    await message.answer(
        "Please select your language / Выберите язык / Bitte wählen Sie Ihre Sprache:",
        reply_markup=kb
    )
    await state.set_state(UserStates.LANGUAGE_SELECT)
    
    # Also attempt to show menu if they ignore lang? 
    # The request says "Show persistent menu... on /start".
    # Creating a reply keyboard AND inline keyboard in one message is impossible.
    # So we send Inline for lang, then maybe text with Reply?
    # Or just wait for lang selection.
    
    # Let's just rely on lang selection to trigger menu show.
    # And if they are an old user, they can re-select lang to get menu.


@router.message(Command("login"))
async def cmd_login(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if await has_user(user_id):
        from bot.handlers.menu import show_main_menu
        await state.clear()
        await show_main_menu(message, user_id)
        return
    await message.answer(
        "You are not logged in yet. Please use /start to select language and begin.",
    )


@router.message(Command("mystatus"))
async def cmd_mystatus(message: Message):
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)

    from utils.subscription import check_subscription
    from utils.db_helpers import get_trial_usage_today, get_bonus_credits
    from utils.config import TRIAL_MAX_MESSAGES, ADMIN_IDS

    # Admin — special status
    if user_id in ADMIN_IDS:
        await message.answer("👑 Admin — full access, no limits." if lang != "ru" else "👑 Администратор — полный доступ, без ограничений.")
        return

    sub_data = await check_subscription(user_id)
    msg_today, _ = await get_trial_usage_today(user_id)
    bonus = await get_bonus_credits(user_id)

    if sub_data["has_subscription"]:
        plan = sub_data["plan"].capitalize()
        remaining = sub_data["daily_remaining"]
        expires_raw = sub_data.get("expires_at", "")
        # Format expiry: "2026-04-12 10:00:00" → "12.04.2026"
        try:
            from datetime import datetime
            exp_dt = datetime.strptime(expires_raw[:10], "%Y-%m-%d")
            exp_str = exp_dt.strftime("%d.%m.%Y")
        except Exception:
            exp_str = expires_raw[:10] if expires_raw else "—"

        if lang == "ru":
            text = (
                f"✅ *Подписка активна* — план {plan}\n\n"
                f"📅 Действует до: *{exp_str}*\n"
                f"💬 Осталось сообщений сегодня: *{remaining}*\n\n"
                f"Для продления: ⭐ Подписка в меню"
            )
        else:
            text = (
                f"✅ *Subscription active* — {plan} plan\n\n"
                f"📅 Valid until: *{exp_str}*\n"
                f"💬 Messages remaining today: *{remaining}*\n\n"
                f"To renew: ⭐ Subscribe in menu"
            )
    else:
        used = msg_today
        total = TRIAL_MAX_MESSAGES + bonus
        left = max(0, total - used)
        bar_filled = min(10, used) * "▓"
        bar_empty = (10 - min(10, used)) * "░"
        if lang == "ru":
            text = (
                f"🆓 *Пробный период*\n\n"
                f"{bar_filled}{bar_empty} {used}/{total}\n\n"
                f"💬 Использовано: *{used}* из {total} сообщений\n"
                f"💬 Осталось: *{left}*\n"
                + (f"🎁 Бонусных сообщений: *{bonus}*\n" if bonus > 0 else "")
                + f"\n💡 Для полного доступа без ограничений:\n👉 ⭐ Подписка в меню"
            )
        else:
            text = (
                f"🆓 *Free trial*\n\n"
                f"{bar_filled}{bar_empty} {used}/{total}\n\n"
                f"💬 Used: *{used}* of {total} messages\n"
                f"💬 Remaining: *{left}*\n"
                + (f"🎁 Bonus credits: *{bonus}*\n" if bonus > 0 else "")
                + f"\n💡 For unlimited access:\n👉 ⭐ Subscribe in menu"
            )

    await message.answer(text, parse_mode="Markdown")

from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import get_user_lang
from utils.i18n import get_text
from utils.config import TRIAL_LIMIT_PER_DAY, ADMIN_IDS
from utils.db_helpers import get_trial_usage_today, increment_trial_photos
from utils.subscription import check_subscription
from bot.ai.gemini_client import merge_reference_photos
from utils.logger import logger
import os
import uuid

router = Router()

# Button labels per language
DONE_LABELS = {"ru": "✅ Готово", "en": "✅ Done", "de": "✅ Fertig"}
CANCEL_LABELS = {"ru": "❌ Отмена", "en": "❌ Cancel", "de": "❌ Abbrechen"}

ALL_DONE_LABELS = set(DONE_LABELS.values()) | {"/done"}
ALL_CANCEL_LABELS = set(CANCEL_LABELS.values()) | {"/cancel"}


def get_photo_keyboard(lang: str) -> ReplyKeyboardMarkup:
    done = DONE_LABELS.get(lang, "✅ Done")
    cancel = CANCEL_LABELS.get(lang, "❌ Cancel")
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=done), KeyboardButton(text=cancel)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_intro_text(lang: str) -> str:
    texts = {
        "ru": (
            "🎨 *Арт по стилю фото*\n\n"
            "Как это работает:\n"
            "1️⃣ Отправьте 1-14 референсных фото\n"
            "2️⃣ Напишите, какой результат нужен: постер, обложка, аватар, баннер, moodboard\n"
            "3️⃣ AI выделит стиль, цвет, свет, композицию и создаст новое премиальное изображение через DALL-E 3 HD\n\n"
            "💡 *Подсказки для промпта:*\n"
            "• Стиль: editorial, cinematic, минимализм, поп-арт\n"
            "• Атмосфера: тёмная, тёплая, неоновая, пастельная\n"
            "• Формат: постер, обложка, баннер, аватар\n\n"
            "⚠️ Важно: это не копирование лица и не face swap. Инструмент делает новый арт по стилю ваших фото, чтобы результат был честным и стабильным.\n\n"
            "Когда загрузите все фото — нажмите *✅ Готово*"
        ),
        "en": (
            "🎨 *Photo Style Art*\n\n"
            "How it works:\n"
            "1️⃣ Send 1-14 reference photos\n"
            "2️⃣ Describe the result: poster, cover, avatar, banner, moodboard\n"
            "3️⃣ AI extracts style, colors, light, composition and generates a new premium image via DALL-E 3 HD\n\n"
            "💡 *Prompt tips:*\n"
            "• Style: editorial, cinematic, minimalist, pop-art\n"
            "• Mood: dark, warm, neon, pastel\n"
            "• Format: poster, cover, banner, avatar\n\n"
            "⚠️ Important: this is not face copying or face swap. It creates new style-inspired art so the result stays honest and stable.\n\n"
            "When done uploading — tap *✅ Done*"
        ),
        "de": (
            "🎨 *Foto-Stil-Art*\n\n"
            "So funktioniert es:\n"
            "1️⃣ Senden Sie 1-14 Referenzfotos\n"
            "2️⃣ Beschreiben Sie das Ergebnis: Poster, Cover, Avatar, Banner, Moodboard\n"
            "3️⃣ KI extrahiert Stil, Farben, Licht, Komposition und generiert ein neues Premiumbild via DALL-E 3 HD\n\n"
            "💡 *Prompt-Tipps:*\n"
            "• Stil: Editorial, Cinematic, Minimalistisch, Pop-Art\n"
            "• Stimmung: dunkel, warm, Neon, Pastell\n"
            "• Format: Poster, Cover, Banner, Avatar\n\n"
            "⚠️ Wichtig: Das ist kein Gesichtskopieren und kein Face Swap. Das Tool erstellt neue stilinspirierte Kunst, damit das Ergebnis ehrlich und stabil bleibt.\n\n"
            "Wenn Sie fertig sind — tippen Sie auf *✅ Fertig*"
        ),
    }
    return texts.get(lang, texts["en"])


def get_status_text(lang: str, count: int) -> str:
    texts = {
        "ru": f"📸 Получено фото: *{count}* {'из макс. 14' if count < 14 else '(максимум)'}\n\nОтправьте ещё или нажмите *✅ Готово*",
        "en": f"📸 Photos received: *{count}* {'of max 14' if count < 14 else '(maximum)'}\n\nSend more or tap *✅ Done*",
        "de": f"📸 Fotos erhalten: *{count}* {'von max. 14' if count < 14 else '(Maximum)'}\n\nSenden Sie mehr oder tippen Sie auf *✅ Fertig*",
    }
    return texts.get(lang, texts["en"])


@router.message(F.text.in_({
    "🎨 Арт по стилю фото", "🎨 Photo Style Art", "🎨 Foto-Stil-Art",
    "🎨 AI Концепт", "🎨 AI Concept", "🎨 AI Konzept",
    "🧩 Референс-Фото", "🧩 Reference Photo", "🧩 Referenzfoto"
}))
async def ref_photo_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)

    # Check access
    if user_id not in ADMIN_IDS:
        sub_data = await check_subscription(user_id)
        is_paid = sub_data["has_subscription"]
        if not is_paid:
            _, photo_count = await get_trial_usage_today(user_id)
            if photo_count >= TRIAL_LIMIT_PER_DAY:
                await message.answer(get_text(lang, "ref_photo_limit"))
                return

    await state.set_state(UserStates.REF_PHOTO_COLLECT)
    await state.update_data(ref_photos=[], ref_prompt="")

    await message.answer(
        get_intro_text(lang),
        reply_markup=get_photo_keyboard(lang),
        parse_mode="Markdown"
    )


@router.message(UserStates.REF_PHOTO_COLLECT, F.photo)
async def ref_photo_collect(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    data = await state.get_data()
    photos = data.get("ref_photos", [])

    if len(photos) >= 14:
        await message.answer(
            "⚠️ Максимум 14 фото. Нажмите ✅ Готово для обработки." if lang == "ru"
            else "⚠️ Maximum 14 photos. Tap ✅ Done to process."
        )
        return

    photos.append(message.photo[-1].file_id)

    if message.caption:
        prompt = data.get("ref_prompt", "")
        await state.update_data(ref_photos=photos, ref_prompt=prompt + f" {message.caption}")
    else:
        await state.update_data(ref_photos=photos)

    await message.answer(
        get_status_text(lang, len(photos)),
        reply_markup=get_photo_keyboard(lang),
        parse_mode="Markdown"
    )


@router.message(UserStates.REF_PHOTO_COLLECT, F.text & ~F.text.in_(ALL_DONE_LABELS | ALL_CANCEL_LABELS))
async def ref_photo_text(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    data = await state.get_data()
    prompt = data.get("ref_prompt", "") + f" {message.text}"
    await state.update_data(ref_prompt=prompt)

    photos = data.get("ref_photos", [])
    added_texts = {
        "ru": f"✏️ Описание добавлено.\n\n{get_status_text('ru', len(photos))}",
        "en": f"✏️ Description added.\n\n{get_status_text('en', len(photos))}",
        "de": f"✏️ Beschreibung hinzugefügt.\n\n{get_status_text('de', len(photos))}",
    }
    await message.answer(
        added_texts.get(lang, added_texts["en"]),
        reply_markup=get_photo_keyboard(lang),
        parse_mode="Markdown"
    )


@router.message(UserStates.REF_PHOTO_COLLECT, F.text.in_(ALL_DONE_LABELS))
async def ref_photo_done(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)
    data = await state.get_data()
    photos = data.get("ref_photos", [])
    prompt = data.get("ref_prompt", "")

    if len(photos) == 0:
        no_photo_text = {
            "ru": "📸 Сначала отправьте хотя бы одно фото.",
            "en": "📸 Please send at least one photo first.",
            "de": "📸 Bitte senden Sie zuerst mindestens ein Foto.",
        }
        await message.answer(no_photo_text.get(lang, no_photo_text["en"]))
        return

    # Check limit for non-admin
    if user_id not in ADMIN_IDS:
        sub_data = await check_subscription(user_id)
        is_paid = sub_data["has_subscription"]
        if not is_paid:
            _, photo_count = await get_trial_usage_today(user_id)
            if photo_count >= TRIAL_LIMIT_PER_DAY:
                await message.answer(get_text(lang, "ref_photo_limit"))
                await state.clear()
                from bot.handlers.menu import show_main_menu
                await show_main_menu(message, user_id)
                return
            await increment_trial_photos(user_id)

    processing_texts = {
        "ru": f"⏳ Обрабатываю {len(photos)} фото... Это займёт около минуты, подождите.",
        "en": f"⏳ Processing {len(photos)} photo(s)... This takes about a minute, please wait.",
        "de": f"⏳ Verarbeite {len(photos)} Foto(s)... Das dauert etwa eine Minute, bitte warten.",
    }

    from aiogram.types import ReplyKeyboardRemove
    status_msg = await message.answer(
        processing_texts.get(lang, processing_texts["en"]),
        reply_markup=ReplyKeyboardRemove()
    )

    temp_files = []
    try:
        temp_dir = os.path.join("data", "temp_photos")
        os.makedirs(temp_dir, exist_ok=True)

        for file_id in photos:
            file = await bot.get_file(file_id)
            file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.jpg")
            await bot.download_file(file.file_path, file_path)
            temp_files.append(file_path)

        result_image_url = await merge_reference_photos(temp_files, prompt)

        await status_msg.delete()

        captions = {
            "ru": "✅ Готово! Это арт по стилю ваших фото: цвет, настроение, свет и композиция. Это не копия лица.",
            "en": "✅ Done! This is style-inspired art based on your photos: color, mood, light and composition. It is not a face copy.",
            "de": "✅ Fertig! Das ist stilinspirierte Kunst nach Ihren Fotos: Farbe, Stimmung, Licht und Komposition. Es ist keine Gesichtskopie.",
        }
        await message.answer_photo(
            result_image_url,
            caption=captions.get(lang, captions["en"])
        )

    except Exception as e:
        err_msg = str(e)
        logger.exception("Ref Photo Failed")
        await status_msg.delete()

        if "Quota" in err_msg or "429" in err_msg:
            quota_texts = {
                "ru": "⚠️ Сервис перегружен. Попробуйте через несколько минут.",
                "en": "⚠️ Service is busy right now. Please try again in a few minutes.",
                "de": "⚠️ Dienst ist gerade ausgelastet. Bitte versuchen Sie es in einigen Minuten erneut.",
            }
            await message.answer(quota_texts.get(lang, quota_texts["en"]))
        else:
            error_texts = {
                "ru": "❌ Ошибка при обработке. Попробуйте ещё раз.",
                "en": "❌ Processing failed. Please try again.",
                "de": "❌ Verarbeitung fehlgeschlagen. Bitte versuchen Sie es erneut.",
            }
            await message.answer(error_texts.get(lang, error_texts["en"]))
    finally:
        for p in temp_files:
            try:
                os.remove(p)
            except Exception:
                pass
        await state.clear()
        from bot.handlers.menu import show_main_menu
        await show_main_menu(message, user_id)


@router.message(UserStates.REF_PHOTO_COLLECT, F.text.in_(ALL_CANCEL_LABELS))
async def ref_photo_cancel(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    cancel_texts = {
        "ru": "Отменено. Возвращаюсь в меню.",
        "en": "Cancelled. Returning to menu.",
        "de": "Abgebrochen. Zurück zum Menü.",
    }
    await state.clear()
    await message.answer(cancel_texts.get(lang, cancel_texts["en"]))
    from bot.handlers.menu import show_main_menu
    await show_main_menu(message, message.from_user.id)

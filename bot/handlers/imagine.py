from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from utils.db import get_user_lang
from utils.config import ADMIN_IDS
from utils.subscription import check_subscription
from utils.db_helpers import get_trial_usage_today
from utils.config import FREE_DAILY_MESSAGES
from utils.logger import logger

router = Router()


@router.message(Command("imagine"))
async def cmd_imagine(message: Message):
    user_id = message.from_user.id
    lang = await get_user_lang(user_id)

    # Extract prompt after /imagine
    prompt = message.text.replace("/imagine", "", 1).strip()
    if not prompt:
        hint = {
            "ru": "🎨 Напишите описание после команды:\n`/imagine красивый закат над морем`",
            "en": "🎨 Add a description after the command:\n`/imagine beautiful sunset over the ocean`",
            "de": "🎨 Fügen Sie eine Beschreibung nach dem Befehl hinzu:\n`/imagine schöner Sonnenuntergang über dem Meer`",
        }
        await message.answer(hint.get(lang, hint["en"]), parse_mode="Markdown")
        return

    # Check access (paid or admin)
    if user_id not in ADMIN_IDS:
        sub_data = await check_subscription(user_id)
        if not sub_data["has_subscription"]:
            msg = {
                "ru": "🔒 Генерация изображений доступна только на платных тарифах.\n\n⭐ Оформите подписку в меню.",
                "en": "🔒 Image generation is available on paid plans only.\n\n⭐ Subscribe in menu.",
                "de": "🔒 Bildgenerierung ist nur in kostenpflichtigen Plänen verfügbar.\n\n⭐ Abonnieren Sie im Menü.",
            }
            await message.answer(msg.get(lang, msg["en"]))
            return

    processing = {
        "ru": "🎨 Генерирую изображение по вашему описанию... (~30 сек)",
        "en": "🎨 Generating image from your description... (~30 sec)",
        "de": "🎨 Generiere Bild nach Ihrer Beschreibung... (~30 Sek.)",
    }
    status_msg = await message.answer(processing.get(lang, processing["en"]))

    try:
        from bot.ai.openai_client import client as openai_client
        if not openai_client:
            await status_msg.edit_text("❌ OpenAI API not configured.")
            return

        response = await openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt[:4000],
            size="1024x1024",
            quality="hd",
            n=1,
        )
        image_url = response.data[0].url

        await status_msg.delete()
        caption = {
            "ru": f"🎨 *Готово!*\n\n_{prompt[:200]}_",
            "en": f"🎨 *Done!*\n\n_{prompt[:200]}_",
            "de": f"🎨 *Fertig!*\n\n_{prompt[:200]}_",
        }
        await message.answer_photo(
            image_url,
            caption=caption.get(lang, caption["en"]),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception("DALL-E 3 /imagine failed")
        err = {
            "ru": "❌ Не удалось сгенерировать. Попробуйте другое описание.",
            "en": "❌ Generation failed. Try a different description.",
            "de": "❌ Generierung fehlgeschlagen. Versuchen Sie eine andere Beschreibung.",
        }
        await status_msg.edit_text(err.get(lang, err["en"]))

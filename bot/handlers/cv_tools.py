import os
import io
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from bot.ai.gemini_client import brand_audit
from bot.ai.removebg_client import remove_background
from bot.ai.magichour_client import generate_animation
from utils.db import get_user_lang
from utils.logger import logger
from utils.subscription import check_subscription
from PIL import Image
import numpy as np

router = Router()

# Download helper
async def download_photo(message: Message, bot: Bot) -> str:
    photo = message.photo[-1]
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = f"temp_{file_id}.jpg"
    await bot.download_file(file.file_path, file_path)
    return file_path

def get_cancel_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Cancel / Назад")]], resize_keyboard=True)

@router.message(F.text == "🔙 Cancel / Назад")
async def cancel_cv_action(message: Message, state: FSMContext):
    await state.clear()
    from bot.handlers.menu import show_main_menu
    await message.answer("🛑", reply_markup=ReplyKeyboardRemove())
    await show_main_menu(message, message.from_user.id)

# Menus Route - Wait for photo
@router.callback_query(F.data == "cv_brand_audit")
async def start_brand_audit(call: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.CV_BRAND_AUDIT)
    lang = await get_user_lang(call.from_user.id)
    msg = "Please send 1 photo for Brand Audit." if lang != "ru" else "Отправьте 1 фото для Brand Audit."
    await call.message.answer(msg, reply_markup=get_cancel_kb())
    await call.answer()

@router.callback_query(F.data == "cv_product_photo")
async def start_product_photo(call: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.CV_PRODUCT_PHOTO)
    lang = await get_user_lang(call.from_user.id)
    msg = "Please send 1 photo for AI Background Removal." if lang != "ru" else "Отправьте 1 фото для удаления фона."
    await call.message.answer(msg, reply_markup=get_cancel_kb())
    await call.answer()

@router.callback_query(F.data == "cv_social_kit")
async def start_social_kit(call: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.CV_SOCIAL_KIT)
    lang = await get_user_lang(call.from_user.id)
    msg = "Please send 1 photo. We will resize it for Social Media (1:1, 4:5, 9:16)." if lang != "ru" else "Отправьте 1 фото для нарезки Social Kit (1:1, 4:5, 9:16)."
    await call.message.answer(msg, reply_markup=get_cancel_kb())
    await call.answer()

@router.callback_query(F.data == "cv_ai_video")
async def start_ai_video(call: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.CV_AI_VIDEO)
    lang = await get_user_lang(call.from_user.id)
    msg = "Please send 1 photo to animate via MagicHour." if lang != "ru" else "Отправьте 1 фото для анимации через MagicHour."
    await call.message.answer(msg, reply_markup=get_cancel_kb())
    await call.answer()

# Brand Audit Handler
@router.message(UserStates.CV_BRAND_AUDIT, F.photo)
async def process_brand_audit(message: Message, state: FSMContext, bot: Bot):
    await message.answer("Analyzing your brand visual... ⏳")
    file_path = await download_photo(message, bot)
    try:
        sub = await check_subscription(message.from_user.id)
        has_pro = "advanced_cv" in sub.get("features", [])
        
        # 1. Local Free Analysis
        img = Image.open(file_path).convert('RGB')
        
        # Aspect Ratio
        w, h = img.size
        aspect = f"{w}:{h} ({round(w/h, 2)})"
        
        # Brightness & Contrast
        img_gray = img.convert('L')
        arr_gray = np.array(img_gray)
        brightness = int(np.mean(arr_gray))
        contrast = int(np.std(arr_gray))
        
        # Palette (Top 5 colors via quantization)
        q_img = img.quantize(colors=16).convert('RGB')
        colors = q_img.getcolors()
        if colors:
            colors.sort(key=lambda x: x[0], reverse=True)
            top_5 = colors[:5]
            palette = ", ".join([f"#{c[1][0]:02x}{c[1][1]:02x}{c[1][2]:02x}" for c in top_5])
        else:
            palette = "N/A"
            
        # Composition weight
        cx, cy = w//2, h//2
        q1 = np.mean(arr_gray[:cy, :cx]) # Top-Left
        q2 = np.mean(arr_gray[:cy, cx:]) # Top-Right
        q3 = np.mean(arr_gray[cy:, :cx]) # Bottom-Left
        q4 = np.mean(arr_gray[cy:, cx:]) # Bottom-Right
        q_max = max(q1, q2, q3, q4)
        if q_max == q1: comp = "Top-Left (Visual weight)"
        elif q_max == q2: comp = "Top-Right ((Visual weight)"
        elif q_max == q3: comp = "Bottom-Left (Visual weight)"
        else: comp = "Bottom-Right (Visual weight)"
        
        free_analysis = (
            f"📊 **Base Visual Metrics**\n"
            f"• Aspect Ratio: {aspect}\n"
            f"• Brightness (0-255): {brightness}\n"
            f"• Contrast (0-255): {contrast}\n"
            f"• Dominant Colors: {palette}\n"
            f"• Heaviest Quadrant: {comp}\n\n"
        )
        img.close()
        
        if has_pro:
            await message.answer(free_analysis + "🧠 Starting Deep AI Analysis (Pro/Business)...")
            response_text = await brand_audit(file_path)
            await message.answer(response_text)
        else:
            await message.answer(free_analysis + "⭐ Upgrade to Pro for deep Gemini AI subjective analysis and improvement recommendations.")
            
    except Exception as e:
        logger.exception("Brand Audit failed.")
        await message.answer("❌ Error during Brand Audit.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    await state.clear()
    
    # Show main menu since task is complete
    from bot.handlers.menu import show_main_menu
    await message.answer("✨", reply_markup=ReplyKeyboardRemove())
    await show_main_menu(message, message.from_user.id)

# Product Photo (Remove.bg) Handler
@router.message(UserStates.CV_PRODUCT_PHOTO, F.photo)
async def process_product_photo(message: Message, state: FSMContext, bot: Bot):
    await message.answer("Removing background... ✂️")
    file_path = await download_photo(message, bot)
    try:
        with open(file_path, "rb") as f:
            image_data = f.read()

        no_bg_data = await remove_background(image_data)
        if no_bg_data:
            file = BufferedInputFile(no_bg_data, filename="product.png")
            await message.bot.send_document(message.chat.id, document=file, caption="Background removed! ✅")
        else:
            await message.answer("❌ Background removal failed.")
    except Exception as e:
        logger.exception("Remove.bg processing failed")
        lang = await get_user_lang(message.from_user.id)
        err = {"ru": "❌ Не удалось обработать фото. Попробуйте другое.", "de": "❌ Foto konnte nicht verarbeitet werden."}.get(lang, "❌ Failed to process photo. Try another one.")
        await message.answer(err)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    await state.clear()
    from bot.handlers.menu import show_main_menu
    await message.answer("✨", reply_markup=ReplyKeyboardRemove())
    await show_main_menu(message, message.from_user.id)

# Social Kit (Pillow crops) Handler
@router.message(UserStates.CV_SOCIAL_KIT, F.photo)
async def process_social_kit(message: Message, state: FSMContext, bot: Bot):
    await message.answer("Generating Social Media Kit... 📐")
    file_path = await download_photo(message, bot)
    try:
        img = Image.open(file_path)
        medias = []
        
        # Helper to crop by aspect ratio
        def crop_aspect(image, ratio_w, ratio_h):
            w, h = image.size
            target_ratio = ratio_w / ratio_h
            current_ratio = w / h
            
            if current_ratio > target_ratio:
                # Image is wider: crop width
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                return image.crop((left, 0, left + new_w, h))
            else:
                # Image is taller: crop height
                new_h = int(w / target_ratio)
                top = (h - new_h) // 2
                return image.crop((0, top, w, top + new_h))
                
        def pil_to_bytes(pil_img):
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG")
            return buf.getvalue()

        # 1:1, 4:5, 9:16
        img_1_1 = crop_aspect(img, 1, 1)
        img_4_5 = crop_aspect(img, 4, 5)
        img_9_16 = crop_aspect(img, 9, 16)
        
        medias.append(InputMediaPhoto(media=BufferedInputFile(pil_to_bytes(img_1_1), filename="1_1.jpg"), caption="1:1 (Insta Square)"))
        medias.append(InputMediaPhoto(media=BufferedInputFile(pil_to_bytes(img_4_5), filename="4_5.jpg"), caption="4:5 (Insta Portrait)"))
        medias.append(InputMediaPhoto(media=BufferedInputFile(pil_to_bytes(img_9_16), filename="9_16.jpg"), caption="9:16 (Stories/Reels)"))
        
        await message.bot.send_media_group(message.chat.id, media=medias)
        img.close()
    except Exception as e:
        logger.exception("Social Kit failed")
        await message.answer(f"❌ Failed to process Social Kit: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    await state.clear()
    from bot.handlers.menu import show_main_menu
    await message.answer("✨", reply_markup=ReplyKeyboardRemove())
    await show_main_menu(message, message.from_user.id)

# AI Video (MagicHour) Handler
@router.message(UserStates.CV_AI_VIDEO, F.photo)
async def process_ai_video(message: Message, state: FSMContext, bot: Bot):
    _start_msg = {
        "ru": "🎬 Отправляю в MagicHour для анимации. Это займёт 2-5 минут, подождите...",
        "en": "🎬 Sending to MagicHour for animation. This takes 2-5 minutes, please wait...",
        "de": "🎬 Wird an MagicHour gesendet. Das dauert 2-5 Minuten, bitte warten...",
    }
    user_lang_pre = await get_user_lang(message.from_user.id)
    await message.answer(_start_msg.get(user_lang_pre, _start_msg["en"]))
    file_path = await download_photo(message, bot)
    user_lang = await get_user_lang(message.from_user.id)
    _timeout_text = {
        "ru": "⏱ Генерация видео заняла слишком долго (лимит 5 мин). Попробуйте другое фото или позже.",
        "en": "⏱ Video generation timed out (5 min limit). Try a different photo or try later.",
        "de": "⏱ Videogenerierung hat zu lange gedauert (5 Min. Limit). Versuchen Sie ein anderes Foto.",
    }
    _fail_text = {
        "ru": "❌ Не удалось сгенерировать видео. Попробуйте другое фото.",
        "en": "❌ Video generation failed. Try a different photo.",
        "de": "❌ Videogenerierung fehlgeschlagen. Versuche ein anderes Foto.",
    }
    try:
        video_path = await generate_animation(file_path)
        if video_path and os.path.exists(video_path):
            from aiogram.types import FSInputFile
            await message.answer_video(FSInputFile(video_path), caption="🎬 Your MagicHour Animation")
            os.remove(video_path)
        else:
            await message.answer(_fail_text.get(user_lang, _fail_text["en"]))
    except TimeoutError:
        await message.answer(_timeout_text.get(user_lang, _timeout_text["en"]))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    await state.clear()
    from bot.handlers.menu import show_main_menu
    await message.answer("✨", reply_markup=ReplyKeyboardRemove())
    await show_main_menu(message, message.from_user.id)

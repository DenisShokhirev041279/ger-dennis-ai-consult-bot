from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from bot.states import UserStates
from utils.db import get_user_lang, get_session_info
from utils.i18n import get_text
from utils.config import TRIAL_LIMIT_PER_DAY
from utils.db_helpers import get_trial_usage_today, increment_trial_photos
from bot.ai.gemini_client import merge_reference_photos
from utils.logger import logger
import os

router = Router()

@router.message(F.text.in_({"🧩 Референс-Фото", "🧩 Reference Photo"}))
async def ref_photo_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)
    
    # Check Trial Limit
    session = await get_session_info(user_id)
    from utils.config import ADMIN_IDS
    is_paid = (session and session[2]) or user_id in ADMIN_IDS
    
    if not is_paid:
        _, photo_count = await get_trial_usage_today(user_id)
        if photo_count >= TRIAL_LIMIT_PER_DAY:
             await message.answer(get_text(user_lang, "ref_photo_limit") or "Daily limit reached.")
             return

    await state.set_state(UserStates.REF_PHOTO_COLLECT)
    await state.update_data(ref_photos=[], ref_prompt="")
    
    await message.answer(
        get_text(user_lang, "ref_photo_intro") or "Send 2-14 photos. Then /done. /cancel to quit.",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(UserStates.REF_PHOTO_COLLECT, F.photo)
async def ref_photo_collect(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("ref_photos", [])
    
    # Store largest photo file_id
    photos.append(message.photo[-1].file_id)
    
    # If caption present, append to prompt
    prompt = data.get("ref_prompt", "")
    if message.caption:
        prompt += f" {message.caption}"
        
    await state.update_data(ref_photos=photos, ref_prompt=prompt)
    await message.answer(f"Received {len(photos)} photos. Send more or /done.")

@router.message(UserStates.REF_PHOTO_COLLECT, F.text, ~F.text.in_({"/done", "/cancel", "🔙 Cancel / Назад"}))
async def ref_photo_text(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt = data.get("ref_prompt", "")
    prompt += f" {message.text}"
    await state.update_data(ref_prompt=prompt)
    await message.answer("Text context added. Send more photos or /done.")

@router.message(UserStates.REF_PHOTO_COLLECT, F.text.casefold() == "/done")
async def ref_photo_done(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_lang = await get_user_lang(user_id)
    data = await state.get_data()
    photos = data.get("ref_photos", [])
    prompt = data.get("ref_prompt", "")
    
    if not (2 <= len(photos) <= 14):
        await message.answer(get_text(user_lang, "ref_photo_error_count") or "Need 2-14 photos.")
        return

    # Check limit again just in case
    session = await get_session_info(user_id)
    from utils.config import ADMIN_IDS
    is_paid = (session and session[2]) or user_id in ADMIN_IDS
    if not is_paid:
        _, photo_count = await get_trial_usage_today(user_id)
        if photo_count >= TRIAL_LIMIT_PER_DAY:
             await message.answer(get_text(user_lang, "ref_photo_limit"))
             await state.clear()
             return
        await increment_trial_photos(user_id)

    status_msg = await message.answer(get_text(user_lang, "ref_photo_done") or "Processing...")
    
    # Download photos
    temp_files = []
    try:
        import uuid
        temp_dir = "temp_photos"
        os.makedirs(temp_dir, exist_ok=True)
        
        for file_id in photos:
            file = await bot.get_file(file_id)
            file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.jpg")
            await bot.download_file(file.file_path, file_path)
            temp_files.append(file_path)
            
        # Call Gemini Logic
        result_image_url = await merge_reference_photos(temp_files, prompt)
        
        await message.answer_photo(result_image_url, caption="✅ Merged Result (NanoBanana Pro)")
        
    except Exception as e:
        err_msg = str(e)
        logger.exception("Ref Photo Failed")
        if "Quota" in err_msg or "429" in err_msg:
            await message.answer("⚠️ NanoBanana Pro is currently busy (Quota Exceeded). Please try again in a few minutes.")
        else:
            await message.answer("❌ Error processing request. Please try again.")
    finally:
        # Cleanup
        for p in temp_files:
            if os.path.exists(p):
                os.remove(p)
        await status_msg.delete()
        await state.clear()
        
        # Restore menu? (Handled by menu command or next interaction)
        from bot.handlers.menu import show_main_menu
        await show_main_menu(message, user_id)

@router.message(UserStates.REF_PHOTO_COLLECT, F.text.casefold() == "/cancel")
async def ref_photo_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Cancelled.")
    from bot.handlers.menu import show_main_menu
    await show_main_menu(message, message.from_user.id)

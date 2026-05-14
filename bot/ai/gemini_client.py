import google.genai as genai
import os
import base64
from utils.config import GEMINI_API_KEY
from utils.logger import logger
from bot.ai.openai_client import client as openai_client

_client = None

if GEMINI_API_KEY:
    try:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Gemini Client init failed: {e}")
else:
    logger.warning("GEMINI_API_KEY is not set. Vision features will fail.")


async def merge_reference_photos(image_paths: list[str], user_prompt: str = "") -> str | bytes:
    """
    AI Style Art Generator:
    1. Analyzes reference images with Gemini Vision.
    2. Extracts style, mood, color palette, composition elements.
    3. Generates a creative style-inspired visual via DALL-E 3.

    Note: This creates a style/mood concept, not an identity-preserving portrait.
    """
    if not _client:
        raise Exception("Gemini API Key missing")

    try:
        import PIL.Image

        pil_images = []
        for path in image_paths:
            try:
                img = PIL.Image.open(path)
                pil_images.append(img)
            except Exception as e:
                logger.error(f"Failed to open image {path}: {e}")
                continue

        if len(pil_images) < 1:
            raise ValueError("Need at least 1 valid image for concept generation.")

        if user_prompt.strip():
            user_context = f"\nUser's creative direction: {user_prompt}\nEnhance and expand this direction while staying true to the user's intent."
        else:
            user_context = "\nNo specific direction given — create the most visually striking concept possible from the reference images."
        merge_prompt = (
            "You are a world-class art director creating a DALL-E 3 prompt from reference images.\n\n"
            "IMPORTANT PRODUCT RULE: this is NOT an identity-preserving portrait tool. "
            "Create a premium style-inspired artwork/moodboard, not a fake copy of a real person.\n\n"
            "Analyze the reference images. Extract:\n"
            "- Visual style (photorealistic, cinematic, editorial, artistic, etc.)\n"
            "- Color palette (dominant colors, mood, temperature)\n"
            "- Composition (layout, lighting, atmosphere)\n"
            "- Textures, materials, key visual elements\n"
            "- Overall mood and emotional feel\n\n"
            f"{user_context}\n\n"
            "Write a premium DALL-E 3 prompt that synthesizes these elements into one stunning image for social media. "
            "Be specific: subject type, composition, lighting setup, camera angle, art direction, color grading. "
            "If people appear, describe only generic roles/silhouettes/poses, not identity. "
            "Avoid generic words like beautiful, cool, amazing. "
            "Output ONLY the prompt. Maximum 800 characters."
        )

        try:
            response = await _client.aio.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=pil_images + [merge_prompt],
            )
            generated_prompt = response.text
            logger.info(f"Gemini NanoBanana Pro Prompt: {generated_prompt[:100]}...")
        except Exception as gemini_error:
            logger.exception("Gemini 1.5 Pro Generation Failed")
            if "quota" in str(gemini_error).lower():
                raise Exception("NanoBanana Pro Quota Exceeded. Please try again later.")
            raise gemini_error

        try:
            image_model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
            image_quality = os.getenv("OPENAI_IMAGE_QUALITY", "medium")
            image_args = {
                "model": image_model,
                "prompt": generated_prompt[:4000],
                "size": "1024x1024",
                "n": 1,
            }
            if image_model.startswith("gpt-image"):
                image_args["quality"] = image_quality
            else:
                image_args["quality"] = "hd"

            dalle_response = await openai_client.images.generate(
                **image_args,
            )
            image_data = dalle_response.data[0]
            if getattr(image_data, "b64_json", None):
                return base64.b64decode(image_data.b64_json)
            if getattr(image_data, "url", None):
                return image_data.url
            raise Exception("Image generation returned no image data.")
        except Exception as dalle_error:
            logger.exception("OpenAI Image Generation Failed")
            raise Exception("Image Generation Service Unavailable.")

    except Exception as e:
        logger.exception("NanoBanana Pro Merge Failed")
        raise e
    finally:
        for img in pil_images:
            if hasattr(img, 'close'):
                img.close()


async def brand_audit(image_path: str) -> str:
    """Analyzes an image to provide a brand audit using Gemini Vision."""
    if not _client:
        return "⚠️ Gemini API key is missing."

    try:
        import PIL.Image
        img = PIL.Image.open(image_path)

        prompt = (
            "You are a senior brand strategist, creative director, and conversion-focused social media producer.\n"
            "Audit this visual for Telegram, Instagram, LinkedIn, YouTube thumbnail, and paid ad usage.\n\n"
            "Return a practical report in the user's likely language if recognizable; otherwise English.\n"
            "Use this exact structure:\n\n"
            "🔍 VISUAL SCORE: <0-100>\n"
            "One-line verdict: <direct verdict>\n\n"
            "📊 SCORECARD\n"
            "• Clarity: <0-10> — <why>\n"
            "• Trust / premium feel: <0-10> — <why>\n"
            "• Composition: <0-10> — <why>\n"
            "• Scroll-stopping power: <0-10> — <why>\n"
            "• Conversion readiness: <0-10> — <why>\n\n"
            "🚨 TOP 3 PROBLEMS\n"
            "1. <specific problem>\n"
            "2. <specific problem>\n"
            "3. <specific problem>\n\n"
            "✅ 3 FIXES BEFORE POSTING\n"
            "1. <specific edit>\n"
            "2. <specific edit>\n"
            "3. <specific edit>\n\n"
            "📱 BEST USE\n"
            "• Best platform/format: <platform + format>\n"
            "• Caption angle: <short angle>\n"
            "• CTA: <short CTA>\n\n"
            "Be strict. Do not flatter. Give concrete fixes a non-designer can execute."
        )

        response = await _client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[img, prompt],
        )

        if hasattr(img, 'close'):
            img.close()

        return response.text
    except Exception as e:
        logger.exception("Brand Audit failed.")
        return f"❌ Analysis failed: {e}"

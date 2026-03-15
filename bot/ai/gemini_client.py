import google.genai as genai
import os
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


async def merge_reference_photos(image_paths: list[str], user_prompt: str = "") -> str:
    """
    NanoBanana Pro Implementation:
    1. Uploads 2-14 images to Gemini 1.5 Pro.
    2. Asks for a high-quality DALL-E 3 prompt to merge them.
    3. Generates the final image via DALL-E 3.
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
            raise ValueError("Need at least 1 valid image for merge.")

        merge_prompt = (
            "Analyze these reference images. "
            "Create a detailed image generation prompt that merges these concepts into one consistent, high-quality image. "
            "Preserve identity, style, and consistency. "
            f"Additional User Instructions: {user_prompt} "
            "Output ONLY the prompt for the image generator, nothing else. "
            "Focus on photorealism and high detail."
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
            dalle_response = await openai_client.images.generate(
                model="dall-e-3",
                prompt=generated_prompt[:4000],
                size="1024x1024",
                quality="hd",
                n=1,
            )
            image_url = dalle_response.data[0].url
            return image_url
        except Exception as dalle_error:
            logger.exception("DALL-E 3 Generation Failed")
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
            "You are a top-tier Brand Strategist and Marketing Director. "
            "Please perform a critical Brand Audit on this image. "
            "Analyze the visual identity, color palette, typography, composition, and emotional impact. "
            "Provide actionable suggestions for improvement in 3-4 short, punchy paragraphs."
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

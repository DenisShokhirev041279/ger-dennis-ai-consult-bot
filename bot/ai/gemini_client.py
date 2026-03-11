import google.generativeai as genai
import os
import asyncio
from utils.config import GEMINI_API_KEY
from utils.logger import logger
from bot.ai.openai_client import client as openai_client

# Initialize Gemini Client
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Gemini Configuration Failed: {e}")
else:
    logger.warning("GEMINI_API_KEY is not set. Vision features will fail.")

async def merge_reference_photos(image_paths: list[str], user_prompt: str = "") -> str:
    """
    NanoBanana Pro Implementation:
    1. Uploads 2-14 images to Gemini 1.5 Pro.
    2. Asks for a high-quality DALL-E 3 prompt to merge them.
    3. Generates the final image via DALL-E 3.
    """
    
    if not GEMINI_API_KEY:
        raise Exception("Gemini API Key missing")

    temp_files_to_delete = []

    try:
        # Load images for Gemini
        import PIL.Image
        
        pil_images = []
        for path in image_paths:
            try:
                img = PIL.Image.open(path)
                pil_images.append(img)
            except Exception as e:
                logger.error(f"Failed to open image {path}: {e}")
                # Continue if we have at least 2
                continue
                
        if len(pil_images) < 1:
            raise ValueError("Need at least 1 valid image for merge.")

        # 1. Analyze with Gemini 1.5 Pro (NanoBanana Pro Tier)
        # Use robust retry logic or fallback if quota exceeded
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        merge_prompt = (
            "Analyze these reference images. "
            "Create a detailed image generation prompt that merges these concepts into one consistent, high-quality image. "
            "Preserve identity, style, and consistency. "
            f"Additional User Instructions: {user_prompt} "
            "Output ONLY the prompt for the image generator, nothing else. "
            "Focus on photorealism and high detail."
        )
        
        try:
            # Run in executor to strict async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: model.generate_content(pil_images + [merge_prompt]))
            generated_prompt = response.text
            logger.info(f"Gemini NanoBanana Pro Prompt: {generated_prompt[:100]}...")
        except Exception as gemini_error:
            logger.exception("Gemini 1.5 Pro Generation Failed")
            if "quota" in str(gemini_error).lower():
                raise Exception("NanoBanana Pro Quota Exceeded. Please try again later.")
            raise gemini_error
        
        # 2. Generate with DALL-E 3
        try:
            dalle_response = await openai_client.images.generate(
                model="dall-e-3",
                prompt=generated_prompt[:4000], # DALL-E 3 limit
                size="1024x1024",
                quality="hd", # NanoBanana Pro Quality
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
        # P.S. The calling handler deletes the temp files, strictly speaking we don't need to close PIL images 
        # as they are lazy or context managed? PIL.Image.open returns an object. 
        # It's good practice to close if possible, but for short lived lambda it's fine.
        for img in pil_images:
            if hasattr(img, 'close'):
                img.close()

async def brand_audit(image_path: str) -> str:
    """Analyzes an image to provide a brand audit using Gemini Vision."""
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key is missing."

    try:
        import PIL.Image
        img = PIL.Image.open(image_path)
        
        model = genai.GenerativeModel('gemini-1.5-pro')
        prompt = (
            "You are a top-tier Brand Strategist and Marketing Director. "
            "Please perform a critical Brand Audit on this image. "
            "Analyze the visual identity, color palette, typography, composition, and emotional impact. "
            "Provide actionable suggestions for improvement in 3-4 short, punchy paragraphs."
        )
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: model.generate_content([img, prompt]))
        
        if hasattr(img, 'close'):
            img.close()
            
        return response.text
    except Exception as e:
        logger.exception("Brand Audit failed.")
        return f"❌ Analysis failed: {e}"

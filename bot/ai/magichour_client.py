import os
import tempfile
import asyncio
from magic_hour import AsyncClient
from utils.logger import logger

GENERATION_TIMEOUT = 300  # 5 minutes max


def _build_animation_prompt(user_prompt: str = "") -> str:
    base_prompt = (
        "subtle premium portrait motion, preserve the original face identity, "
        "facial proportions, clothing, hairstyle, body pose, and background; "
        "no face morphing, no new person, no age change, no gender change, "
        "no extra limbs, no distorted eyes, natural micro movement, slight camera movement, "
        "cinematic lighting, stable frame, high quality"
    )
    clean_prompt = (user_prompt or "").strip()
    if clean_prompt:
        return f"{base_prompt}. User direction: {clean_prompt[:500]}"
    return base_prompt


async def generate_animation(image_path: str, end_seconds: int = 4, user_prompt: str = "") -> str:
    """Generates an animation from a local image using MagicHour SDK."""
    api_key = os.getenv("MAGIC_HOUR_API_KEY")
    if not api_key:
        logger.error("MAGIC_HOUR_API_KEY is missing.")
        return None

    try:
        client = AsyncClient(token=api_key)

        response = await asyncio.wait_for(
            client.v1.animation.generate(
                assets={
                    "image_file_path": image_path,
                    "audio_source": "none"
                },
                name="AI Video Animation",
                fps=12,
                end_seconds=end_seconds,
                height=960,
                width=512,
                style={
                    "art_style": "Custom",
                    "art_style_custom": "photorealistic safe portrait animation, identity-preserving, subtle motion",
                    "camera_effect": "Simple Zoom Out",
                    "prompt_type": "custom",
                    "prompt": _build_animation_prompt(user_prompt),
                    "transition_speed": 2
                },
                wait_for_completion=True,
                download_outputs=True,
                download_directory=tempfile.gettempdir()
            ),
            timeout=GENERATION_TIMEOUT
        )

        if hasattr(response, 'downloaded_paths') and response.downloaded_paths:
            return response.downloaded_paths[0]

        return None

    except asyncio.TimeoutError:
        logger.error(f"MagicHour generation timed out after {GENERATION_TIMEOUT}s")
        raise TimeoutError(f"Video generation exceeded {GENERATION_TIMEOUT} seconds")
    except Exception as e:
        logger.exception(f"MagicHour exception: {e}")
        return None

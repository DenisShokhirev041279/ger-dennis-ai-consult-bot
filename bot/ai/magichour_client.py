import os
import tempfile
import asyncio
from magic_hour import AsyncClient
from utils.logger import logger

GENERATION_TIMEOUT = 300  # 5 minutes max


async def generate_animation(image_path: str, end_seconds: int = 5) -> str:
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
                    "art_style_custom": "cinematic realistic 3d render animation with smooth transitions",
                    "camera_effect": "Simple Zoom Out",
                    "prompt_type": "custom",
                    "prompt": "dynamic motion, high quality cinematic animation",
                    "transition_speed": 5
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

import os
import aiohttp
from utils.logger import logger

async def remove_background(image_data: bytes) -> bytes:
    """Removes the background using Remove.bg API."""
    api_key = os.getenv("REMOVEBG_API_KEY")
    if not api_key:
        logger.error("REMOVEBG_API_KEY is missing.")
        return None

    url = "https://api.remove.bg/v1.0/removebg"
    headers = {"X-Api-Key": api_key}
    
    data = aiohttp.FormData()
    data.add_field("image_file", image_data, filename="input.jpg", content_type="image/jpeg")
    data.add_field("size", "auto")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    error_msg = await response.text()
                    logger.error(f"Remove.bg failed: {response.status} - {error_msg}")
                    return None
    except Exception as e:
        logger.exception(f"Remove.bg exception: {e}")
        return None

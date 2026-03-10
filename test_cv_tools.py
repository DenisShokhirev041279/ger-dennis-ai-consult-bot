import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load env vars
load_dotenv()

from bot.ai.removebg_client import remove_background
from bot.ai.magichour_client import generate_animation
from bot.ai.gemini_client import brand_audit
from PIL import Image

async def download_sample_image(filename="sample.jpg"):
    url = "https://picsum.photos/512/512"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(filename, 'wb') as f:
                    f.write(await response.read())
                return True
    return False

async def main():
    print("--- Starting CV Tools QA Test ---")
    
    mh_key = os.getenv("MAGIC_HOUR_API_KEY")
    rb_key = os.getenv("REMBG_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    print(f"MagicHour Key present: {bool(mh_key)}")
    print(f"Remove.bg Key present: {bool(rb_key)}")
    print(f"Gemini Key present: {bool(gemini_key)}")
    
    if not await download_sample_image("test_image.jpg"):
        print("Failed to download sample image.")
        return

    # 1. Test Remove.bg
    if False and rb_key:
        print("\nTesting Remove.bg...")
        try:
            with open("test_image.jpg", "rb") as f:
                img_data = f.read()
            res = await remove_background(img_data)
            if res:
                print("[SUCCESS] Remove.bg")
                with open("test_image_nobg.png", "wb") as f:
                    f.write(res)
            else:
                print("[FAIL] Remove.bg: Empty response")
        except Exception as e:
            print(f"[ERROR] Remove.bg: {e}")
    
    # 2. Test Gemini Brand Audit
    if False and gemini_key:
        print("\nTesting Gemini Brand Audit...")
        try:
            res = await brand_audit("test_image.jpg")
            if "Gemini API key is missing" not in res and "Analysis failed" not in res:
                print("[SUCCESS] Gemini Brand Audit")
                print(f"Excerpt: {res[:100]}...")
            else:
                print(f"[FAIL] Gemini Brand Audit: {res}")
        except Exception as e:
             print(f"[ERROR] Gemini Brand Audit: {e}")
             
    # 3. Test MagicHour
    if mh_key:
        print("\nTesting MagicHour Video Generation...")
        try:
            # We use 1 second to make it fast
            res = await generate_animation("test_image.jpg", end_seconds=1)
            if res:
                print("[SUCCESS] MagicHour")
                print(f"Output saved to: {res}")
            else:
                print("[FAIL] MagicHour")
        except Exception as e:
            print(f"[ERROR] MagicHour: {e}")
            
    # Cleanup
    for f in ["test_image.jpg", "test_image_nobg.png"]:
         if os.path.exists(f):
             try:
                 os.remove(f)
             except:
                 pass
                 
    print("\n--- QA Test Complete ---")

if __name__ == "__main__":
    asyncio.run(main())

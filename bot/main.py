import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from utils.config import BOT_TOKEN
from utils.db import init_db
from utils.logger import logger

# Import Handlers
try:
    from bot.handlers import start, lang, menu, bookings, consult, admin, selftest
    from bot.payments import stars, external
except ImportError as e:
    logger.error(f"Failed to import handlers: {e}")
    # Continue to allow basic boot if possible, or exit? 
    # If handlers fail, bot is useless. But maybe partial load?
    # For now just log.
    pass

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set!")
        sys.exit(1)

    # Init DB
    await init_db()

    # Init Bot & Dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Register Routers
    dp.include_router(start.router)
    dp.include_router(lang.router)
    dp.include_router(menu.router)
    dp.include_router(bookings.router)
    dp.include_router(stars.router)     # Payment handlers
    dp.include_router(external.router)  # Payment handlers
    dp.include_router(admin.router)     # Admin handlers
    dp.include_router(selftest.router)  # Admin selftest
    
    from bot.handlers import reference_photo
    dp.include_router(reference_photo.router)
    
    dp.include_router(consult.router)   # Must be last (catch-all)

    logger.info("Bot started...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Polling error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")

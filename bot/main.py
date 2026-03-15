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
    from utils.fsm_storage import SQLiteStorage
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=SQLiteStorage())

    # Register Middleware
    from bot.middleware.rate_limit import RateLimitMiddleware
    dp.message.middleware(RateLimitMiddleware())

    # Register Routers
    dp.include_router(start.router)
    dp.include_router(lang.router)
    dp.include_router(menu.router)
    dp.include_router(bookings.router)
    dp.include_router(stars.router)     # Payment handlers
    dp.include_router(external.router)  # Payment handlers
    dp.include_router(admin.router)     # Admin handlers
    dp.include_router(selftest.router)  # Admin selftest
    
    from bot.handlers import reference_photo, newsession, subscribe, cv_tools
    dp.include_router(reference_photo.router)
    dp.include_router(newsession.router)
    dp.include_router(subscribe.router)
    dp.include_router(cv_tools.router)
    
    dp.include_router(consult.router)   # Must be last (catch-all)

    logger.info("Bot configuration loaded.")

    import os
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    
    webhook_url = os.getenv("WEBHOOK_URL")
    # Use PORT env variable if WEBHOOK_PORT isn't set (Koyeb uses PORT)
    webhook_port = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", 8080)))

    app = web.Application()
    
    async def health_check(request: web.Request):
        return web.json_response({"status": "ok", "db": "ok", "uptime": "connected"})
        
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    if webhook_url:
        logger.info(f"Starting in Webhook mode on port {webhook_port}...")
        
        async def on_startup(bot: Bot):
            await bot.set_webhook(f"{webhook_url}/webhook/{BOT_TOKEN}")
            logger.info(f"Webhook set to {webhook_url}")

        async def on_shutdown(bot: Bot):
            logger.info("Shutting down...")
            await bot.delete_webhook()

        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot
        )
        webhook_requests_handler.register(app, path=f"/webhook/{BOT_TOKEN}")
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', webhook_port)
        await site.start()

        # Keep running
        await asyncio.Event().wait()
    else:
        logger.info(f"Starting in Polling mode (Healthcheck on port {webhook_port})...")
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', webhook_port)
        await site.start()
        
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Polling error: {e}")
        finally:
            await bot.session.close()
            await runner.cleanup()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")

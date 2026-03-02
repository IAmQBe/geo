from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from bot.config import get_settings
from bot.handlers import (
    admin_router,
    categories_router,
    favorites_router,
    history_router,
    main_menu_router,
    places_router,
    profile_router,
    rating_router,
    search_router,
    start_router,
)
from bot.middlewares import (
    CityMiddleware,
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    ThrottlingMiddleware,
    UserMiddleware,
)
from db.base import init_models


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware.register(ThrottlingMiddleware(rate_limit=5, period_seconds=1))
    dp.update.middleware.register(UserMiddleware())
    dp.update.middleware.register(CityMiddleware())
    dp.update.middleware.register(LoggingMiddleware())
    dp.update.middleware.register(MetricsMiddleware())
    dp.update.middleware.register(ErrorHandlerMiddleware())

    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(main_menu_router)
    dp.include_router(categories_router)
    dp.include_router(favorites_router)
    dp.include_router(history_router)
    dp.include_router(search_router)
    dp.include_router(profile_router)
    dp.include_router(places_router)
    dp.include_router(rating_router)
    return dp


async def _health(_: web.Request) -> web.Response:
    return web.Response(text="ok")


async def _metrics(_: web.Request) -> web.Response:
    return web.Response(body=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})


async def start_webhook(bot: Bot, dp: Dispatcher, webhook_url: str, webhook_secret: str) -> None:
    app = web.Application()
    app.router.add_get("/health", _health)
    app.router.add_get("/metrics", _metrics)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=webhook_secret or None,
    ).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    await bot.set_webhook(
        webhook_url,
        secret_token=webhook_secret or None,
        drop_pending_updates=True,
    )

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8000)
    await site.start()
    logging.getLogger(__name__).info("Webhook mode started on 0.0.0.0:8000")

    await asyncio.Event().wait()


async def start_polling(bot: Bot, dp: Dispatcher) -> None:
    await dp.start_polling(bot)


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set. Configure it in .env before running the bot.")

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    await init_models()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=settings.bot_parse_mode),
    )
    dp = build_dispatcher()

    if settings.webhook_url:
        await start_webhook(bot, dp, settings.webhook_url, settings.webhook_secret)
    else:
        await start_polling(bot, dp)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.handlers import (
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
from db.base import init_models


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set. Configure it in .env before running the bot.")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    await init_models()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=settings.bot_parse_mode),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(main_menu_router)
    dp.include_router(categories_router)
    dp.include_router(favorites_router)
    dp.include_router(history_router)
    dp.include_router(search_router)
    dp.include_router(profile_router)
    dp.include_router(places_router)
    dp.include_router(rating_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

from bot.handlers.categories import router as categories_router
from bot.handlers.favorites import router as favorites_router
from bot.handlers.history import router as history_router
from bot.handlers.main_menu import router as main_menu_router
from bot.handlers.places import router as places_router
from bot.handlers.profile import router as profile_router
from bot.handlers.rating import router as rating_router
from bot.handlers.search import router as search_router
from bot.handlers.start import router as start_router

__all__ = [
    "categories_router",
    "favorites_router",
    "history_router",
    "main_menu_router",
    "places_router",
    "profile_router",
    "rating_router",
    "search_router",
    "start_router",
]

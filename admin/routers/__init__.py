from admin.routers.categories import router as categories_router
from admin.routers.cities import router as cities_router
from admin.routers.dashboard import router as dashboard_router
from admin.routers.parse_jobs import router as parse_jobs_router
from admin.routers.places import router as places_router
from admin.routers.reviews import router as reviews_router
from admin.routers.users import router as users_router

__all__ = [
    "categories_router",
    "cities_router",
    "dashboard_router",
    "parse_jobs_router",
    "places_router",
    "reviews_router",
    "users_router",
]

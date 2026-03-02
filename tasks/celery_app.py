from celery import Celery

from bot.config import get_settings

settings = get_settings()
celery_app = Celery("jambot", broker=settings.redis_url, backend=settings.redis_url)

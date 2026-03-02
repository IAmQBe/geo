from celery import Celery

from bot.config import get_settings
from tasks.beat_schedule import CELERY_BEAT_SCHEDULE

settings = get_settings()

celery_app = Celery(
    "jambot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "tasks.parse_tasks",
        "tasks.ai_tasks",
        "tasks.maintenance_tasks",
    ],
)

celery_app.conf.update(
    timezone=settings.default_timezone,
    enable_utc=False,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule=CELERY_BEAT_SCHEDULE,
)

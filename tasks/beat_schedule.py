from datetime import timedelta

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "parse-yandex-moscow-eat-hourly": {
        "task": "tasks.parse_tasks.run_parse_job",
        "schedule": timedelta(hours=1),
        "args": ("yandex", "москва", "eat", 30),
    },
    "parse-2gis-spb-specialty-hourly": {
        "task": "tasks.parse_tasks.run_parse_job",
        "schedule": timedelta(hours=1),
        "args": ("2gis", "санкт-петербург", "specialty_coffee", 30),
    },
    "generate-ai-descriptions-nightly": {
        "task": "tasks.ai_tasks.generate_missing_descriptions",
        "schedule": crontab(minute=20, hour=2),
    },
    "weekly-trends": {
        "task": "tasks.ai_tasks.generate_weekly_trends",
        "schedule": crontab(minute=0, hour=6, day_of_week="mon"),
    },
    "cleanup-inactive-users": {
        "task": "tasks.maintenance_tasks.cleanup_inactive_users",
        "schedule": crontab(minute=30, hour=3),
    },
}

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "reconforge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Result cleanup: results expire after 24 hours
    result_expires=86400,
)

celery_app.conf.beat_schedule = {
    # Cleanup expired Celery results every 6 hours
    "cleanup-expired-results": {
        "task": "maintenance.cleanup_results",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Daily database backup at 02:00 UTC
    "daily-database-backup": {
        "task": "maintenance.database_backup",
        "schedule": crontab(minute=0, hour=2),
    },
}

celery_app.autodiscover_tasks(["workers.tasks"])

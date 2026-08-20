"""Celery application for async/scheduled work: on-demand ingestion
triggers from the API, plus the nightly ingestion + sentiment-snapshot
rollup for every tracked stock.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sentivest",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

celery_app.conf.beat_schedule = {
    "nightly-ingest-and-snapshot": {
        "task": "app.worker.tasks.ingest_all_tracked_stocks",
        "schedule": crontab(hour=1, minute=0),  # 01:00 UTC daily
    },
}

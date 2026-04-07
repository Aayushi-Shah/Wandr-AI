"""Celery application instance.

Import ``celery_app`` wherever tasks need to be registered or the app
needs to be configured (e.g. in the worker entrypoint).
"""

from celery import Celery

from app.core.config import get_settings


def create_celery() -> Celery:
    settings = get_settings()
    app = Celery(
        "wandr",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.tasks.agent_tasks"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,          # re-queue on worker crash
        worker_prefetch_multiplier=1, # one task at a time per worker process
    )
    return app


celery_app = create_celery()

"""Shared test fixtures."""

import pytest

from app.tasks.celery_app import celery_app


@pytest.fixture(autouse=False)
def eager_celery():
    """Run Celery tasks synchronously in-process (no broker needed)."""
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False

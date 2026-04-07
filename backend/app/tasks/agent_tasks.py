"""Celery tasks — one thin wrapper per specialist agent.

Each task:
  1. Deserializes the AgentTask dict from the Celery message
  2. Calls agent.execute() via asyncio.run()
  3. Returns AgentResult.model_dump() — JSON-serializable for the Celery backend

budget_task signature is different: it receives the list of parallel results as its
first positional argument (injected by Celery chord) plus the raw task dict.
"""

import asyncio
from typing import Any

import structlog

from app.agents.budget import BudgetAgent
from app.agents.flight import FlightAgent
from app.agents.hotel import HotelAgent
from app.agents.itinerary import ItineraryAgent
from app.agents.models import AgentTask
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _run(coro: Any) -> Any:
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)


@celery_app.task(name="wandr.flight", bind=True, max_retries=2)
def flight_task(self: Any, task_dict: dict[str, Any]) -> dict[str, Any]:
    task = AgentTask(**task_dict)
    try:
        result = _run(FlightAgent().execute(task))
        return result.model_dump()
    except Exception as exc:
        logger.error("flight_task_failed", task_id=task.task_id, error=str(exc))
        raise self.retry(exc=exc, countdown=5) from exc


@celery_app.task(name="wandr.hotel", bind=True, max_retries=2)
def hotel_task(self: Any, task_dict: dict[str, Any]) -> dict[str, Any]:
    task = AgentTask(**task_dict)
    try:
        result = _run(HotelAgent().execute(task))
        return result.model_dump()
    except Exception as exc:
        logger.error("hotel_task_failed", task_id=task.task_id, error=str(exc))
        raise self.retry(exc=exc, countdown=5) from exc


@celery_app.task(name="wandr.itinerary", bind=True, max_retries=2)
def itinerary_task(self: Any, task_dict: dict[str, Any]) -> dict[str, Any]:
    task = AgentTask(**task_dict)
    try:
        result = _run(ItineraryAgent().execute(task))
        return result.model_dump()
    except Exception as exc:
        logger.error("itinerary_task_failed", task_id=task.task_id, error=str(exc))
        raise self.retry(exc=exc, countdown=5) from exc


@celery_app.task(name="wandr.budget", bind=True, max_retries=1)
def budget_task(
    self: Any,
    parallel_results: list[dict[str, Any]],
    task_dict: dict[str, Any],
) -> dict[str, Any]:
    """Chord callback — receives parallel results as first positional arg."""
    task = AgentTask(**task_dict)
    task = task.model_copy(
        update={"context": {"parallel_results": parallel_results}}
    )
    try:
        result = _run(BudgetAgent().execute(task))
        return result.model_dump()
    except Exception as exc:
        logger.error("budget_task_failed", task_id=task.task_id, error=str(exc))
        raise self.retry(exc=exc, countdown=5) from exc

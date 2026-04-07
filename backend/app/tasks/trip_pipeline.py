"""Trip pipeline — assembles the Celery group + chord for a full trip plan.

Pipeline shape:
    group(flight_task, hotel_task, itinerary_task)  ← parallel
        | chord callback →
    budget_task(parallel_results, task_dict)         ← fan-in

Usage:
    from app.tasks.trip_pipeline import dispatch_trip
    async_result = dispatch_trip(orchestrator_task)
"""

from typing import Any

from celery import chord, group

from app.agents.models import AgentTask
from app.tasks.agent_tasks import budget_task, flight_task, hotel_task, itinerary_task


def build_trip_chord(task: AgentTask) -> chord:
    """Return a Celery chord (not yet dispatched)."""
    task_dict = task.model_dump()

    parallel = group(
        flight_task.si(task_dict),
        hotel_task.si(task_dict),
        itinerary_task.si(task_dict),
    )
    # budget_task receives (parallel_results, task_dict) — chord injects results as arg 0
    callback = budget_task.s(task_dict)
    return chord(parallel, callback)


def dispatch_trip(task: AgentTask) -> Any:
    """Dispatch the full trip pipeline and return the AsyncResult for the chord."""
    return build_trip_chord(task).delay()

"""Unit tests for Celery agent tasks.

Tests call task functions directly (not via .delay()) to stay broker-free.
Agents are mocked so no external I/O occurs.
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.models import AgentResult, AgentStatus, AgentTask
from app.tasks.agent_tasks import budget_task, flight_task, hotel_task, itinerary_task


def make_task_dict(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "task_id": "t-001",
        "agent_name": "flight",
        "destination": "Paris",
        "start_date": "2024-09-01",
        "end_date": "2024-09-07",
        "budget": 2000.0,
        "currency": "USD",
    }
    defaults.update(overrides)
    return defaults


def make_agent_result(agent_name: str = "flight") -> AgentResult:
    return AgentResult(
        task_id="t-001",
        agent_name=agent_name,
        status=AgentStatus.DONE,
        summary="ok",
        data={"stub": True},
    )


# ── flight_task ───────────────────────────────────────────────────────────────


def test_flight_task_returns_serializable_dict() -> None:
    mock_result = make_agent_result("flight")
    with patch(
        "app.tasks.agent_tasks.FlightAgent.execute",
        new=AsyncMock(return_value=mock_result),
    ):
        result = flight_task.run(make_task_dict(agent_name="flight"))

    assert isinstance(result, dict)
    assert result["status"] == "DONE"
    assert result["agent_name"] == "flight"


def test_flight_task_retries_on_exception() -> None:
    with patch(
        "app.tasks.agent_tasks.FlightAgent.execute",
        new=AsyncMock(side_effect=RuntimeError("timeout")),
    ):
        with pytest.raises(RuntimeError):
            # max_retries=2 but retry() raises the exc after exhausting retries
            flight_task.run(make_task_dict(agent_name="flight"))


# ── hotel_task ────────────────────────────────────────────────────────────────


def test_hotel_task_returns_serializable_dict() -> None:
    mock_result = make_agent_result("hotel")
    with patch(
        "app.tasks.agent_tasks.HotelAgent.execute",
        new=AsyncMock(return_value=mock_result),
    ):
        result = hotel_task.run(make_task_dict(agent_name="hotel"))

    assert result["agent_name"] == "hotel"
    assert result["status"] == "DONE"


# ── itinerary_task ────────────────────────────────────────────────────────────


def test_itinerary_task_returns_serializable_dict() -> None:
    mock_result = make_agent_result("itinerary")
    with patch(
        "app.tasks.agent_tasks.ItineraryAgent.execute",
        new=AsyncMock(return_value=mock_result),
    ):
        result = itinerary_task.run(make_task_dict(agent_name="itinerary"))

    assert result["agent_name"] == "itinerary"
    assert result["status"] == "DONE"


# ── budget_task ───────────────────────────────────────────────────────────────


def test_budget_task_injects_parallel_results_into_context() -> None:
    """Verify parallel_results are placed into task.context before calling BudgetAgent."""
    parallel = [
        {"status": "DONE", "agent_name": "flight", "data": {"flights": []}},
        {"status": "DONE", "agent_name": "hotel", "data": {"hotels": []}},
        {"status": "DONE", "agent_name": "itinerary", "data": {"days": []}},
    ]
    mock_result = make_agent_result("budget")
    captured: list[AgentTask] = []

    async def fake_execute(self: Any, task: AgentTask) -> AgentResult:
        captured.append(task)
        return mock_result

    with patch("app.tasks.agent_tasks.BudgetAgent.execute", new=fake_execute):
        budget_task.run(parallel, make_task_dict(agent_name="budget"))

    assert captured[0].context["parallel_results"] == parallel


def test_budget_task_returns_serializable_dict() -> None:
    mock_result = make_agent_result("budget")
    with patch(
        "app.tasks.agent_tasks.BudgetAgent.execute",
        new=AsyncMock(return_value=mock_result),
    ):
        result = budget_task.run([], make_task_dict(agent_name="budget"))

    assert isinstance(result, dict)
    assert result["agent_name"] == "budget"


# ── trip_pipeline ─────────────────────────────────────────────────────────────


def test_build_trip_chord_structure() -> None:
    """Chord should have 3 tasks in the group and a budget callback."""
    from celery import chord as CeleryChord

    from app.tasks.trip_pipeline import build_trip_chord

    task = AgentTask(
        task_id="pipe-001",
        agent_name="orchestrator",
        destination="Rome",
        start_date="2024-10-01",
        end_date="2024-10-07",
        budget=3000.0,
    )

    pipeline = build_trip_chord(task)
    assert isinstance(pipeline, CeleryChord)
    # The group body should contain 3 tasks
    assert len(pipeline.tasks) == 3

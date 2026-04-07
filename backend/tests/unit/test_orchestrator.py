"""Unit tests for OrchestratorAgent.

Tests verify:
- Fan-out completes and all four sub-results appear in result.data
- One FAILED sub-agent does not crash the orchestrator (graceful degradation)
- All four sub-agents failing → status=FAILED (not a crash)
- duration_ms is populated on final result
- _synthesize always returns an AgentResult (never raises)
"""

from typing import Any
from unittest.mock import AsyncMock, patch

from app.agents.models import AgentResult, AgentStatus, AgentTask
from app.agents.orchestrator import OrchestratorAgent

# ── Helpers ───────────────────────────────────────────────────────────────────


def make_task(**overrides: Any) -> AgentTask:
    defaults: dict[str, Any] = {
        "task_id": "orch-001",
        "agent_name": "orchestrator",
        "destination": "Paris",
        "start_date": "2024-08-01",
        "end_date": "2024-08-08",
        "budget": 4000.0,
        "currency": "USD",
        "raw_request": "One week in Paris with €4000",
    }
    defaults.update(overrides)
    return AgentTask(**defaults)


def make_sub_tasks(parent: AgentTask) -> dict[str, AgentTask]:
    """Return a minimal set of sub-tasks (no Claude call needed)."""
    agents = ("flight", "hotel", "itinerary", "budget")
    return {
        name: AgentTask(
            task_id=f"{parent.task_id}-{name}",
            agent_name=name,
            destination=parent.destination,
            start_date=parent.start_date,
            end_date=parent.end_date,
            budget=parent.budget / 4,
            currency=parent.currency,
        )
        for name in agents
    }


# ── Tests ─────────────────────────────────────────────────────────────────────


async def test_orchestrator_returns_all_four_sub_results() -> None:
    agent = OrchestratorAgent()
    task = make_task()

    with patch.object(agent, "_decompose", new=AsyncMock(return_value=make_sub_tasks(task))):
        result = await agent.execute(task)

    assert result.status == AgentStatus.DONE
    assert result.task_id == "orch-001"
    assert result.agent_name == "orchestrator"
    for key in ("flight", "hotel", "itinerary", "budget"):
        assert key in result.data


async def test_orchestrator_duration_ms_populated() -> None:
    agent = OrchestratorAgent()
    task = make_task()

    with patch.object(agent, "_decompose", new=AsyncMock(return_value=make_sub_tasks(task))):
        result = await agent.execute(task)

    assert result.duration_ms is not None
    assert result.duration_ms >= 0


async def test_orchestrator_one_failed_agent_does_not_crash() -> None:
    """One FAILED sub-agent → orchestrator still returns DONE (degraded)."""
    agent = OrchestratorAgent()
    task = make_task()
    sub_tasks = make_sub_tasks(task)

    # Patch FlightAgent to raise
    with patch.object(agent, "_decompose", new=AsyncMock(return_value=sub_tasks)):
        with patch(
            "app.agents.orchestrator.FlightAgent.run",
            side_effect=RuntimeError("flight service down"),
        ):
            result = await agent.execute(task)

    assert result.status == AgentStatus.DONE  # degraded, not crashed
    assert "flight" in result.data
    assert result.data["flight"]["status"] == "FAILED"
    assert result.error is not None and "flight" in result.error


async def test_orchestrator_all_failed_gives_failed_status() -> None:
    """All four agents failing → status=FAILED, no exception raised."""
    agent = OrchestratorAgent()
    task = make_task()
    sub_tasks = make_sub_tasks(task)

    err = RuntimeError("total meltdown")

    with patch.object(agent, "_decompose", new=AsyncMock(return_value=sub_tasks)):
        with (
            patch("app.agents.orchestrator.FlightAgent.run", side_effect=err),
            patch("app.agents.orchestrator.HotelAgent.run", side_effect=err),
            patch("app.agents.orchestrator.ItineraryAgent.run", side_effect=err),
            patch("app.agents.orchestrator.BudgetAgent.run", side_effect=err),
        ):
            result = await agent.execute(task)

    assert result.status == AgentStatus.FAILED
    for key in ("flight", "hotel", "itinerary", "budget"):
        assert result.data[key]["status"] == "FAILED"


async def test_synthesize_never_raises() -> None:
    """_synthesize must always return AgentResult regardless of input."""
    agent = OrchestratorAgent()
    task = make_task()

    mixed: list[Any] = [
        AgentResult(task_id="t1", agent_name="flight", status=AgentStatus.DONE),
        ValueError("hotel exploded"),
        AgentResult(task_id="t2", agent_name="itinerary", status=AgentStatus.DONE),
        RuntimeError("budget gone"),
    ]

    result = agent._synthesize(task, mixed)
    assert isinstance(result, AgentResult)
    assert result.status == AgentStatus.DONE  # 2 of 4 succeeded


async def test_orchestrator_summary_mentions_destination() -> None:
    """When all agents succeed, summary names the destination."""
    from app.agents.models import AgentResult as AR

    agent = OrchestratorAgent()
    task = make_task(destination="Tokyo")
    sub_tasks = make_sub_tasks(task)

    ok = AR(task_id="x", agent_name="flight", status=AgentStatus.DONE)

    with patch.object(agent, "_decompose", new=AsyncMock(return_value=sub_tasks)):
        with (
            patch("app.agents.orchestrator.FlightAgent.run", new=AsyncMock(return_value=ok)),
            patch("app.agents.orchestrator.HotelAgent.run", new=AsyncMock(return_value=ok)),
            patch("app.agents.orchestrator.ItineraryAgent.run", new=AsyncMock(return_value=ok)),
            patch("app.agents.orchestrator.BudgetAgent.run", new=AsyncMock(return_value=ok)),
        ):
            result = await agent.execute(task)

    assert "Tokyo" in result.summary

"""Unit tests for BudgetAgent."""

from typing import Any

from app.agents.budget import BudgetAgent
from app.agents.models import AgentStatus, AgentTask


def make_task(**overrides: Any) -> AgentTask:
    defaults: dict[str, Any] = {
        "task_id": "budget-001",
        "agent_name": "budget",
        "destination": "Tokyo",
        "start_date": "2024-08-01",
        "end_date": "2024-08-08",
        "budget": 3000.0,
        "currency": "USD",
    }
    defaults.update(overrides)
    return AgentTask(**defaults)


def make_context(
    flight_price: float = 800.0,
    hotel_price: float = 150.0,
    activity_cost: float = 20.0,
) -> dict[str, Any]:
    return {
        "parallel_results": [
            {
                "status": "DONE",
                "agent_name": "flight",
                "data": {
                    "flights": [{"price": flight_price, "currency": "USD"}]
                },
            },
            {
                "status": "DONE",
                "agent_name": "hotel",
                "data": {
                    "hotels": [{"price_per_night": hotel_price, "currency": "USD"}]
                },
            },
            {
                "status": "DONE",
                "agent_name": "itinerary",
                "data": {
                    "days": [
                        {"activities": [{"estimated_cost": activity_cost}]},
                    ]
                },
            },
        ]
    }


async def test_budget_agent_returns_done_with_summary() -> None:
    task = make_task(context=make_context())
    agent = BudgetAgent()
    result = await agent.execute(task)

    assert result.status == AgentStatus.DONE
    assert "budget" in result.data


async def test_budget_agent_sums_correctly() -> None:
    task = make_task(
        context=make_context(flight_price=800.0, hotel_price=150.0, activity_cost=20.0)
    )
    agent = BudgetAgent()
    result = await agent.execute(task)

    summary = result.data["budget"]
    assert summary["flight_total"] == 800.0
    assert summary["hotel_total"] == 150.0
    assert summary["activities_total"] == 20.0
    assert summary["grand_total"] == 970.0


async def test_budget_agent_under_budget() -> None:
    task = make_task(budget=3000.0, context=make_context(flight_price=800.0))
    agent = BudgetAgent()
    result = await agent.execute(task)

    assert result.data["budget"]["over_budget"] is False
    assert result.data["budget"]["remaining"] > 0


async def test_budget_agent_over_budget() -> None:
    task = make_task(budget=500.0, context=make_context(flight_price=800.0))
    agent = BudgetAgent()
    result = await agent.execute(task)

    assert result.data["budget"]["over_budget"] is True
    assert result.data["budget"]["remaining"] < 0


async def test_budget_agent_skips_failed_parallel_results() -> None:
    ctx: dict[str, Any] = {
        "parallel_results": [
            {"status": "FAILED", "error": "flight service down", "data": {}},
            {
                "status": "DONE",
                "agent_name": "hotel",
                "data": {"hotels": [{"price_per_night": 150.0}]},
            },
        ]
    }
    task = make_task(context=ctx)
    agent = BudgetAgent()
    result = await agent.execute(task)

    assert result.status == AgentStatus.DONE
    assert result.data["budget"]["flight_total"] == 0.0
    assert result.data["budget"]["hotel_total"] == 150.0


async def test_budget_agent_empty_context() -> None:
    task = make_task()  # no context set
    agent = BudgetAgent()
    result = await agent.execute(task)

    assert result.status == AgentStatus.DONE
    assert result.data["budget"]["grand_total"] == 0.0


async def test_budget_agent_duration_ms_populated() -> None:
    task = make_task(context=make_context())
    agent = BudgetAgent()
    result = await agent.execute(task)

    assert result.duration_ms is not None and result.duration_ms >= 0

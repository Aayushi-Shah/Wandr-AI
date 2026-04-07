"""Unit tests for ItineraryAgent."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.agents.itinerary import ItineraryAgent
from app.agents.models import AgentStatus, AgentTask


def make_task(**overrides: Any) -> AgentTask:
    defaults: dict[str, Any] = {
        "task_id": "itin-001",
        "agent_name": "itinerary",
        "destination": "Tokyo",
        "start_date": "2024-08-01",
        "end_date": "2024-08-04",  # 3 days
        "budget": 500.0,
        "currency": "USD",
    }
    defaults.update(overrides)
    return AgentTask(**defaults)


def make_activity(name: str = "Test Activity", category: str = "museum") -> dict[str, Any]:
    return {
        "name": name,
        "description": "A fun activity",
        "location": "Tokyo, Japan",
        "duration_minutes": 120,
        "estimated_cost": 20.0,
        "currency": "USD",
        "category": category,
    }


async def test_itinerary_agent_returns_done_with_days() -> None:
    mock_client = AsyncMock()
    mock_client.fetch.return_value = [make_activity()]

    agent = ItineraryAgent(places_client=mock_client)
    result = await agent.execute(make_task())

    assert result.status == AgentStatus.DONE
    assert "days" in result.data
    assert len(result.data["days"]) == 3  # 3-day trip


async def test_itinerary_agent_day_count_matches_trip_length() -> None:
    mock_client = AsyncMock()
    mock_client.fetch.return_value = []

    agent = ItineraryAgent(places_client=mock_client)
    result = await agent.execute(make_task(start_date="2024-08-01", end_date="2024-08-06"))

    assert len(result.data["days"]) == 5


async def test_itinerary_agent_max_three_activities_per_day() -> None:
    mock_client = AsyncMock()
    # 10 activities for a 1-day trip — should cap at 3
    mock_client.fetch.return_value = [make_activity(name=f"Act{i}") for i in range(10)]

    agent = ItineraryAgent(places_client=mock_client)
    result = await agent.execute(
        make_task(start_date="2024-08-01", end_date="2024-08-02")
    )

    assert len(result.data["days"][0]["activities"]) == 3


async def test_itinerary_agent_distributes_across_days() -> None:
    mock_client = AsyncMock()
    mock_client.fetch.return_value = [make_activity(name=f"Act{i}") for i in range(6)]

    agent = ItineraryAgent(places_client=mock_client)
    result = await agent.execute(make_task())  # 3-day trip

    # 6 activities / 3 days = 2 each
    for day in result.data["days"]:
        assert len(day["activities"]) == 2


async def test_itinerary_agent_skips_malformed_activities() -> None:
    mock_client = AsyncMock()
    mock_client.fetch.return_value = [{"bad": "data"}, make_activity()]

    agent = ItineraryAgent(places_client=mock_client)
    result = await agent.execute(make_task())

    assert result.status == AgentStatus.DONE
    total = sum(len(d["activities"]) for d in result.data["days"])
    assert total == 1


async def test_itinerary_agent_duration_ms_populated() -> None:
    mock_client = AsyncMock()
    mock_client.fetch.return_value = [make_activity()]

    agent = ItineraryAgent(places_client=mock_client)
    result = await agent.execute(make_task())

    assert result.duration_ms is not None and result.duration_ms >= 0


def test_itinerary_agent_no_client_raises_not_implemented() -> None:
    agent = ItineraryAgent()
    with pytest.raises(NotImplementedError):
        import asyncio
        asyncio.run(agent.run(make_task()))

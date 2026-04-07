"""Unit tests for FlightAgent."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.agents.flight import FlightAgent
from app.agents.models import AgentStatus, AgentTask


def make_task(**overrides: Any) -> AgentTask:
    defaults: dict[str, Any] = {
        "task_id": "flight-001",
        "agent_name": "flight",
        "destination": "NRT",
        "start_date": "2024-08-01",
        "end_date": "2024-08-08",
        "budget": 1200.0,
        "currency": "USD",
    }
    defaults.update(overrides)
    return AgentTask(**defaults)


def make_flight(price: float = 800.0, duration: int = 780) -> dict[str, Any]:
    return {
        "airline": "JAL",
        "flight_number": "JL006",
        "origin": "JFK",
        "destination": "NRT",
        "departure_dt": "2024-08-01T11:00:00",
        "arrival_dt": "2024-08-02T14:30:00",
        "price": price,
        "currency": "USD",
        "stops": 0,
        "duration_minutes": duration,
    }


async def test_flight_agent_returns_done_with_flights() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [make_flight(800.0)]

    agent = FlightAgent(search_client=mock_client)
    result = await agent.execute(make_task())

    assert result.status == AgentStatus.DONE
    assert "flights" in result.data
    assert len(result.data["flights"]) == 1
    assert result.data["flights"][0]["airline"] == "JAL"


async def test_flight_agent_filters_over_budget() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [
        make_flight(800.0),   # within budget
        make_flight(1500.0),  # over budget (task budget=1200)
    ]

    agent = FlightAgent(search_client=mock_client)
    result = await agent.execute(make_task(budget=1200.0))

    assert len(result.data["flights"]) == 1
    assert result.data["flights"][0]["price"] == 800.0


async def test_flight_agent_sorts_by_price_then_duration() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [
        make_flight(900.0, duration=900),
        make_flight(700.0, duration=840),
        make_flight(700.0, duration=780),  # same price, shorter → first
    ]

    agent = FlightAgent(search_client=mock_client)
    result = await agent.execute(make_task())

    prices = [f["price"] for f in result.data["flights"]]
    assert prices[0] == 700.0
    assert result.data["flights"][0]["duration_minutes"] == 780


async def test_flight_agent_caps_at_five_results() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [make_flight(100.0 + i) for i in range(10)]

    agent = FlightAgent(search_client=mock_client)
    result = await agent.execute(make_task(budget=9999.0))

    assert len(result.data["flights"]) == 5


async def test_flight_agent_skips_malformed_items() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [
        {"bad": "data"},  # missing required fields
        make_flight(800.0),
    ]

    agent = FlightAgent(search_client=mock_client)
    result = await agent.execute(make_task())

    assert result.status == AgentStatus.DONE
    assert len(result.data["flights"]) == 1


async def test_flight_agent_duration_ms_populated() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [make_flight()]

    agent = FlightAgent(search_client=mock_client)
    result = await agent.execute(make_task())

    assert result.duration_ms is not None and result.duration_ms >= 0


def test_flight_agent_no_client_raises_not_implemented() -> None:
    agent = FlightAgent()  # uses _UnimplementedFlightClient
    with pytest.raises(NotImplementedError):
        import asyncio
        asyncio.get_event_loop().run_until_complete(agent.run(make_task()))

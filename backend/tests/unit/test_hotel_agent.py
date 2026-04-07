"""Unit tests for HotelAgent."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.agents.hotel import HotelAgent
from app.agents.models import AgentStatus, AgentTask


def make_task(**overrides: Any) -> AgentTask:
    defaults: dict[str, Any] = {
        "task_id": "hotel-001",
        "agent_name": "hotel",
        "destination": "Tokyo",
        "start_date": "2024-08-01",
        "end_date": "2024-08-08",  # 7 nights
        "budget": 1400.0,  # ~200/night
        "currency": "USD",
    }
    defaults.update(overrides)
    return AgentTask(**defaults)


def make_hotel(
    price: float = 150.0, rating: float = 4.0, name: str = "Test Hotel"
) -> dict[str, Any]:
    return {
        "name": name,
        "address": "1-1 Shinjuku, Tokyo",
        "neighborhood": "Shinjuku",
        "price_per_night": price,
        "currency": "USD",
        "rating": rating,
        "amenities": ["wifi", "gym"],
    }


async def test_hotel_agent_returns_done_with_hotels() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [make_hotel()]

    agent = HotelAgent(search_client=mock_client)
    result = await agent.execute(make_task())

    assert result.status == AgentStatus.DONE
    assert "hotels" in result.data
    assert len(result.data["hotels"]) == 1


async def test_hotel_agent_filters_over_budget_per_night() -> None:
    mock_client = AsyncMock()
    # budget=1400 / 7 nights = 200/night
    mock_client.search.return_value = [
        make_hotel(price=150.0, name="Cheap"),   # within
        make_hotel(price=300.0, name="Pricey"),  # over budget/night
    ]

    agent = HotelAgent(search_client=mock_client)
    result = await agent.execute(make_task(budget=1400.0))

    assert len(result.data["hotels"]) == 1
    assert result.data["hotels"][0]["name"] == "Cheap"


async def test_hotel_agent_scores_higher_rating_first() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [
        make_hotel(price=150.0, rating=3.0, name="Mid"),
        make_hotel(price=150.0, rating=4.5, name="Good"),
    ]

    agent = HotelAgent(search_client=mock_client)
    result = await agent.execute(make_task())

    # Higher rating should score higher
    assert result.data["hotels"][0]["name"] == "Good"


async def test_hotel_agent_caps_at_five_results() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [
        make_hotel(price=100.0, rating=4.0, name=f"Hotel{i}") for i in range(10)
    ]

    agent = HotelAgent(search_client=mock_client)
    result = await agent.execute(make_task(budget=9999.0))

    assert len(result.data["hotels"]) == 5


async def test_hotel_agent_skips_malformed_items() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [{"bad": "data"}, make_hotel()]

    agent = HotelAgent(search_client=mock_client)
    result = await agent.execute(make_task())

    assert result.status == AgentStatus.DONE
    assert len(result.data["hotels"]) == 1


async def test_hotel_agent_duration_ms_populated() -> None:
    mock_client = AsyncMock()
    mock_client.search.return_value = [make_hotel()]

    agent = HotelAgent(search_client=mock_client)
    result = await agent.execute(make_task())

    assert result.duration_ms is not None and result.duration_ms >= 0


def test_hotel_agent_no_client_raises_not_implemented() -> None:
    agent = HotelAgent()
    with pytest.raises(NotImplementedError):
        import asyncio
        asyncio.get_event_loop().run_until_complete(agent.run(make_task()))

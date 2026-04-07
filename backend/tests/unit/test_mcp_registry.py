"""Unit tests for MCPRegistry and MCP providers.

HTTP calls are mocked with respx — no real network traffic.
Tavily calls are mocked via AsyncMock — no real API key needed.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from httpx import Response

from app.mcp.registry import MCPRegistry

# ── Helpers ───────────────────────────────────────────────────────────────────


class _EchoProvider:
    """Test double — echoes params back as result."""

    async def call(self, tool: str, params: dict[str, Any]) -> dict[str, Any]:
        return {"tool": tool, "params": params}


# ── MCPRegistry ───────────────────────────────────────────────────────────────


async def test_registry_register_and_call() -> None:
    registry = MCPRegistry()
    registry.register("echo", _EchoProvider())
    result = await registry.call("echo", {"key": "value"})
    assert result["tool"] == "echo"
    assert result["params"] == {"key": "value"}


async def test_registry_unregistered_tool_raises_key_error() -> None:
    registry = MCPRegistry()
    with pytest.raises(KeyError, match="not registered"):
        await registry.call("nonexistent", {})


async def test_registry_lists_registered_tools() -> None:
    registry = MCPRegistry()
    registry.register("search", _EchoProvider())
    registry.register("get_weather", _EchoProvider())
    assert set(registry.registered_tools) == {"search", "get_weather"}


async def test_registry_from_settings_registers_expected_tools() -> None:
    """from_settings() should register search, get_weather, get_exchange_rate."""
    with patch("app.mcp.providers.tavily.AsyncTavilyClient"):
        registry = MCPRegistry.from_settings()

    assert "search" in registry.registered_tools
    assert "get_weather" in registry.registered_tools
    assert "get_exchange_rate" in registry.registered_tools


# ── TavilyProvider ────────────────────────────────────────────────────────────


async def test_tavily_provider_returns_results() -> None:
    from app.mcp.providers.tavily import TavilyProvider

    mock_client = MagicMock()
    mock_client.search = AsyncMock(return_value={
        "results": [
            {"title": "JAL Flights JFK-NRT", "url": "https://example.com",
             "content": "...", "score": 0.9},
        ],
        "answer": "Flights from $700",
    })

    with patch("app.mcp.providers.tavily.AsyncTavilyClient", return_value=mock_client):
        provider = TavilyProvider(api_key="test-key")

    result = await provider.call("search", {"query": "flights JFK to Tokyo"})
    assert len(result["results"]) == 1
    assert result["results"][0]["title"] == "JAL Flights JFK-NRT"
    assert result["answer"] == "Flights from $700"


async def test_tavily_provider_passes_max_results() -> None:
    from app.mcp.providers.tavily import TavilyProvider

    mock_client = MagicMock()
    mock_client.search = AsyncMock(return_value={"results": [], "answer": None})

    with patch("app.mcp.providers.tavily.AsyncTavilyClient", return_value=mock_client):
        provider = TavilyProvider(api_key="test-key")

    await provider.call("search", {"query": "hotels Tokyo", "max_results": 3})
    mock_client.search.assert_called_once_with(
        query="hotels Tokyo", max_results=3, search_depth="basic"
    )


# ── OpenMeteoProvider ─────────────────────────────────────────────────────────


@respx.mock
async def test_weather_provider_returns_daily_forecast() -> None:
    from app.mcp.providers.weather import OpenMeteoProvider

    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(200, json={
            "results": [
                {"name": "Tokyo", "country": "Japan", "latitude": 35.68, "longitude": 139.69}
            ]
        })
    )
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=Response(200, json={
            "daily": {
                "time": ["2024-08-01"],
                "temperature_2m_max": [32.0],
                "temperature_2m_min": [25.0],
                "precipitation_sum": [2.5],
                "weathercode": [80],
            }
        })
    )

    provider = OpenMeteoProvider(
        base_url="https://api.open-meteo.com/v1",
        geocoding_url="https://geocoding-api.open-meteo.com/v1",
    )
    result = await provider.call("get_weather", {
        "location": "Tokyo",
        "start_date": "2024-08-01",
        "end_date": "2024-08-01",
    })

    assert len(result["days"]) == 1
    assert result["days"][0]["temp_max_c"] == 32.0
    assert result["days"][0]["description"] == "Rain showers"


@respx.mock
async def test_weather_provider_raises_on_unknown_location() -> None:
    from app.mcp.providers.weather import OpenMeteoProvider

    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=Response(200, json={"results": []})
    )

    provider = OpenMeteoProvider(
        base_url="https://api.open-meteo.com/v1",
        geocoding_url="https://geocoding-api.open-meteo.com/v1",
    )
    with pytest.raises(ValueError, match="Location not found"):
        await provider.call("get_weather", {
            "location": "Xyzzy123",
            "start_date": "2024-08-01",
            "end_date": "2024-08-07",
        })


# ── FrankfurterProvider ───────────────────────────────────────────────────────


@respx.mock
async def test_currency_provider_converts_correctly() -> None:
    from app.mcp.providers.currency import FrankfurterProvider

    respx.get("https://api.frankfurter.dev/latest").mock(
        return_value=Response(200, json={"rates": {"JPY": 149.5}})
    )

    provider = FrankfurterProvider(base_url="https://api.frankfurter.dev")
    result = await provider.call("get_exchange_rate", {
        "from_currency": "USD",
        "to_currency": "JPY",
        "amount": 100.0,
    })

    assert result["rate"] == 149.5
    assert result["converted"] == 14950.0
    assert result["from"] == "USD"
    assert result["to"] == "JPY"


@respx.mock
async def test_currency_provider_defaults_amount_to_one() -> None:
    from app.mcp.providers.currency import FrankfurterProvider

    respx.get("https://api.frankfurter.dev/latest").mock(
        return_value=Response(200, json={"rates": {"EUR": 0.92}})
    )

    provider = FrankfurterProvider(base_url="https://api.frankfurter.dev")
    result = await provider.call("get_exchange_rate", {
        "from_currency": "USD",
        "to_currency": "EUR",
    })

    assert result["amount"] == 1.0
    assert result["converted"] == 0.92

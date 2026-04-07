"""MCPRegistry — central tool registry.

Adding a new data source = one call to registry.register().
Agents call registry.call(tool, params) without knowing which provider handles it.

Usage:
    registry = MCPRegistry.from_settings()
    results = await registry.call("search", {"query": "flights JFK to NRT August"})
"""

from typing import Any

import structlog

from app.mcp.client import MCPToolProvider

logger = structlog.get_logger(__name__)


class MCPRegistry:
    """Maps tool names to provider instances."""

    def __init__(self) -> None:
        self._providers: dict[str, MCPToolProvider] = {}

    def register(self, tool: str, provider: MCPToolProvider) -> None:
        """Register a provider for a tool name. One line to add a new source."""
        self._providers[tool] = provider
        logger.info("mcp_tool_registered", tool=tool, provider=type(provider).__name__)

    async def call(self, tool: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call a registered tool. Raises KeyError if tool is not registered."""
        if tool not in self._providers:
            raise KeyError(f"MCP tool '{tool}' not registered. Available: {list(self._providers)}")
        logger.debug("mcp_tool_call", tool=tool)
        return await self._providers[tool].call(tool, params)

    @property
    def registered_tools(self) -> list[str]:
        return list(self._providers.keys())

    @classmethod
    def from_settings(cls) -> "MCPRegistry":
        """Build the production registry from Settings. Called once at app startup."""
        from app.core.config import get_settings
        from app.mcp.providers.currency import FrankfurterProvider
        from app.mcp.providers.tavily import TavilyProvider
        from app.mcp.providers.weather import OpenMeteoProvider

        settings = get_settings()
        registry = cls()
        registry.register("search", TavilyProvider(api_key=settings.tavily_api_key))
        registry.register(
            "get_weather",
            OpenMeteoProvider(
                base_url=settings.open_meteo_url,
                geocoding_url=settings.open_meteo_geocoding_url,
            ),
        )
        registry.register(
            "get_exchange_rate",
            FrankfurterProvider(base_url=settings.frankfurter_url),
        )
        return registry

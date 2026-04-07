"""MCPToolProvider protocol — the interface every MCP provider must satisfy.

Each provider wraps one external data source (Tavily, Open-Meteo, Frankfurter).
Agents never import providers directly — they call MCPRegistry.call().
"""

from typing import Any, Protocol


class MCPToolProvider(Protocol):
    """Any object that can execute a named tool call."""

    async def call(self, tool: str, params: dict[str, Any]) -> dict[str, Any]: ...

"""Tavily search provider — wraps the official tavily-python SDK.

Handles web search for flights, hotels, and activities.
Tool: "search"
Params: { query, max_results?, search_depth? }
"""

from typing import Any

from tavily import AsyncTavilyClient


class TavilyProvider:
    """Wraps AsyncTavilyClient for use via MCPRegistry."""

    def __init__(self, api_key: str) -> None:
        self._client = AsyncTavilyClient(api_key=api_key)

    async def call(self, tool: str, params: dict[str, Any]) -> dict[str, Any]:
        query: str = params["query"]
        max_results: int = int(params.get("max_results", 5))
        search_depth: str = str(params.get("search_depth", "basic"))

        response = await self._client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
        )

        return {
            "query": query,
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                }
                for r in response.get("results", [])
            ],
            "answer": response.get("answer"),
        }

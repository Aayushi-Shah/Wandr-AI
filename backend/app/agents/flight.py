"""FlightAgent — searches for flights and ranks by price and duration.

The agent delegates all external I/O to a ``FlightSearchClient`` implementation.
In unit tests, inject a mock. In production (P2.2), inject the MCP web-search client.
"""

from typing import Any, Protocol

import structlog

from app.agents.base import BaseAgent
from app.agents.models import AgentResult, AgentStatus, AgentTask, FlightOption

logger = structlog.get_logger(__name__)

_MAX_RESULTS = 5


class FlightSearchClient(Protocol):
    """Search interface — satisfied by MCP web-search client in P2.2."""

    async def search(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        budget: float,
        currency: str,
    ) -> list[dict[str, Any]]: ...


class _UnimplementedFlightClient:
    """Placeholder until the MCP client is wired in P2.2."""

    async def search(self, **_kwargs: Any) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "FlightSearchClient not configured — wire MCP client in P2.2"
        )


class FlightAgent(BaseAgent):
    """Searches for flights and returns up to 5 ranked options."""

    name = "flight"

    def __init__(self, *, search_client: FlightSearchClient | None = None) -> None:
        self._client: FlightSearchClient = search_client or _UnimplementedFlightClient()  # type: ignore[assignment]

    async def run(self, task: AgentTask) -> AgentResult:
        log = logger.bind(agent=self.name, task_id=task.task_id)

        # Derive origin from context if Orchestrator set it, else leave blank for client
        origin: str = task.context.get("origin", "")

        raw = await self._client.search(
            origin=origin,
            destination=task.destination,
            departure_date=task.start_date,
            return_date=task.end_date,
            budget=task.budget,
            currency=task.currency,
        )

        options = self._rank(raw, budget=task.budget)
        log.info("flight_search_complete", found=len(raw), ranked=len(options))

        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
            summary=f"Found {len(options)} flights to {task.destination}.",
            data={"flights": [o.model_dump() for o in options]},
        )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _rank(self, raw: list[dict[str, Any]], budget: float) -> list[FlightOption]:
        """Parse, filter by budget, sort by price then duration, cap at _MAX_RESULTS."""
        options: list[FlightOption] = []
        for item in raw:
            try:
                opt = FlightOption(**item)
            except Exception:  # noqa: BLE001
                continue  # skip malformed items from search client
            if opt.price <= budget:
                options.append(opt)

        options.sort(key=lambda o: (o.price, o.duration_minutes))
        return options[:_MAX_RESULTS]

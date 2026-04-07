"""HotelAgent — searches for hotels and scores by rating and price.

Scoring formula: score = 0.6 × rating/5 + 0.4 × (1 − price/budget_per_night)
Higher score = better value. Top 5 returned.
"""

from typing import Any, Protocol

import structlog

from app.agents.base import BaseAgent
from app.agents.models import AgentResult, AgentStatus, AgentTask, HotelOption

logger = structlog.get_logger(__name__)

_MAX_RESULTS = 5


class HotelSearchClient(Protocol):
    """Search interface — satisfied by MCP maps/search client in P2.3."""

    async def search(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        budget_per_night: float,
        currency: str,
    ) -> list[dict[str, Any]]: ...


class _UnimplementedHotelClient:
    async def search(self, **_kwargs: Any) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "HotelSearchClient not configured — wire MCP client in P2.3"
        )


class HotelAgent(BaseAgent):
    """Searches for hotels and returns up to 5 scored options."""

    name = "hotel"

    def __init__(self, *, search_client: HotelSearchClient | None = None) -> None:
        self._client: HotelSearchClient = search_client or _UnimplementedHotelClient()  # type: ignore[assignment]

    async def run(self, task: AgentTask) -> AgentResult:
        log = logger.bind(agent=self.name, task_id=task.task_id)

        # Rough per-night budget: total ÷ trip length (minimum 1 night)
        from datetime import date

        try:
            nights = max(
                1,
                (
                    date.fromisoformat(task.end_date) - date.fromisoformat(task.start_date)
                ).days,
            )
        except ValueError:
            nights = 1

        budget_per_night = task.budget / nights

        raw = await self._client.search(
            destination=task.destination,
            check_in=task.start_date,
            check_out=task.end_date,
            budget_per_night=budget_per_night,
            currency=task.currency,
        )

        options = self._score(raw, budget_per_night=budget_per_night)
        log.info("hotel_search_complete", found=len(raw), scored=len(options))

        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
            summary=f"Found {len(options)} hotels in {task.destination}.",
            data={"hotels": [o.model_dump() for o in options]},
        )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _score(
        self, raw: list[dict[str, Any]], budget_per_night: float
    ) -> list[HotelOption]:
        """Parse, score by rating+value, filter over-budget, return top _MAX_RESULTS."""
        scored: list[tuple[float, HotelOption]] = []
        for item in raw:
            try:
                opt = HotelOption(**item)
            except Exception:  # noqa: BLE001
                continue
            if opt.price_per_night > budget_per_night:
                continue
            price_ratio = opt.price_per_night / budget_per_night if budget_per_night > 0 else 1.0
            score = 0.6 * (opt.rating / 5.0) + 0.4 * (1.0 - price_ratio)
            scored.append((score, opt))

        scored.sort(key=lambda t: t[0], reverse=True)
        return [opt for _, opt in scored[:_MAX_RESULTS]]

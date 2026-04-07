"""ItineraryAgent — fetches activities and builds a day-by-day schedule.

Scheduling rules:
- Max 3 activities per day
- Activities distributed across days in round-robin order
- Categories rotated to maximise variety within each day
"""

from datetime import date, timedelta
from typing import Any, Protocol

import structlog

from app.agents.base import BaseAgent
from app.agents.models import Activity, AgentResult, AgentStatus, AgentTask, DayPlan

logger = structlog.get_logger(__name__)

_MAX_PER_DAY = 3


class PlacesClient(Protocol):
    """Places/activities interface — satisfied by MCP maps/weather client in P2.3."""

    async def fetch(
        self,
        destination: str,
        days: int,
        budget: float,
        currency: str,
    ) -> list[dict[str, Any]]: ...


class _UnimplementedPlacesClient:
    async def fetch(self, **_kwargs: Any) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "PlacesClient not configured — wire MCP client in P2.3"
        )


class ItineraryAgent(BaseAgent):
    """Fetches activities and schedules them into a day-by-day itinerary."""

    name = "itinerary"

    def __init__(self, *, places_client: PlacesClient | None = None) -> None:
        self._client: PlacesClient = places_client or _UnimplementedPlacesClient()  # type: ignore[assignment]

    async def run(self, task: AgentTask) -> AgentResult:
        log = logger.bind(agent=self.name, task_id=task.task_id)

        try:
            start = date.fromisoformat(task.start_date)
            end = date.fromisoformat(task.end_date)
            days = max(1, (end - start).days)
        except ValueError:
            days = 1
            start = date.today()

        raw = await self._client.fetch(
            destination=task.destination,
            days=days,
            budget=task.budget,
            currency=task.currency,
        )

        day_plans = self._schedule(raw, start=start, days=days)
        log.info("itinerary_built", activities=len(raw), days=len(day_plans))

        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
            summary=(
                f"{days}-day itinerary for {task.destination} "
                f"with {sum(len(d.activities) for d in day_plans)} activities."
            ),
            data={"days": [d.model_dump() for d in day_plans]},
        )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _schedule(
        self, raw: list[dict[str, Any]], *, start: date, days: int
    ) -> list[DayPlan]:
        """Parse activities, rotate by category for variety, fill days."""
        activities: list[Activity] = []
        for item in raw:
            try:
                activities.append(Activity(**item))
            except Exception:  # noqa: BLE001
                continue

        # Sort by category to interleave variety when filling days
        activities.sort(key=lambda a: a.category)

        day_plans: list[DayPlan] = [
            DayPlan(date=(start + timedelta(days=i)).isoformat())
            for i in range(days)
        ]

        for idx, activity in enumerate(activities):
            day_idx = idx % days
            if len(day_plans[day_idx].activities) < _MAX_PER_DAY:
                day_plans[day_idx].activities.append(activity)

        return day_plans

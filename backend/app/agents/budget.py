"""BudgetAgent — aggregates costs from parallel agent results into a BudgetSummary.

Reads task.context["parallel_results"] set by OrchestratorAgent.
No external client needed — pure computation over structured data.
"""

from typing import Any

import structlog

from app.agents.base import BaseAgent
from app.agents.models import AgentResult, AgentStatus, AgentTask, BudgetSummary

logger = structlog.get_logger(__name__)


class BudgetAgent(BaseAgent):
    """Computes a BudgetSummary from flight, hotel, and itinerary results."""

    name = "budget"

    async def run(self, task: AgentTask) -> AgentResult:
        log = logger.bind(agent=self.name, task_id=task.task_id)

        parallel: list[dict[str, Any]] = task.context.get("parallel_results", [])
        summary = self._aggregate(parallel, total_budget=task.budget, currency=task.currency)

        log.info(
            "budget_computed",
            grand_total=summary.grand_total,
            over_budget=summary.over_budget,
        )

        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
            summary=(
                f"Total cost {summary.grand_total:.2f} {summary.currency} "
                f"({'over' if summary.over_budget else 'within'} budget)."
            ),
            data={"budget": summary.model_dump()},
        )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _aggregate(
        self,
        parallel_results: list[dict[str, Any]],
        total_budget: float,
        currency: str,
    ) -> BudgetSummary:
        flight_total = 0.0
        hotel_total = 0.0
        activities_total = 0.0

        for result in parallel_results:
            if result.get("status") == "FAILED":
                continue
            data: dict[str, Any] = result.get("data", {})

            # Flight: sum cheapest option (first in ranked list)
            flights = data.get("flights", [])
            if flights:
                flight_total += float(flights[0].get("price", 0.0))

            # Hotel: sum price_per_night × nights from first option
            hotels = data.get("hotels", [])
            if hotels:
                hotel_total += float(hotels[0].get("price_per_night", 0.0))

            # Itinerary: sum all activity estimated_costs
            days = data.get("days", [])
            for day in days:
                for activity in day.get("activities", []):
                    activities_total += float(activity.get("estimated_cost", 0.0))

        grand_total = flight_total + hotel_total + activities_total

        return BudgetSummary(
            flight_total=round(flight_total, 2),
            hotel_total=round(hotel_total, 2),
            activities_total=round(activities_total, 2),
            grand_total=round(grand_total, 2),
            currency=currency,
            over_budget=grand_total > total_budget,
            remaining=round(total_budget - grand_total, 2),
        )

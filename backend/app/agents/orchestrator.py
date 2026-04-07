"""OrchestratorAgent — decomposes a trip request and fans out to specialist agents.

Flow:
  1. _decompose(): Claude extracts structured AgentTask for each specialist.
  2. asyncio.gather(): Flight, Hotel, Itinerary run in parallel; Budget fans in last.
  3. _synthesize(): collects results into a single AgentResult (degraded if any failed).
"""

import asyncio
import json
import uuid
from typing import Any

import anthropic
import structlog

from app.agents.base import BaseAgent
from app.agents.budget import BudgetAgent
from app.agents.flight import FlightAgent
from app.agents.hotel import HotelAgent
from app.agents.itinerary import ItineraryAgent
from app.agents.models import AgentResult, AgentStatus, AgentTask

logger = structlog.get_logger(__name__)

_DECOMPOSE_SYSTEM = """\
You are a travel planning assistant. Given a trip request, extract structured data
for four specialist agents: flight, hotel, itinerary, and budget.

Return ONLY a JSON object with this exact shape (no markdown, no explanation):
{
  "flight":    {
    "destination": "...", "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD", "budget": 0.0, "currency": "USD"
  },
  "hotel":     {
    "destination": "...", "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD", "budget": 0.0, "currency": "USD"
  },
  "itinerary": {
    "destination": "...", "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD", "budget": 0.0, "currency": "USD"
  },
  "budget":    {
    "destination": "...", "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD", "budget": 0.0, "currency": "USD"
  }
}
All four keys are required. Split the total budget equally if not specified per category.
"""


class OrchestratorAgent(BaseAgent):
    """Decomposes a user trip request and fans out to specialist agents."""

    name = "orchestrator"

    def __init__(self, *, anthropic_client: anthropic.AsyncAnthropic | None = None) -> None:
        self._client = anthropic_client or anthropic.AsyncAnthropic()

    async def run(self, task: AgentTask) -> AgentResult:
        log = logger.bind(agent=self.name, task_id=task.task_id)

        # 1. Decompose via Claude
        sub_tasks = await self._decompose(task)
        log.info("orchestrator_decomposed", agents=list(sub_tasks.keys()))

        # 2. Fan-out: Flight / Hotel / Itinerary in parallel, Budget fans in last
        parallel_results: list[AgentResult | BaseException] = list(
            await asyncio.gather(
                FlightAgent().execute(sub_tasks["flight"]),
                HotelAgent().execute(sub_tasks["hotel"]),
                ItineraryAgent().execute(sub_tasks["itinerary"]),
                return_exceptions=True,
            )
        )

        # Budget receives the parallel results as context
        budget_task = sub_tasks["budget"].model_copy(
            update={
                "context": {
                    "parallel_results": [
                        r.model_dump() if isinstance(r, AgentResult) else {"error": str(r)}
                        for r in parallel_results
                    ]
                }
            }
        )
        budget_result: AgentResult | BaseException
        try:
            budget_result = await BudgetAgent().execute(budget_task)
        except Exception as exc:  # noqa: BLE001
            budget_result = exc

        all_results = [*parallel_results, budget_result]
        log.info(
            "orchestrator_fan_out_complete",
            failed=sum(1 for r in all_results if isinstance(r, BaseException)),
        )

        return self._synthesize(task, all_results)

    # ── helpers ───────────────────────────────────────────────────────────────

    async def _decompose(self, task: AgentTask) -> dict[str, AgentTask]:
        """Call Claude to parse task.raw_request into four sub-AgentTasks."""
        user_message = (
            f"Trip request: {task.raw_request or task.destination}\n"
            f"Overall budget: {task.budget} {task.currency}\n"
            f"Dates: {task.start_date} to {task.end_date}"
        )

        message = await self._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=_DECOMPOSE_SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_json = message.content[0].text.strip()
        parsed: dict[str, Any] = json.loads(raw_json)

        agent_names = ("flight", "hotel", "itinerary", "budget")
        sub_tasks: dict[str, AgentTask] = {}
        for agent_name in agent_names:
            fields = parsed[agent_name]
            sub_tasks[agent_name] = AgentTask(
                task_id=f"{task.task_id}-{agent_name}-{uuid.uuid4().hex[:6]}",
                agent_name=agent_name,
                raw_request=task.raw_request,
                destination=fields["destination"],
                start_date=fields["start_date"],
                end_date=fields["end_date"],
                budget=float(fields["budget"]),
                currency=fields.get("currency", task.currency),
            )

        return sub_tasks

    def _synthesize(
        self,
        task: AgentTask,
        results: list[AgentResult | BaseException],
    ) -> AgentResult:
        """Combine specialist results into one AgentResult. Never raises."""
        agent_keys = ("flight", "hotel", "itinerary", "budget")
        data: dict[str, Any] = {}
        failed_agents: list[str] = []

        for key, result in zip(agent_keys, results):
            if isinstance(result, BaseException):
                data[key] = {"status": "FAILED", "error": str(result)}
                failed_agents.append(key)
            else:
                data[key] = result.model_dump()

        overall_status = AgentStatus.FAILED if len(failed_agents) == 4 else AgentStatus.DONE
        summary = (
            f"Trip plan for {task.destination} ready."
            if not failed_agents
            else f"Partial plan — failed agents: {', '.join(failed_agents)}."
        )

        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=overall_status,
            summary=summary,
            data=data,
            error=f"Agents failed: {', '.join(failed_agents)}" if failed_agents else None,
        )

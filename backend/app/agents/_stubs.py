"""Stub agents used only in tests.

These return an immediate DONE result and are replaced by real implementations
in P1.3 (FlightAgent), P1.4 (HotelAgent), P1.5 (ItineraryAgent), P1.6 (BudgetAgent).
"""

from app.agents.base import BaseAgent
from app.agents.models import AgentResult, AgentStatus, AgentTask


class FlightStubAgent(BaseAgent):
    name = "flight"

    async def run(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
            summary="stub flight result",
            data={"stub": True},
        )


class HotelStubAgent(BaseAgent):
    name = "hotel"

    async def run(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
            summary="stub hotel result",
            data={"stub": True},
        )


class ItineraryStubAgent(BaseAgent):
    name = "itinerary"

    async def run(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
            summary="stub itinerary result",
            data={"stub": True},
        )


class BudgetStubAgent(BaseAgent):
    name = "budget"

    async def run(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
            summary="stub budget result",
            data={"stub": True},
        )

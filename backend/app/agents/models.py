"""Agent data contracts — AgentTask, AgentResult, AgentStatus.

Imported by BaseAgent and all specialist agents. The TypeScript equivalents
live in shared/src/agents.ts and must be kept in sync.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class AgentTask(BaseModel):
    """Input contract for every specialist agent.

    The Orchestrator populates this from its Claude decomposition.
    ``context`` carries results from upstream agents (used by BudgetAgent fan-in).
    """

    task_id: str = Field(..., description="Shared ID for the entire trip-planning request")
    agent_name: str = Field(..., description="Which agent should handle this task")
    destination: str
    start_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    end_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    budget: float = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    raw_request: str = Field(
        default="", description="Original user prompt, for Orchestrator context"
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Results from upstream agents (e.g. flight cost passed to BudgetAgent)",
    )


class AgentResult(BaseModel):
    """Output contract for every specialist agent."""

    task_id: str
    agent_name: str
    status: AgentStatus
    summary: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: float | None = None

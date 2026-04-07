import asyncio
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ── Agent status ──────────────────────────────────────────────────────────────

class AgentStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


# ── Data contracts ────────────────────────────────────────────────────────────

class AgentTask(BaseModel):
    """Input contract for every specialist agent.

    The Orchestrator populates this from its Claude decomposition.
    context carries results from upstream agents (used by BudgetAgent fan-in).
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


# ── Base class ────────────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """Abstract base class all wandr-ai agents inherit from.

    Subclasses must set `name` and implement `run()`.
    Call `execute()` — never `run()` directly — to get timeout + logging.
    """

    name: str  # Set on the subclass, e.g. name = "flight"
    timeout: float = 30.0  # Override in tests to speed up timeout assertions

    async def execute(self, task: AgentTask) -> AgentResult:
        """Public entry point. Wraps run() with timeout, structlog, and timing."""
        log = logger.bind(agent=self.name, task_id=task.task_id)
        log.info("agent_started", destination=task.destination)

        start = time.monotonic()
        try:
            result = await asyncio.wait_for(self.run(task), timeout=self.timeout)
            duration_ms = (time.monotonic() - start) * 1000
            result = result.model_copy(update={"duration_ms": duration_ms})
            log.info("agent_done", summary=result.summary, duration_ms=round(duration_ms, 1))
            return result

        except asyncio.TimeoutError:
            duration_ms = (time.monotonic() - start) * 1000
            log.error("agent_timeout", timeout=self.timeout, duration_ms=round(duration_ms, 1))
            raise

        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            log.error("agent_failed", error=str(exc), duration_ms=round(duration_ms, 1))
            raise

    @abstractmethod
    async def run(self, task: AgentTask) -> AgentResult:
        """Core agent logic. Implement in each specialist agent.

        Must return AgentResult with status DONE on success.
        Raise on unrecoverable failure — execute() will log and re-raise.
        """
        ...

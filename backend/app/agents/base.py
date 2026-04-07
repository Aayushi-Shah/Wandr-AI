import asyncio
import time
from abc import ABC, abstractmethod

import structlog

from app.agents.models import AgentResult, AgentStatus, AgentTask  # noqa: F401 — re-exported

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class all wandr-ai agents inherit from.

    Subclasses must set ``name`` and implement ``run()``.
    Always call ``execute()`` — never ``run()`` directly — to get
    timeout enforcement, structured logging, and timing.
    """

    name: str  # Set on each subclass, e.g. name = "flight"
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

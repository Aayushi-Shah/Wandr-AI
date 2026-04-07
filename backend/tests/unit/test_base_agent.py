"""Unit tests for BaseAgent interface.

Tests verify:
- Concrete subclass can be instantiated and execute() returns AgentResult
- execute() enforces timeout and re-raises TimeoutError
- execute() re-raises arbitrary exceptions (no swallowing)
- BaseAgent cannot be instantiated directly (abstract)
- duration_ms is populated on every result
"""

import asyncio

import pytest

from app.agents.base import BaseAgent
from app.agents.models import AgentResult, AgentStatus, AgentTask

# ── Helpers ───────────────────────────────────────────────────────────────────


def make_task(**overrides: object) -> AgentTask:
    defaults: dict = {
        "task_id": "task-001",
        "agent_name": "test",
        "destination": "Tokyo",
        "start_date": "2024-06-01",
        "end_date": "2024-06-06",
        "budget": 3000.0,
        "currency": "USD",
    }
    defaults.update(overrides)
    return AgentTask(**defaults)


class SuccessAgent(BaseAgent):
    name = "success"

    async def run(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
            summary="all good",
            data={"destination": task.destination},
        )


class FailingAgent(BaseAgent):
    name = "failing"

    async def run(self, task: AgentTask) -> AgentResult:
        raise ValueError("something went wrong")


class SlowAgent(BaseAgent):
    name = "slow"
    timeout = 0.05  # 50ms — triggers timeout quickly in tests

    async def run(self, task: AgentTask) -> AgentResult:
        await asyncio.sleep(10)
        return AgentResult(  # pragma: no cover
            task_id=task.task_id,
            agent_name=self.name,
            status=AgentStatus.DONE,
        )


# ── Tests ─────────────────────────────────────────────────────────────────────


async def test_execute_returns_done_result() -> None:
    agent = SuccessAgent()
    task = make_task()
    result = await agent.execute(task)

    assert result.status == AgentStatus.DONE
    assert result.task_id == "task-001"
    assert result.agent_name == "success"
    assert result.summary == "all good"
    assert result.data == {"destination": "Tokyo"}


async def test_execute_populates_duration_ms() -> None:
    agent = SuccessAgent()
    result = await agent.execute(make_task())

    assert result.duration_ms is not None
    assert result.duration_ms >= 0


async def test_execute_reraises_on_failure() -> None:
    agent = FailingAgent()
    with pytest.raises(ValueError, match="something went wrong"):
        await agent.execute(make_task())


async def test_execute_raises_timeout_error() -> None:
    agent = SlowAgent()
    with pytest.raises(asyncio.TimeoutError):
        await agent.execute(make_task())


def test_base_agent_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseAgent()  # type: ignore[abstract]


async def test_task_requires_positive_budget() -> None:
    with pytest.raises(Exception):
        make_task(budget=-100)


async def test_task_context_defaults_to_empty_dict() -> None:
    task = make_task()
    assert task.context == {}


async def test_result_error_is_none_by_default() -> None:
    agent = SuccessAgent()
    result = await agent.execute(make_task())
    assert result.error is None

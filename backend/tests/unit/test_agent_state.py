"""Unit tests for AgentStateStore (Redis state machine).

Uses fakeredis so no real Redis server is needed.
"""

import fakeredis.aioredis as fakeredis

from app.agents.models import AgentStatus
from app.agents.state import AgentStateStore


async def make_store() -> AgentStateStore:
    redis = fakeredis.FakeRedis(decode_responses=True)
    return AgentStateStore(redis)


async def test_set_and_get_status() -> None:
    store = await make_store()
    await store.set("task-1", "flight", AgentStatus.RUNNING)
    status = await store.get("task-1", "flight")
    assert status == AgentStatus.RUNNING


async def test_get_returns_none_for_unknown_key() -> None:
    store = await make_store()
    status = await store.get("task-1", "flight")
    assert status is None


async def test_state_transitions() -> None:
    store = await make_store()
    await store.set("task-1", "flight", AgentStatus.PENDING)
    await store.set("task-1", "flight", AgentStatus.RUNNING)
    await store.set("task-1", "flight", AgentStatus.DONE)
    assert await store.get("task-1", "flight") == AgentStatus.DONE


async def test_set_stores_extra_fields() -> None:
    store = await make_store()
    await store.set("task-1", "flight", AgentStatus.DONE, extra={"duration_ms": 123.4})
    # get() returns only the status — extra is stored but not surfaced by this method
    assert await store.get("task-1", "flight") == AgentStatus.DONE


async def test_get_all_returns_all_agents() -> None:
    store = await make_store()
    await store.set("task-1", "flight", AgentStatus.DONE)
    await store.set("task-1", "hotel", AgentStatus.RUNNING)

    all_states = await store.get_all("task-1")
    assert all_states["flight"] == AgentStatus.DONE
    assert all_states["hotel"] == AgentStatus.RUNNING
    assert all_states["itinerary"] is None  # never set


async def test_is_complete_true_when_all_terminal() -> None:
    store = await make_store()
    for agent in ("flight", "hotel", "itinerary", "budget"):
        await store.set("task-1", agent, AgentStatus.DONE)

    assert await store.is_complete("task-1") is True


async def test_is_complete_false_when_running() -> None:
    store = await make_store()
    await store.set("task-1", "flight", AgentStatus.DONE)
    await store.set("task-1", "hotel", AgentStatus.RUNNING)  # still in progress

    assert await store.is_complete("task-1") is False


async def test_is_complete_true_with_mixed_done_failed() -> None:
    """DONE + FAILED mix is still complete (orchestrator continues degraded)."""
    store = await make_store()
    await store.set("task-1", "flight", AgentStatus.FAILED)
    await store.set("task-1", "hotel", AgentStatus.DONE)
    await store.set("task-1", "itinerary", AgentStatus.DONE)
    await store.set("task-1", "budget", AgentStatus.DONE)

    assert await store.is_complete("task-1") is True


async def test_keys_are_isolated_per_task_id() -> None:
    store = await make_store()
    await store.set("task-A", "flight", AgentStatus.DONE)
    await store.set("task-B", "flight", AgentStatus.RUNNING)

    assert await store.get("task-A", "flight") == AgentStatus.DONE
    assert await store.get("task-B", "flight") == AgentStatus.RUNNING

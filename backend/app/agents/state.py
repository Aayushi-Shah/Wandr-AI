"""Agent state machine backed by Redis.

Each agent's state is stored at key:
    agent:{task_id}:{agent_name}

State transitions (CLAUDE.md):
    PENDING → RUNNING → DONE | FAILED

TTL: 1 hour — ephemeral, no recovery needed beyond that window.

Usage:
    store = AgentStateStore(redis_client)
    await store.set(task_id, "flight", AgentStatus.RUNNING)
    status = await store.get(task_id, "flight")
    all_states = await store.get_all(task_id)
"""

import json
from typing import Any

import redis.asyncio as aioredis

from app.agents.models import AgentStatus

_TTL_SECONDS = 3600  # 1 hour
_KEY_PREFIX = "agent"


def _key(task_id: str, agent_name: str) -> str:
    return f"{_KEY_PREFIX}:{task_id}:{agent_name}"


class AgentStateStore:
    """Thin async wrapper around Redis for agent state transitions."""

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def set(
        self,
        task_id: str,
        agent_name: str,
        status: AgentStatus,
        *,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Write (or overwrite) the state for one agent."""
        payload = {"status": status.value, **(extra or {})}
        await self._redis.setex(
            _key(task_id, agent_name),
            _TTL_SECONDS,
            json.dumps(payload),
        )

    async def get(self, task_id: str, agent_name: str) -> AgentStatus | None:
        """Return current status or None if the key has expired / never set."""
        raw = await self._redis.get(_key(task_id, agent_name))
        if raw is None:
            return None
        data = json.loads(raw)
        return AgentStatus(data["status"])

    async def get_all(self, task_id: str) -> dict[str, AgentStatus | None]:
        """Return status for all known agents for a given task_id."""
        from app.agents.models import AGENT_NAMES  # local import to avoid circular

        return {
            name: await self.get(task_id, name)
            for name in AGENT_NAMES
        }

    async def is_complete(self, task_id: str) -> bool:
        """True when every agent is DONE or FAILED (none still PENDING/RUNNING)."""
        states = await self.get_all(task_id)
        terminal = {AgentStatus.DONE, AgentStatus.FAILED}
        return all(s in terminal for s in states.values() if s is not None)

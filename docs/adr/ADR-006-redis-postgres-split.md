# ADR-006 — Redis for agent state, PostgreSQL for trip data

## Status
Accepted

## Context
Two distinct types of data need to be stored:

1. **Agent state during planning** — which agents are PENDING/RUNNING/DONE/FAILED,
   partial results, task IDs. This data is only relevant while a trip plan is
   being generated (minutes to hours). It changes frequently and at high velocity.

2. **Trip plans and user data** — completed trip plans, user accounts, flight/hotel
   records. This data must be durable, queryable, and retained indefinitely.

Options considered:
- **PostgreSQL for everything** — one system, but agent state would pollute the
  primary DB with high-write ephemeral rows, and TTL-based cleanup is complex.
- **Redis for everything** — simple, but Redis is not designed for complex relational
  queries, and data loss on restart would delete saved trips.
- **Split: Redis for ephemeral agent state, PostgreSQL for durable trip data.**

## Decision
- **Redis** stores agent state under the key `agent:{task_id}:{agent_name}` with a
  1-hour TTL. Keys auto-expire — no cleanup job needed.
- **PostgreSQL** stores all trip plans, user accounts, and related records via
  SQLAlchemy ORM + Alembic migrations.

## Consequences
**Positive:**
- Agent state TTL is automatic — no cron job or manual cleanup
- PostgreSQL schema is clean — only durable, relational data
- Redis reads/writes are sub-millisecond — ideal for frequent state updates during planning
- Clear operational model: Redis loss is recoverable (in-progress plans fail, no data loss); PostgreSQL loss is critical

**Negative:**
- Two datastores to operate, monitor, and back up
- Engineers must be deliberate about which store to use — documented in code conventions

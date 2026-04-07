# wandr-ai — AI Travel Agent
> Auto-loaded every session. Keep ≤150 lines. Full task list → .claude/context/tasks.md

---

## Project overview
Multi-agent AI travel planner. User types a trip request → Orchestrator decomposes
it → 4 parallel agents (Flight, Hotel, Itinerary, Budget) call real-world data via
MCP servers → results stream via SSE to a Next.js frontend with live agent status,
an interactive map, day-by-day timeline, and budget breakdown.

**GitHub:** github.com/aayushishah/wandr-ai

---

## Key entry points
```
backend/app/main.py          ← create_app() — FastAPI app factory
backend/app/core/config.py   ← Settings — pydantic-settings
backend/app/agents/base.py   ← BaseAgent — abstract class
backend/app/mcp/registry.py  ← MCPRegistry — central tool registry
backend/app/api/v1/trip.py   ← SSE endpoint
frontend/src/app/page.tsx    ← landing / chat input
frontend/src/hooks/useAgentStream.ts  ← SSE EventSource hook
shared/src/events.ts         ← typed SSE event contracts
```

---

## Tech stack
| Layer | Technology |
|---|---|
| Backend | FastAPI 0.115+, Python 3.12 |
| Agents | Anthropic Python SDK (Claude + MCP tool use) |
| Queue | Celery 5.x + Redis 7 |
| Database | PostgreSQL 15 + Alembic |
| Tracing | OpenTelemetry + Jaeger |
| Frontend | Next.js 14 App Router, Tailwind, Framer Motion |
| Map | Mapbox GL / react-map-gl |
| State | Zustand |
| Package mgr | pnpm workspaces |

---

## Architecture decisions (full ADRs in docs/adr/)
- **ADR-001** Monorepo + pnpm — shared TS types without npm publish
- **ADR-002** Orchestrator pattern — Claude decomposes at runtime, not hardcoded rules; BudgetAgent always fan-in last
- **ADR-003** MCPRegistry — agents request tools by name; adding a server = one-line registry change
- **ADR-004** SSE over WebSocket — one-directional stream, no client library, HTTP/1.1 compatible
- **ADR-005** App factory — `create_app()` gives each test a fresh instance, no shared state
- **ADR-006** Redis for agent state (ephemeral, 1hr TTL), PostgreSQL for trips (durable)
- **ADR-007** Calendar MCP behind feature flag — OAuth opt-in; currency MCP has fallback cache

---

## Agent design
```
User prompt
  → Claude: decompose → JSON sub-tasks
  → Celery group: [FlightTask, HotelTask, ItineraryTask]  ← parallel
  → BudgetTask: fan-in after all three
  → Claude: synthesize → TripPlan
  → SSE: stream typed events to frontend
```
Agent state machine (Redis key `agent:{task_id}:{agent_name}`):
`PENDING → RUNNING → DONE | FAILED` (orchestrator continues degraded on FAILED)

SSE event types (shared/src/events.ts):
`agent_started · agent_progress · agent_done · agent_failed · orchestrator_synthesis · trip_complete`

---

## Code conventions
**Python:** Pydantic v2 for all contracts · type hints on every function · async handlers throughout · structlog JSON with trace_id · `asyncio.wait_for(coro, timeout=30.0)` on every agent call · pydantic-settings (never `os.environ` directly) · Alembic for all schema changes
**TypeScript:** `strict: true`, no `any` · path aliases `@/` and `@wandr/shared` · all API calls via `@/lib/api.ts` · Zustand for global, useState for local · Framer Motion only (no CSS transitions) · never localStorage/sessionStorage
**Git:** branch `feat/P{n}.{n}-{slug}` · conventional commits · squash-merge PRs

---

## Rules — never break these
- Do NOT install a dependency without explaining what it does first
- Do NOT create files outside `packages/` or `docs/`
- Do NOT write a migration by hand — always `alembic revision --autogenerate`
- Do NOT skip tests for any agent logic
- Do NOT use `any` in TypeScript
- Do NOT store secrets in code — `.env` only, never committed
- Do NOT implement Calendar MCP without the feature flag
- Do NOT catch bare `Exception` — catch specific, handle or re-raise
- Do NOT commit to main — branch per task
- Do NOT start Phase 2 before Phase 1 agents have passing unit tests

---

## Session protocol

**START — read in this order:**
1. This file (auto-loaded)
2. `.claude/context/progress.md` — current task, what's done
3. `.claude/context/lessons.md` — past mistakes to avoid
4. `.claude/context/code-map.md` — where things live (skip Phase 0)
5. `.claude/context/phase-{N-1}-summary.md` — only when starting a new phase

**END — update in this order:**
1. `.claude/context/progress.md` — check off task, set next Active, append session log
2. `.claude/context/code-map.md` — add new files and key symbols
3. This file's "Current session" block → next task
4. If phase complete → write `.claude/context/phase-N-summary.md`

---

## Task completion gates — run ALL before marking any task done

**Backend task:**
```
ruff check backend/app/ backend/tests/ --select E,F,W,I
pytest backend/tests/ -x -q
zero bare except: · zero os.environ direct reads · type hints on every function
```
**Frontend task:**
```
pnpm --filter @wandr/frontend tsc --noEmit
pnpm --filter @wandr/frontend exec eslint src/ --max-warnings 0
zero `any` · zero localStorage · zero raw fetch calls in components
```
**All tasks:**
```
.claude/context/progress.md updated
.claude/context/code-map.md updated
CLAUDE.md "Current session" updated to next task
```

---

## Stuck protocol
- Attempts 1–3: diagnose, adjust, retry — do not stop or ask
- After attempt 3: write diagnosis + what was tried to `.claude/context/lessons.md`, then ask
- Even when eventually solved: if it took 2+ attempts, write the fix to `lessons.md`

---

## Useful commands
```bash
make dev            # docker-compose up all services
make dev-backend    # FastAPI + hot reload only
make dev-frontend   # Next.js only
make test           # all tests
make test-backend   # pytest
make migrate        # alembic upgrade head
make migration msg="add users table"
make lint           # ruff + eslint
```

---

## Current session

**Working on:** P1.7 — Celery task queue

**Goal:** Wire each specialist agent as a Celery task; group() for parallel fan-out, chord for Budget fan-in.

**Notes:**
- Celery app already bootstrapped in `app/tasks/celery_app.py` (stub from P0.2)
- Tasks wrap agent.execute() — one task per agent
- Use celery group() for Flight/Hotel/Itinerary parallel; chord() for Budget fan-in
- Redis broker already configured in docker-compose

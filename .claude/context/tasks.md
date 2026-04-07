---
read: planning sessions only (not every session)
update: when tasks are added, changed, or dropped — always add a change log entry
---

# Task List — wandr-ai (34 tasks across 6 phases)

_This is the single source of truth for the project plan._
_CLAUDE.md does NOT contain this list. Never duplicate it._
_Struck-through rows = dropped/superseded. Never delete rows._

---

### Phase 0 — Setup & Architecture
| ID | Task | Key commits |
|---|---|---|
| P0.1 | Initialize monorepo with pnpm workspaces | chore: init pnpm workspace root · chore: add packages/backend skeleton · chore: add packages/frontend skeleton · chore: add packages/shared types package · chore: add makefile |
| P0.2 | FastAPI backend skeleton with app factory | feat: fastapi app factory with versioned routers · feat: structlog json logging · feat: lifespan for db/redis startup |
| P0.3 | Next.js 14 frontend with App Router | feat: init nextjs app router and tailwind · chore: path aliases and tsconfig strict · feat: framer-motion dependency |
| P0.4 | Docker Compose local dev | chore: docker-compose all services · chore: .env.example · chore: makefile dev commands |
| P0.5 | ADR docs + structure decisions | docs: adr-001 through adr-004 |

### Phase 1 — Agent Infrastructure
| ID | Task | Key commits |
|---|---|---|
| P1.1 | BaseAgent abstract class | feat: BaseAgent with type contracts · feat: AgentTask and AgentResult dataclasses · test: BaseAgent interface tests |
| P1.2 | OrchestratorAgent | feat: orchestrator task decomposition · feat: parallel fan-out with asyncio · feat: result synthesis · test: orchestrator unit tests |
| P1.3 | FlightAgent | feat: FlightAgent with web search MCP · feat: FlightOption model and ranking · test: mock mcp responses |
| P1.4 | HotelAgent | feat: HotelAgent with search + maps MCP · feat: neighborhood scoring · test: ranking logic |
| P1.5 | ItineraryAgent | feat: weather-aware scheduling · feat: proximity grouping · test: generation tests |
| P1.6 | BudgetAgent | feat: cost aggregation · feat: currency conversion · feat: over-budget detection · test: calculations |
| P1.7 | Celery task queue | feat: wrap agents as celery tasks · feat: celery group dispatch · feat: timeout and retry · test: integration tests |
| P1.8 | Agent state machine (Redis) | feat: state machine in redis · feat: partial result support · test: state transitions and ttl |

### Phase 2 — MCP Integration
| ID | Task | Key commits |
|---|---|---|
| P2.1 | MCP registry + client setup | feat: MCPRegistry · feat: client initialization · test: tool discovery |
| P2.2 | Web Search MCP | feat: client wrapper · feat: domain helpers · test: integration with vcr |
| P2.3 | Maps + Weather MCP | feat: maps client · feat: weather with redis cache · test: cache hit/miss |
| P2.4 | Currency + Calendar MCP | feat: currency with fallback · feat: calendar behind feature flag · feat: google oauth |
| P2.5 | MCP error handling + circuit breaker | feat: circuit breaker with tenacity · feat: degraded response strategy · feat: otel mcp spans |

### Phase 3 — Backend API & Streaming
| ID | Task | Key commits |
|---|---|---|
| P3.1 | OpenAPI spec first | docs: openapi 3.1 spec · chore: spectral linter |
| P3.2 | SSE streaming endpoint | feat: sse endpoint with typed events · feat: event emitter from redis · test: sse sequence integration |
| P3.3 | PostgreSQL + Alembic | feat: full schema · feat: alembic setup · feat: uuid pks and audit timestamps · test: migration rollback |
| P3.4 | JWT auth + refresh tokens | feat: register and login · feat: refresh token with httponly cookie · feat: auth middleware · test: token lifecycle |
| P3.5 | OpenTelemetry tracing | feat: otel fastapi · feat: celery spans · feat: mcp spans · feat: trace id in logs |

### Phase 4 — Frontend Core
| ID | Task | Key commits |
|---|---|---|
| P4.1 | App layout + auth flow | feat: root layout · feat: auth pages · feat: zustand auth store · feat: nextjs middleware protection |
| P4.2 | Chat input + streaming display | feat: chat input · feat: useAgentStream hook · feat: streaming display · feat: markdown render |
| P4.3 | Live agent status panel | feat: agent status panel · feat: useAgentStatus hook · feat: framer motion · feat: elapsed timer |
| P4.4 | Itinerary timeline | feat: horizontal scroll timeline · feat: day card with weather blocks · feat: activity block · feat: expand/collapse |
| P4.5 | Trip summary + budget chart | feat: summary card · feat: budget donut recharts · feat: budget progress bar |

### Phase 5 — Interactive Features
| ID | Task | Key commits |
|---|---|---|
| P5.1 | Mapbox itinerary map | feat: mapbox map · feat: numbered markers per day · feat: activity popup · feat: route polylines |
| P5.2 | Budget dial — drag to re-plan | feat: circular dial svg · feat: drag handler · feat: debounced re-plan · feat: diff view |
| P5.3 | Weather overlay | feat: weather icon component · feat: rain warning on outdoor activities · feat: temp range display |
| P5.4 | Compare mode | feat: compare toggle · feat: split-screen layout · feat: diff highlighting · feat: re-plan second trip |
| P5.5 | Framer Motion choreography | feat: staggered agent entry · feat: thinking pulse · feat: trip slide-up reveal · feat: typing cursor |

### Phase 6 — Polish & Launch
| ID | Task | Key commits |
|---|---|---|
| P6.1 | Trip history — save and reload | feat: save trip to postgres · feat: history sidebar · feat: load saved trip · feat: delete with optimistic ui |
| P6.2 | Error boundaries + empty states | feat: error boundary · feat: skeleton loaders · feat: empty states · feat: retry on agent failure |
| P6.3 | Playwright E2E tests | feat: playwright setup · test: plan trip flow · test: save and reload · chore: add to github actions |
| P6.4 | README + docs + demo | docs: readme with setup guide · docs: architecture deep-dive · chore: railway deployment |

---

## Change log
<!-- Every mutation to the plan is recorded here — never delete entries -->
<!-- Format: [DATE] [ID] action — reason -->
<!-- Example: [2026-04-15] P2.6 added — rate limiting on SSE endpoint, needed before deploy -->
<!-- Example: [2026-04-20] P1.5 scope reduced — weather scheduling moved to P5.3 -->
<!-- Example: [2026-05-01] P2.4 calendar dropped — OAuth deferred, see ADR-008 -->

<!-- 2026-04-07 — initial 34-task list moved from CLAUDE.md to this file (single source of truth) -->

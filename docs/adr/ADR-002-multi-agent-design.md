# ADR-002 — Multi-agent Orchestrator pattern

## Status
Accepted

## Context
Trip planning requires gathering data from multiple domains simultaneously: flights,
hotels, itinerary activities, and budget calculations. These domains are largely
independent and can be parallelised. Options considered:

1. **Single monolithic prompt** — one Claude call with all context. Simple, but slow
   (sequential tool calls), hits context limits on complex trips, and gives no
   visibility into intermediate progress.

2. **Hardcoded pipeline** — fixed sequence of API calls. Fast but brittle — adding
   a new domain (e.g. restaurant reservations) requires code changes.

3. **Orchestrator + specialist agents** — Claude decomposes the request into
   sub-tasks at runtime (not hardcoded), dispatches them in parallel, then
   synthesises results. Adding a new agent = one new Celery task + one new class.

## Decision
Implement an Orchestrator agent that uses Claude to decompose user requests into
structured JSON sub-tasks at runtime. Specialist agents (Flight, Hotel, Itinerary,
Budget) run in parallel via Celery `group()`. BudgetAgent always runs last as a
fan-in, because it depends on cost data from all three other agents.

## Consequences
**Positive:**
- Parallelism: Flight, Hotel, and Itinerary agents run concurrently — faster results
- Generalises to new request types without changing decomposition logic
- Each agent is independently testable with mock MCP responses
- Real-time SSE progress per agent (user sees agents "thinking" live)

**Negative:**
- More moving parts than a single prompt — requires Redis for agent state, Celery for task dispatch
- Orchestrator decomposition can produce unexpected sub-tasks for unusual requests; requires prompt testing
- BudgetAgent fan-in means total latency = max(Flight, Hotel, Itinerary) + Budget

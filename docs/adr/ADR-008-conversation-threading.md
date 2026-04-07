# ADR-008 — Conversation Threading (Multi-turn Chat)

**Status:** Accepted  
**Date:** 2026-04-07

---

## Context

The initial design is one-shot: one user prompt → one `TripPlan`. Users will naturally
want to refine their plan:
- *"Make it $5000 instead and add couple activities"*
- *"Skip the temples, more food tours"*
- *"Can we do 10 days instead of 7?"*

We need to decide how to support this without a costly post-launch migration.

---

## Decision

Bake conversation context and selective agent re-running into the schema and API
from Phase 3 onwards. Do **not** build the full chat UI yet — that is P4.2/P4.6 —
but make the backend capable of it from day one.

### Database additions (P3.3)

```
conversations
  id            UUID  PK
  user_id       FK → users.id
  created_at    TIMESTAMP

trips
  id               UUID  PK
  conversation_id  FK → conversations.id  ← nullable for backward compat
  parent_trip_id   FK → trips.id (self)   ← nullable, previous version of plan
  message          TEXT                   ← user message that triggered this plan
  ...existing fields...
```

### API additions (P3.1 / P3.6)

```
POST /trips
  Body: { raw_request, budget, currency, start_date, end_date }
  Creates a new Conversation + first Trip.
  Returns: { conversation_id, trip_id, stream_url }

POST /trips/{trip_id}/refine
  Body: { message }
  Classifies which agents need re-running, re-runs only those.
  Returns: { conversation_id, trip_id, stream_url }
```

### Orchestrator — selective re-run (P3.6)

On a refinement request, the Orchestrator runs a classification step before fan-out:

```
POST /trips/{id}/refine  { message: "add more food tours" }
  │
  ▼
OrchestratorAgent._classify_changes(message, current_trip)
  └─ Claude reads message + current TripPlan
  └─ Returns: { "agents_to_rerun": ["itinerary"], "reason": "..." }
  │
  ▼
For each specialist agent:
  - In agents_to_rerun  → run agent, get fresh result
  - Not in list         → reuse previous result directly
  Budget ALWAYS re-runs (costs may change even with partial updates)
  │
  ▼
_synthesize() merges fresh + reused results into new TripPlan
```

**Classification heuristics Claude uses:**

| Message type | Agents to re-run |
|---|---|
| "more food tours", "skip temples" | itinerary |
| "nicer hotel", "budget $200/night" | hotel, budget |
| "fly business class", "earlier departure" | flight, budget |
| "change dates", "10 days not 7" | flight, hotel, itinerary, budget |
| "increase total budget to $5000" | all (constraint affects every agent) |

**`AgentTask.context` shape for refinement:**
```python
context = {
    "conversation_history": [
        {"role": "user", "content": "Plan me a week in Tokyo, $3000"},
        {"role": "assistant", "content": "<TripPlan summary>"},
        {"role": "user", "content": "Add more food tours"},
    ],
    "current_trip": { ...previous TripPlan dict... },
    "agents_to_rerun": ["itinerary"],    # set by Orchestrator after classification
    "reused_results": {                   # passed through unchanged
        "flight": { ...previous FlightResult... },
        "hotel":  { ...previous HotelResult... },
    },
}
```

For the initial request `conversation_history` is empty and `agents_to_rerun` is
`["flight", "hotel", "itinerary"]` — the one-shot flow is unchanged.

### Frontend (P4.2, P4.6)

- P4.2: `ChatThread` component — message list with streaming plan cards inline
- P4.6: Conversation history sidebar — list of past conversations, click to reload

---

## Consequences

**Good:**
- Only changed agents re-run — faster responses and lower API cost on refinements
- `_classify_changes()` follows the same pattern as `_decompose()` — one more Claude
  call, no new infrastructure
- `parent_trip_id` enables compare-mode (P5.4) between plan versions for free
- One-shot flow is untouched when `conversation_history` is empty

**Trade-offs:**
- `POST /trips` now creates two records (Conversation + Trip) instead of one
- Classification can occasionally be wrong — if Claude misclassifies, a stale
  result is reused. Mitigation: user can always trigger a full re-plan by saying
  "re-plan everything"
- P4.2 is more complex than a single input box — but it's the right UX

---

## Rejected alternatives

**Full re-plan every time:** Simpler and always coherent, but wasteful. A "more
food tours" message re-runs flight search for no reason. Rejected in favour of
selective re-running from the start.

**Separate chatbot service:** Unnecessary complexity. The Orchestrator already
calls Claude; `_classify_changes()` is a prompt change, not a service boundary.

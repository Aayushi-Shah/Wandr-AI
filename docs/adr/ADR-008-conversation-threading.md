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

Bake conversation context into the schema and API from Phase 3 onwards. Do **not**
build the full chat UI yet — that is P4.2/P4.6 — but make the backend capable of it
from day one.

### Database additions (P3.3)

```
conversations
  id            UUID  PK
  user_id       FK → users.id
  created_at    TIMESTAMP

trips
  id            UUID  PK
  conversation_id  FK → conversations.id  ← new (nullable for backward compat)
  parent_trip_id   FK → trips.id (self)   ← new (nullable, previous version of plan)
  message          TEXT                   ← new (user message that triggered this plan)
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
  Adds to existing Conversation, re-runs relevant agents.
  Returns: { conversation_id, trip_id, stream_url }
```

### Orchestrator change (P3.6)

`AgentTask.context` already exists as an open dict. For refinement requests,
the Orchestrator populates it with:

```python
context = {
    "conversation_history": [
        {"role": "user", "content": "Plan me a week in Tokyo, $3000"},
        {"role": "assistant", "content": "<previous TripPlan summary>"},
        {"role": "user", "content": "Add more food tours"},
    ],
    "current_trip": { ...previous TripPlan dict... },
}
```

Claude's decomposition prompt is updated to include this history, so it can
determine which sub-agents need re-running vs. which results can be reused.

### Frontend (P4.2, P4.6)

- P4.2: `ChatThread` component (replaces single `ChatInput`) — message list with
  streaming plan cards inline
- P4.6: Conversation history sidebar — list of past conversations, click to reload

---

## Consequences

**Good:**
- No migration needed later — schema is ready from P3.3
- Orchestrator history awareness is additive — existing one-shot flow still works
  when `conversation_history` is empty
- `parent_trip_id` enables compare-mode (P5.4) between plan versions for free

**Trade-offs:**
- `POST /trips` now creates two records (Conversation + Trip) instead of one
- Orchestrator decomposition prompt grows slightly with history context
- P4.2 is more complex than a single input box — but it's the right UX

## Rejected alternatives

**Full re-plan every time (no diff logic):** Accepted — simpler, always coherent.
We do NOT attempt to figure out which agents to skip. Every refinement runs all
four agents with history in context. Selective re-running can be added later as
a performance optimisation if needed.

**Separate chatbot service:** Rejected — unnecessary complexity. The Orchestrator
already calls Claude; passing conversation history is a prompt change, not a
service boundary.

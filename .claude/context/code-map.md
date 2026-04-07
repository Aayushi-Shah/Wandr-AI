---
read: every session start (skip in Phase 0 — no code yet)
update: every session end — append new files/symbols created
---

# Code Map
_Living map of what exists and where. Append after every session._
_Format: `path/to/file.py → ClassName or func_name() — what it does`_

---

## Backend (`backend/`)

<!-- app/main.py → create_app() — FastAPI app factory -->
<!-- app/core/config.py → Settings — pydantic-settings root config object -->
<!-- app/core/database.py → get_db() — async SQLAlchemy session dependency -->
<!-- app/core/redis.py → get_redis() — Redis connection pool -->
<!-- app/agents/base.py → BaseAgent — abstract base with run(), timeout, structlog -->
<!-- app/agents/orchestrator.py → OrchestratorAgent — decomposes prompt, fan-out, synthesis -->
<!-- app/agents/flight.py → FlightAgent — web search MCP, FlightOption ranking -->
<!-- app/agents/hotel.py → HotelAgent — search + maps MCP, neighborhood scoring -->
<!-- app/agents/itinerary.py → ItineraryAgent — weather-aware scheduling, proximity grouping -->
<!-- app/agents/budget.py → BudgetAgent — cost aggregation, FX conversion, over-budget detection -->
<!-- app/mcp/registry.py → MCPRegistry — central tool registry, one-line to add new server -->
<!-- app/api/v1/trip.py → POST /trips, GET /trips/{id}/stream (SSE) -->
<!-- app/api/v1/auth.py → POST /auth/register, /auth/login, /auth/refresh -->
<!-- app/models/db.py → User, Trip, TripFlight, TripHotel, TripDay, TripActivity (ORM) -->
<!-- app/models/schemas.py → Pydantic request/response schemas -->
<!-- app/tasks/celery_app.py → celery app, FlightTask, HotelTask, ItineraryTask, BudgetTask -->
<!-- app/telemetry/otel.py → setup_telemetry() — OTel + Jaeger exporter -->

---

## Frontend (`frontend/src/`)

<!-- app/layout.tsx → root layout, fonts, Zustand provider -->
<!-- app/page.tsx → landing/chat input page -->
<!-- app/trip/[id]/page.tsx → trip results page -->
<!-- components/chat/ChatInput.tsx — trip request input with submit -->
<!-- components/chat/StreamingDisplay.tsx — renders SSE stream as typed text -->
<!-- components/agents/AgentStatusPanel.tsx — live status + Framer Motion choreography -->
<!-- components/trip/TripSummaryCard.tsx — destination, dates, total cost -->
<!-- components/trip/ItineraryTimeline.tsx — horizontal scroll day/activity timeline -->
<!-- components/trip/BudgetDial.tsx — draggable SVG dial, triggers re-plan -->
<!-- components/trip/CompareMode.tsx — split-screen diff of two trip plans -->
<!-- components/map/TripMap.tsx — Mapbox GL map, numbered markers, route polylines -->
<!-- hooks/useAgentStream.ts — SSE EventSource hook, typed events from @wandr/shared -->
<!-- hooks/useAgentStatus.ts — per-agent PENDING/RUNNING/DONE/FAILED state -->
<!-- hooks/useTrip.ts — trip CRUD via /lib/api.ts -->
<!-- lib/api.ts — all fetch calls go through here, handles auth headers -->
<!-- lib/auth.ts — JWT decode, token refresh logic -->
<!-- store/auth.ts — Zustand auth store (user, token, setUser, logout) -->

---

## Shared types (`shared/src/`)

<!-- events.ts → AgentStarted, AgentProgress, AgentDone, AgentFailed, TripComplete (SSE types) -->
<!-- agents.ts → AgentName, AgentStatus, AgentResult -->
<!-- trip.ts → TripPlan, FlightOption, HotelOption, DayPlan, Activity -->

---

## Database
<!-- Canonical schema lives in backend/alembic/versions/ -->
<!-- ORM models: backend/app/models/db.py -->
<!-- Tables: users, trips, trip_flights, trip_hotels, trip_days, trip_activities -->

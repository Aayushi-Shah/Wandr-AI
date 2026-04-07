# ADR-007 — Calendar MCP behind a feature flag

## Status
Accepted

## Context
The ItineraryAgent can optionally integrate with Google Calendar to check the
user's existing commitments when scheduling activities. This requires a Google
OAuth flow, refresh token management, and handling token revocation.

Two concerns led to this decision:

1. **OAuth complexity** — Calendar requires a complete OAuth 2.0 flow (consent screen,
   token storage, refresh). This is disproportionate complexity for an optional feature
   that adds value only to users who explicitly want it. Shipping it unconditionally
   would block the core trip-planning flow behind OAuth setup.

2. **MCP reliability** — External MCP servers can be unavailable or slow. If any
   single MCP call can crash the entire plan, the UX is fragile. The currency MCP
   has a similar concern (FX API outages).

## Decision
- **Calendar MCP** is gated behind `ENABLE_CALENDAR_MCP=false` in `.env`.
  The ItineraryAgent checks this flag before attempting any calendar tool calls.
  Users opt in explicitly; the default experience requires no Google auth.

- **Currency MCP** implements a **graceful degradation** fallback: on API failure,
  fall back to cached exchange rates (Redis, TTL 24h). One bad external API must
  never break the whole plan.

## Consequences
**Positive:**
- Core trip planning works with zero OAuth setup
- Calendar integration can be tested and enabled per-deployment without code changes
- Degradation strategy for currency means FX failures are invisible to users
- Pattern is reusable for any future opt-in integrations

**Negative:**
- Feature flag state must be documented for operators (covered by `.env.example`)
- Cached FX rates can be stale — acceptable for trip budget estimates, not financial transactions
- Calendar feature requires separate testing path; easy to neglect in CI

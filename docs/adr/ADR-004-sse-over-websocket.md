# ADR-004 — SSE over WebSocket for agent streaming

## Status
Accepted

## Context
The frontend needs to receive live updates as agents work: agent started,
tool called, agent done, trip complete. Options considered:

1. **Polling** — frontend calls `GET /trips/{id}/status` every N seconds.
   Simple but high latency, wasteful, and gives a choppy UX.

2. **WebSocket** — full-duplex, persistent connection. Standard choice for
   real-time features. But requires a WebSocket server, client library, and
   adds complexity for reconnection handling.

3. **Server-Sent Events (SSE)** — HTTP/1.1 chunked response, browser-native
   `EventSource` API, server pushes events. One-directional (server → client only).

## Decision
Use SSE via FastAPI's `StreamingResponse` and the browser's native `EventSource`.
The frontend hook `useAgentStream` opens an `EventSource` to `GET /api/v1/trips/{id}/stream`.

## Consequences
**Positive:**
- No client library needed — `EventSource` is built into every browser
- Works over HTTP/1.1 and through standard load balancers/proxies without special config
- Automatic reconnection is built into `EventSource`
- FastAPI has native `StreamingResponse` support — no additional server needed
- Trip planning is one-directional by nature (server pushes progress, client only reads)

**Negative:**
- One-directional only — if bidirectional interaction is ever needed (e.g. mid-plan edits), SSE cannot be used and WebSocket would need to be introduced
- HTTP/1.1 has a per-domain connection limit (6); mitigated by HTTP/2 multiplexing in production
- SSE connections must be managed carefully to avoid memory leaks on long-lived plans

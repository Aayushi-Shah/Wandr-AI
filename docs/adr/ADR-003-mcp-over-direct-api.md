# ADR-003 — MCPRegistry over direct API calls

## Status
Accepted

## Context
Each specialist agent needs to call external data sources: web search, maps,
weather, currency exchange. Options for wiring these up:

1. **Direct API calls per agent** — each agent imports and calls the relevant API
   client directly. Simple initially, but adding a new data source requires
   modifying every agent that needs it, and there's no standard interface.

2. **Shared utility functions** — a `utils/apis.py` module that all agents import.
   Better than option 1, but still ad-hoc and not aligned with how Claude's
   tool-use interface works.

3. **MCPRegistry with named tools** — a central registry where agents request tools
   by name (`registry.get_tool("web_search")`). Backed by MCP servers that speak
   Claude's native tool-use protocol. Adding a new data source = one registry
   entry + one MCP server URL.

## Decision
Build a central `MCPRegistry` in `backend/app/mcp/registry.py`. All agents request
tools by name. The registry initialises MCP clients at startup and provides a
uniform interface regardless of the underlying data source.

## Consequences
**Positive:**
- Adding a new data source is a one-line registry change, not per-agent code changes
- Aligns with Claude's native MCP tool-use interface — no adapter layer needed
- Registry can enforce rate limits, circuit breakers, and fallbacks in one place
- Easy to mock for unit tests (replace registry tools with stubs)

**Negative:**
- Adds an abstraction layer — engineers must understand the registry to add tools
- MCP server URLs must be maintained in environment config
- Tool discovery at startup means MCP servers must be reachable before the backend accepts requests

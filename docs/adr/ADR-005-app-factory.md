# ADR-005 — App factory pattern for FastAPI

## Status
Accepted

## Context
FastAPI applications are commonly initialised as a module-level global:

```python
# common but problematic pattern
app = FastAPI()
```

This creates a single shared `app` instance for the entire process lifetime.
When running tests, every test imports the same `app`, inheriting any state
from previous tests (database connections, registered routes, middleware config).

Options considered:
1. **Module-level `app = FastAPI()`** — simple, but causes test pollution and
   makes it impossible to vary configuration between tests.

2. **`create_app()` factory function** — returns a new `FastAPI` instance on
   each call. Used by uvicorn with `--factory` flag: `uvicorn app.main:create_app --factory`.

## Decision
Implement `create_app()` in `backend/app/main.py`. Every call returns a fresh
`FastAPI` instance with its own lifespan, middleware stack, and state.
Uvicorn runs it with `--factory`.

## Consequences
**Positive:**
- Each pytest test can call `create_app()` and get an isolated instance with no shared state
- Configuration can vary per instance (e.g. test DB URL injected via environment)
- Lifespan startup/shutdown runs cleanly per instance — no leftover connections
- Standard pattern in production FastAPI applications

**Negative:**
- `uvicorn` must be called with `--factory` flag — easy to forget, documented in Makefile
- Slightly more verbose than the module-level pattern

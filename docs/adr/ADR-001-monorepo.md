# ADR-001 — Monorepo with pnpm workspaces

## Status
Accepted

## Context
wandr-ai has three distinct packages that must share TypeScript types:
- `backend/` — Python / FastAPI (no JS)
- `frontend/` — Next.js app consuming shared types
- `shared/` — TypeScript type definitions used by both frontend and any future JS tooling

Options considered:
1. **Separate repos** — independent versioning, but sharing types requires an npm publish step on every change
2. **pnpm workspaces monorepo** — all packages in one repo, types importable as `@wandr/shared` without publishing
3. **npm/yarn workspaces** — similar to pnpm but with weaker dependency isolation

## Decision
Use a pnpm workspace monorepo with `backend/`, `frontend/`, and `shared/` at the repo root.

## Consequences
**Positive:**
- `@wandr/shared` importable in frontend without any publish step
- pnpm strict dep resolution prevents phantom dependency bugs (a package can only import what it explicitly declares)
- Single `git clone` to get a working dev environment
- One CI pipeline covers all packages

**Negative:**
- All packages must be cloned together — acceptable for a single-team project
- Python backend lives alongside Node packages; engineers must know to use `backend/.venv` for Python deps, not the root `node_modules`

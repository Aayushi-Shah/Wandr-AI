.PHONY: dev dev-workers dev-build dev-down dev-logs \
        dev-backend dev-frontend \
        test test-backend test-frontend \
        migrate migration lint

# ── Docker Compose ────────────────────────────────────────────────────────────

dev:                          ## Start all core services (postgres, redis, jaeger, backend, frontend)
	docker compose up

dev-workers:                  ## Also start Celery worker + Flower (requires P1.7)
	docker compose --profile worker up

dev-build:                    ## Rebuild images before starting
	docker compose build

dev-down:                     ## Stop and remove containers (keeps volumes)
	docker compose down

dev-logs:                     ## Tail logs for all services
	docker compose logs -f

# ── Local (no Docker) ─────────────────────────────────────────────────────────

dev-backend:                  ## FastAPI with hot reload (activate backend/.venv first)
	cd backend && uvicorn app.main:create_app --factory --reload --port 8000

dev-frontend:                 ## Next.js dev server
	pnpm --filter @wandr/frontend dev

# ── Tests ─────────────────────────────────────────────────────────────────────

test: test-backend test-frontend

test-backend:                 ## pytest (activate backend/.venv first)
	cd backend && python -m pytest tests/ -x -q

test-frontend:                ## Playwright E2E
	pnpm --filter @wandr/frontend exec playwright test

# ── Database ──────────────────────────────────────────────────────────────────

migrate:                      ## alembic upgrade head
	cd backend && alembic upgrade head

migration:                    ## alembic revision --autogenerate -m "msg"
	cd backend && alembic revision --autogenerate -m "$(msg)"

# ── Lint ─────────────────────────────────────────────────────────────────────

lint:                         ## ruff (backend) + eslint (frontend)
	cd backend && source .venv/bin/activate && ruff check app/ tests/
	pnpm --filter @wandr/frontend run lint

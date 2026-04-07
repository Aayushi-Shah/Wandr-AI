.PHONY: dev dev-backend dev-frontend test test-backend test-frontend migrate migration lint

dev:
	docker-compose up

dev-backend:
	cd backend && uvicorn app.main:create_app --factory --reload --port 8000

dev-frontend:
	pnpm --filter @wandr/frontend dev

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest tests/ -x -q

test-frontend:
	pnpm --filter @wandr/frontend exec playwright test

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m "$(msg)"

lint:
	cd backend && ruff check app/ tests/
	pnpm --filter @wandr/frontend exec eslint src/ --max-warnings 0

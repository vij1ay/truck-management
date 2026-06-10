BACKEND_DIR := apps/backend
FRONTEND_DIR := apps/admin-frontend

.PHONY: dev stop setup migrate seed test test-cov lint dev-backend dev-frontend \
        docker-migrate docker-seed docker-shell help

help:
	@echo "Docker workflow (recommended):"
	@echo "  make dev             Start full stack (postgres + backend + frontend)"
	@echo "  make setup           First-time init: migrate + seed inside Docker"
	@echo "  make stop            Stop and remove containers"
	@echo "  make docker-migrate  Run Alembic migrations inside backend container"
	@echo "  make docker-seed     Seed roles + SuperAdmin inside backend container"
	@echo "  make docker-shell    Open a shell inside the backend container"
	@echo ""
	@echo "Local workflow (no Docker):"
	@echo "  make migrate         Run Alembic migrations locally"
	@echo "  make seed            Seed data locally"
	@echo "  make dev-backend     Start backend dev server locally"
	@echo "  make dev-frontend    Start Angular dev server locally"
	@echo ""
	@echo "Quality:"
	@echo "  make test            Run backend tests"
	@echo "  make test-cov        Run tests with coverage report"
	@echo "  make lint            Lint backend with ruff"

# ── Docker workflow ────────────────────────────────────────────────────────────

dev:
	docker compose up --build

stop:
	docker compose down

setup: docker-migrate docker-seed
	@echo "Initial setup complete."

docker-migrate:
	docker compose exec backend alembic upgrade head

docker-seed:
	docker compose exec backend python -m app.scripts.seed_data

docker-shell:
	docker compose exec backend /bin/bash

# ── Local workflow ─────────────────────────────────────────────────────────────

migrate:
	cd $(BACKEND_DIR) && alembic upgrade head

seed:
	cd $(BACKEND_DIR) && python -m app.scripts.seed_data

dev-backend:
	cd $(BACKEND_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && npm start

# ── Quality ────────────────────────────────────────────────────────────────────

test:
	cd $(BACKEND_DIR) && python -m pytest tests/ -v --tb=short -p no:warnings

test-cov:
	cd $(BACKEND_DIR) && python -m pytest tests/ --cov=app --cov-report=term-missing

lint:
	cd $(BACKEND_DIR) && ruff check app/

.PHONY: help install setup-hooks serve serve-front gensynth phoenix db db-stop db-reset db-migrate validate-ui test test-fast test-full test-unit test-integration test-contract lint-format clean

# =============================================================================
# Configuration
# =============================================================================
ENV ?= dev

# PostgreSQL (via Podman)
POSTGRES_CONTAINER := synthlab-postgres
POSTGRES_USER := synthlab
POSTGRES_PASSWORD := synthlab
POSTGRES_DB := synthlab
POSTGRES_PORT := 5432
DATABASE_URL := postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost:$(POSTGRES_PORT)/$(POSTGRES_DB)

# Alembic
ALEMBIC_CONFIG := src/synth_lab/alembic/alembic.ini

# Environment-based settings
ifeq ($(ENV),dev)
    PHOENIX_ENABLED := true
    LOG_LEVEL := DEBUG
    UVICORN_RELOAD := --reload
    BACKEND_LOG := /tmp/synth-lab-backend.log
    FRONTEND_LOG := /tmp/synth-lab-frontend.log
    TEE_BACKEND := 2>&1 | tee $(BACKEND_LOG)
    TEE_FRONTEND := 2>&1 | tee $(FRONTEND_LOG)
else
    PHOENIX_ENABLED := false
    LOG_LEVEL := INFO
    UVICORN_RELOAD :=
    TEE_BACKEND :=
    TEE_FRONTEND :=
endif

# =============================================================================
# Help
# =============================================================================
help:
	@echo "synth-lab Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install dependencies"
	@echo "  make setup-hooks  Configure Git hooks"
	@echo ""
	@echo "Database (PostgreSQL):"
	@echo "  make db           Start PostgreSQL + apply migrations"
	@echo "  make db-stop      Stop PostgreSQL"
	@echo "  make db-reset     Reset database (drop + recreate schema)"
	@echo "  make db-migrate   Create migration: make db-migrate MSG='description'"
	@echo ""
	@echo "Development:"
	@echo "  make serve        Start API server (port 8000)"
	@echo "  make serve-front  Start frontend (port 8080)"
	@echo "  make phoenix      Start Phoenix tracing (port 6006)"
	@echo "  make gensynth     Generate synths: make gensynth ARGS='-n 3'"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-fast    Run unit tests only"
	@echo "  make test-full    Run all tests verbose"
	@echo ""
	@echo "Other:"
	@echo "  make lint-format  Run ruff linter and formatter"
	@echo "  make clean        Remove cache files"

# =============================================================================
# Setup
# =============================================================================
install:
	uv sync

setup-hooks:
	@git config core.hooksPath .githooks
	@echo "✅ Git hooks configured"

# =============================================================================
# Database (PostgreSQL via Podman)
# =============================================================================
db:
	@if podman ps --format "{{.Names}}" | grep -q "^$(POSTGRES_CONTAINER)$$"; then \
		echo "PostgreSQL already running"; \
	elif podman ps -a --format "{{.Names}}" | grep -q "^$(POSTGRES_CONTAINER)$$"; then \
		echo "Starting PostgreSQL..."; \
		podman start $(POSTGRES_CONTAINER); \
	else \
		echo "Creating PostgreSQL container..."; \
		podman run -d \
			--name $(POSTGRES_CONTAINER) \
			-e POSTGRES_USER=$(POSTGRES_USER) \
			-e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
			-e POSTGRES_DB=$(POSTGRES_DB) \
			-p $(POSTGRES_PORT):5432 \
			postgres:14-alpine; \
		sleep 2; \
	fi
	@echo "Applying migrations..."
	@DATABASE_URL="$(DATABASE_URL)" uv run alembic -c $(ALEMBIC_CONFIG) upgrade head
	@echo ""
	@echo "✅ Database ready!"
	@echo "   $(DATABASE_URL)"

db-stop:
	@podman stop $(POSTGRES_CONTAINER) 2>/dev/null || true
	@echo "✅ PostgreSQL stopped"

db-reset:
	@echo "Resetting database schema..."
	@DATABASE_URL="$(DATABASE_URL)" uv run alembic -c $(ALEMBIC_CONFIG) downgrade base
	@DATABASE_URL="$(DATABASE_URL)" uv run alembic -c $(ALEMBIC_CONFIG) upgrade head
	@echo "✅ Database reset complete"

db-migrate:
ifndef MSG
	$(error Usage: make db-migrate MSG="description")
endif
	@DATABASE_URL="$(DATABASE_URL)" uv run alembic -c $(ALEMBIC_CONFIG) revision --autogenerate -m "$(MSG)"
	@echo "✅ Migration created. Review before applying."

# =============================================================================
# Development
# =============================================================================
serve:
	@echo "API: http://127.0.0.1:$(or $(PORT),8000)/docs"
	DATABASE_URL="$(DATABASE_URL)" PHOENIX_ENABLED=$(PHOENIX_ENABLED) LOG_LEVEL=$(LOG_LEVEL) \
		uv run uvicorn synth_lab.api.main:app --host 127.0.0.1 --port $(or $(PORT),8000) $(UVICORN_RELOAD) $(TEE_BACKEND)

serve-front:
	@echo "Frontend: http://localhost:$(or $(FRONT_PORT),8080)"
	@cd frontend && VITE_PORT=$(or $(FRONT_PORT),8080) VITE_API_PORT=$(or $(PORT),8000) pnpm dev $(TEE_FRONTEND)

gensynth:
	DATABASE_URL="$(DATABASE_URL)" PHOENIX_ENABLED=$(PHOENIX_ENABLED) LOG_LEVEL=$(LOG_LEVEL) uv run synthlab gensynth $(ARGS)

phoenix:
	@echo "Phoenix: http://127.0.0.1:6006"
	uv run python -m phoenix.server.main serve

# =============================================================================
# Testing
# =============================================================================
test:
	POSTGRES_URL="$(DATABASE_URL)" uv run pytest

test-fast:
	uv run pytest tests/unit/ -q --tb=short

test-full:
	POSTGRES_URL="$(DATABASE_URL)" uv run pytest tests/ -v --tb=short

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	POSTGRES_URL="$(DATABASE_URL)" uv run pytest tests/integration/ -v

test-contract:
	uv run pytest tests/contract/ -v

# =============================================================================
# Other
# =============================================================================
lint-format:
	uv run ruff check . --fix
	uv run ruff format .

validate-ui:
	uv run python scripts/validate_ui.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__ htmlcov dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

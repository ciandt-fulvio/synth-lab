.PHONY: help install setup-hooks serve serve-front serve-test serve-front-test gensynth phoenix kill kill-server kill-test-servers db db-stop db-reset db-migrate db-test db-test-reset validate-ui test test-fast test-full test-unit test-integration test-contract test-e2e test-e2e-ui lint-format update-docs clean clean-server

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

# Test database (ISOLATED - never use production/dev DB for tests!)
POSTGRES_TEST_DB := synthlab_test
DATABASE_TEST_URL := postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost:$(POSTGRES_PORT)/$(POSTGRES_TEST_DB)

# Test server ports (to avoid conflicts with dev servers)
TEST_BACKEND_PORT := 8000
TEST_FRONTEND_PORT := 8080

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
	@echo "  make db-test      Setup isolated test database (for running tests)"
	@echo "  make db-test-reset Reset test database"
	@echo ""
	@echo "Development:"
	@echo "  make serve             Start API server (port 8000)"
	@echo "  make serve-front       Start frontend (port 8080)"
	@echo "  make serve-test        Start API server for tests (port 8000)"
	@echo "  make serve-front-test  Start frontend for tests (port 8080)"
	@echo "  make phoenix           Start Phoenix tracing (port 6006)"
	@echo "  make kill              Kill all dev servers (ports 8000, 8080, 6006)"
	@echo "  make kill-test-servers Kill test servers (ports 8000, 8080)"
	@echo "  make gensynth          Generate synths: make gensynth ARGS='-n 3'"
	@echo ""
	@echo "Testing:"
	@echo "  make test                    Run all tests"
	@echo "  make test-fast               Run fast anti-regression tests (~30s: smoke+contract+schema)"
	@echo "  make test-full               Run all tests verbose"
	@echo "  make test-e2e                Run E2E tests (requires servers running on ports 8000/8080)"
	@echo "  make test-e2e-ui             Run E2E tests in UI mode"
	@echo "  make test-coverage-analysis  Analyze test coverage gaps (suggests Claude prompts)"
	@echo ""
	@echo "Documentation:"
	@echo "  make update-docs  Update docs using Claude Code (auto-detect changes)"
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

db-test:
	@echo "Setting up isolated test database..."
	@echo "Creating test database: $(POSTGRES_TEST_DB)"
	@podman exec -it $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -tc \
		"SELECT 1 FROM pg_database WHERE datname = '$(POSTGRES_TEST_DB)'" | grep -q 1 || \
		podman exec -it $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -c \
		"CREATE DATABASE $(POSTGRES_TEST_DB)"
	@echo "Applying migrations to test database..."
	@DATABASE_URL="$(DATABASE_TEST_URL)" uv run alembic -c $(ALEMBIC_CONFIG) upgrade head
	@echo ""
	@echo "✅ Test database ready!"
	@echo "   $(DATABASE_TEST_URL)"
	@echo ""
	@echo "⚠️  This database is for TESTS ONLY - data will be destroyed during tests!"

db-test-reset:
	@echo "Resetting test database schema..."
	@DATABASE_URL="$(DATABASE_TEST_URL)" uv run alembic -c $(ALEMBIC_CONFIG) downgrade base
	@DATABASE_URL="$(DATABASE_TEST_URL)" uv run alembic -c $(ALEMBIC_CONFIG) upgrade head
	@echo "✅ Test database reset complete"

# =============================================================================
# Development
# =============================================================================
serve: kill-server clean-server
	@echo "API: http://127.0.0.1:$(or $(PORT),8000)/docs"
	@exec env DATABASE_URL="$(DATABASE_URL)" PHOENIX_ENABLED=$(PHOENIX_ENABLED) LOG_LEVEL=$(LOG_LEVEL) \
		uv run uvicorn synth_lab.api.main:app --host 127.0.0.1 --port $(or $(PORT),8000) $(UVICORN_RELOAD) $(TEE_BACKEND)

serve-front:
	@echo "Frontend: http://localhost:$(or $(FRONT_PORT),8080)"
	@cd frontend && exec env VITE_PORT=$(or $(FRONT_PORT),8080) VITE_API_PORT=$(or $(PORT),8000) pnpm dev $(TEE_FRONTEND)

serve-test:
	@echo "Test API: http://127.0.0.1:$(TEST_BACKEND_PORT)/docs"
	@exec env DATABASE_URL="$(DATABASE_TEST_URL)" PHOENIX_ENABLED=false LOG_LEVEL=INFO \
		uv run uvicorn synth_lab.api.main:app --host 127.0.0.1 --port $(TEST_BACKEND_PORT)

serve-front-test:
	@echo "Test Frontend: http://localhost:$(TEST_FRONTEND_PORT)"
	@cd frontend && exec env VITE_PORT=$(TEST_FRONTEND_PORT) VITE_API_PORT=$(TEST_BACKEND_PORT) npm run dev:test

gensynth:
	DATABASE_URL="$(DATABASE_URL)" PHOENIX_ENABLED=$(PHOENIX_ENABLED) LOG_LEVEL=$(LOG_LEVEL) uv run synthlab gensynth $(ARGS)

phoenix:
	@echo "Phoenix: http://127.0.0.1:6006"
	@exec uv run python -m phoenix.server.main serve

kill:
	@echo "Killing dev servers..."
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:8080 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:6006 | xargs kill -9 2>/dev/null || true
	@echo "✅ Done"

kill-server:
	@echo "Killing backend server..."
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@echo "✅ Done"

kill-test-servers:
	@echo "Killing test servers..."
	@-lsof -ti:$(TEST_BACKEND_PORT) | xargs kill -9 2>/dev/null || true
	@-lsof -ti:$(TEST_FRONTEND_PORT) | xargs kill -9 2>/dev/null || true
	@echo "✅ Done"

# =============================================================================
# Testing
# =============================================================================
test:
	POSTGRES_URL="$(DATABASE_TEST_URL)" uv run pytest

test-fast:
	@echo "🚀 Running fast anti-regression tests..."
	@echo ""
	DATABASE_TEST_URL="$(DATABASE_TEST_URL)" uv run pytest -m "smoke or contract or schema" --maxfail=5 -q --tb=short

test-full:
	POSTGRES_URL="$(DATABASE_TEST_URL)" uv run pytest tests/ -v --tb=short

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	POSTGRES_URL="$(DATABASE_TEST_URL)" uv run pytest tests/integration/ -v

test-contract:
	uv run pytest tests/contract/ -v

test-e2e:
	@echo "🎭 Running E2E tests..."
	@echo "⚠️  Make sure test servers are running:"
	@echo "   Terminal 1: make serve-test"
	@echo "   Terminal 2: make serve-front-test"
	@echo ""
	@cd frontend && VITE_PORT=$(TEST_FRONTEND_PORT) npm run test:e2e

test-e2e-ui:
	@echo "🎭 Running E2E tests in UI mode..."
	@cd frontend && VITE_PORT=$(TEST_FRONTEND_PORT) npm run test:e2e:ui

test-coverage-analysis:
	@echo "📊 Analisando gaps de cobertura de testes..."
	@echo ""
	@uv run python scripts/analyze_test_coverage.py --suggest-claude-prompts

# =============================================================================
# Other
# =============================================================================
lint-format:
	uv run ruff check . --fix
	uv run ruff format .

validate-ui:
	uv run python scripts/validate_ui.py

# =============================================================================
# Documentation
# =============================================================================
update-docs:
	@./scripts/auto-update-docs.sh --last-commit

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__ htmlcov dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-server:
	@echo "Cleaning server logs..."
	@-rm -f $(BACKEND_LOG) 2>/dev/null || true
	@echo "✅ Done"

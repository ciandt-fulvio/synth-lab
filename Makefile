.PHONY: help install setup-hooks gensynth phoenix kill validate-ui test test-fast test-e2e test-e2e-docker test-e2e-docker-up test-e2e-docker-down test-e2e-docker-logs lint-format update-docs clean dev-up dev-down dev-logs-back dev-logs-front db-migrate

# =============================================================================
# Configuration
# =============================================================================

# Container runtime detection (Docker or Podman)
DOCKER_CMD := $(shell command -v docker 2> /dev/null)
PODMAN_CMD := $(shell command -v podman 2> /dev/null)

ifdef DOCKER_CMD
    CONTAINER_RUNTIME := docker
else ifdef PODMAN_CMD
    CONTAINER_RUNTIME := podman
else
    $(error Neither Docker nor Podman found. Please install one of them.)
endif

$(info 🐳 Using container runtime: $(CONTAINER_RUNTIME))

# Database URLs
# Dev: matches docker/.env.dev credentials (port 5432)
DATABASE_URL := postgresql://synthlab:synthlab_dev@localhost:5432/synthlab
# Test: matches docker/.env.test credentials (port 5433, ephemeral container)
DATABASE_URL_TEST := postgresql://synthlab_test:synthlab_test@localhost:5433/synthlab_test

# Alembic
ALEMBIC_CONFIG := src/synth_lab/alembic/alembic.ini

# Phoenix tracing
PHOENIX_ENABLED := true
LOG_LEVEL := DEBUG

# =============================================================================
# Help
# =============================================================================
help:
	@echo "synth-lab Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies"
	@echo "  make setup-hooks   Configure Git hooks"
	@echo ""
	@echo "Development (Docker):"
	@echo "  make dev-up         Start full stack (frontend:8080, backend:8000, postgres:5432)"
	@echo "  make dev-down       Stop Docker environment"
	@echo "  make dev-logs-back  View backend logs"
	@echo "  make dev-logs-front View frontend logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run unit/integration tests (requires dev-up)"
	@echo "  make test-fast     Run fast anti-regression tests (~30s)"
	@echo "  make test-e2e      Run E2E tests (isolated Docker environment)"
	@echo ""
	@echo "Observability:"
	@echo "  make phoenix       Start Phoenix tracing UI (http://localhost:6006)"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate    Create migration: make db-migrate MSG='description'"
	@echo ""
	@echo "Other:"
	@echo "  make gensynth      Generate synths: make gensynth ARGS='-n 3'"
	@echo "  make lint-format   Run ruff linter and formatter"
	@echo "  make kill          Kill processes on ports 8000, 8080, 6006"
	@echo "  make clean         Remove cache files"

# =============================================================================
# Setup
# =============================================================================
install:
	uv sync

setup-hooks:
	@git config core.hooksPath .githooks
	@echo "✅ Git hooks configured"

# =============================================================================
# Database
# =============================================================================
db-migrate:
ifndef MSG
	$(error Usage: make db-migrate MSG="description")
endif
	@DATABASE_URL="$(DATABASE_URL)" uv run alembic -c $(ALEMBIC_CONFIG) revision --autogenerate -m "$(MSG)"
	@echo "✅ Migration created. Review before applying."

# =============================================================================
# Tools
# =============================================================================
gensynth:
	DATABASE_URL="$(DATABASE_URL)" PHOENIX_ENABLED=$(PHOENIX_ENABLED) LOG_LEVEL=$(LOG_LEVEL) uv run synthlab gensynth $(ARGS)

phoenix:
	@echo "Phoenix: http://127.0.0.1:6006"
	@exec uv run python -m phoenix.server.main serve

kill:
	@echo "Killing processes on ports 8000, 8080, 6006..."
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:8080 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:6006 | xargs kill -9 2>/dev/null || true
	@echo "✅ Done"

# =============================================================================
# Testing
# =============================================================================

# Start test database container (ephemeral, no persistent data)
test-db-up:
	@echo "🐘 Starting test database container..."
	@$(CONTAINER_RUNTIME) compose -f docker/docker-compose.yml --profile test up postgres-test -d
	@echo "⏳ Waiting for postgres-test to be healthy..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		$(CONTAINER_RUNTIME) exec synthlab-postgres-test pg_isready -U synthlab_test -d synthlab_test >/dev/null 2>&1 && break || sleep 1; \
	done
	@echo "✅ Test database ready at localhost:5433"

test-db-down:
	@echo "🛑 Stopping test database container..."
	@$(CONTAINER_RUNTIME) compose -f docker/docker-compose.yml --profile test down postgres-test
	@echo "✅ Test database stopped"

test: test-db-up
	@echo "🧪 Running tests against isolated test database (port 5433)..."
	DATABASE_URL="$(DATABASE_URL_TEST)" uv run pytest
	@$(MAKE) test-db-down

test-fast: test-db-up
	@echo "🚀 Running fast anti-regression tests..."
	@echo ""
	DATABASE_URL="$(DATABASE_URL_TEST)" uv run pytest -m "smoke or contract or schema" --maxfail=5 -q --tb=short

# E2E Tests via Docker (isolated environment)
test-e2e: test-e2e-docker

test-e2e-docker:
	@echo "🎭 Running E2E tests (isolated environment)..."
	@echo "   Frontend: http://localhost:8091"
	@echo "   Backend:  http://localhost:8001"
	@echo "   Database: localhost:5433"
	@echo ""
	@./scripts/compose-e2e.sh up; \
	exit_code=$$?; \
	./scripts/compose-e2e.sh down; \
	exit $$exit_code

test-e2e-docker-up:
	@echo "🎭 Starting E2E environment..."
	@./scripts/compose-e2e.sh up-detached
	@echo ""
	@echo "✅ E2E environment running at:"
	@echo "   Frontend: http://localhost:8091"
	@echo "   Backend:  http://localhost:8001"
	@echo "   Database: localhost:5433"
	@echo ""
	@echo "To run tests: cd frontend && TEST_ENV=docker npm run test:e2e"
	@echo "To view logs: make test-e2e-docker-logs"
	@echo "To stop: make test-e2e-docker-down"

test-e2e-docker-down:
	@./scripts/compose-e2e.sh down

test-e2e-docker-logs:
	@./scripts/compose-e2e.sh logs

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

# =============================================================================
# Docker Development Environment
# =============================================================================

# Docker compose file location
COMPOSE_FILE := docker/docker-compose.yml

dev-up:
	@echo "🐳 Starting Docker development environment..."
	@echo "   Frontend: http://localhost:8080 (with HMR)"
	@echo "   Backend:  http://localhost:8000 (with hot reload)"
	@echo "   Database: localhost:5432"
	@echo ""
	@$(CONTAINER_RUNTIME) compose -f $(COMPOSE_FILE) --profile dev up -d
	@echo ""
	@echo "✅ Environment ready! Use 'make dev-logs-back e make dev-logs-front' to view logs"

dev-down:
	@echo "🛑 Stopping Docker development environment..."
	@$(CONTAINER_RUNTIME) compose -f $(COMPOSE_FILE) --profile dev down
	@echo "✅ Done"

dev-logs-back:
	@$(CONTAINER_RUNTIME) logs -f synthlab-backend-dev

dev-logs-front:
	@$(CONTAINER_RUNTIME) logs -f synthlab-frontend-dev

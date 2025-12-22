.PHONY: help install setup-hooks serve serve-front serve-traced phoenix init-db reset-db validate-ui test test-fast test-full test-unit test-integration test-contract lint-format clean

# Default target
help:
	@echo "synth-lab Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install dependencies with uv"
	@echo "  make setup-hooks  Configure Git hooks for automated testing"
	@echo "  make init-db      Initialize SQLite database with schema"
	@echo "  make reset-db     Delete and recreate database from scratch"
	@echo ""
	@echo "Development:"
	@echo "  make serve        Start FastAPI REST API server (port 8000)"
	@echo "  make serve-front  Start frontend dev server (port 8080)"
	@echo "  make serve-traced Start API with Phoenix tracing enabled"
	@echo "  make phoenix      Start Phoenix observability server (port 6006)"
	@echo "  make lint-format  Run ruff linter and formatter"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-fast    Run fast unit tests only (<5s, for commits)"
	@echo "  make test-full    Run comprehensive tests (for PRs)"
	@echo "  make test-unit    Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-contract     Run contract tests only"
	@echo ""
	@echo "Validation:"
	@echo "  make validate-ui  Validate trace visualizer UI files"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        Remove cache files and build artifacts"

# Setup
install:
	uv sync

setup-hooks:
	@echo "Configuring Git hooks..."
	@git config core.hooksPath .githooks
	@echo "✅ Git hooks configured!"
	@echo ""
	@echo "Hooks installed:"
	@echo "  - pre-commit: runs 'make test-fast' before each commit"
	@echo "  - pre-push: runs 'make test-full' before each push"
	@echo ""
	@echo "To bypass hooks (not recommended):"
	@echo "  git commit --no-verify"
	@echo "  git push --no-verify"

init-db:
	uv run python scripts/init_db.py

reset-db:
	@echo "Deleting existing database..."
	rm -f output/synthlab.db output/synthlab.db-wal output/synthlab.db-shm
	@echo "Creating new database..."
	uv run python scripts/init_db.py
	@echo "Database reset complete!"

# Development
serve:
	@echo "Starting synth-lab API on http://127.0.0.1:8000"
	@echo "OpenAPI docs: http://127.0.0.1:8000/docs"
	@echo ""
	uv run uvicorn synth_lab.api.main:app --host 127.0.0.1 --port 8000 --reload

serve-front:
	@echo "Starting frontend dev server on http://localhost:8080"
	@echo "API proxy: http://localhost:8000"
	@echo ""
	@cd frontend && pnpm dev

serve-traced:
	@echo "Starting synth-lab API with Phoenix tracing on http://127.0.0.1:8000"
	@echo "OpenAPI docs: http://127.0.0.1:8000/docs"
	@echo "Phoenix dashboard: http://127.0.0.1:6006"
	@echo ""
	@echo "TIP: Run 'make phoenix' in another terminal first!"
	@echo ""
	PHOENIX_ENABLED=true uv run uvicorn synth_lab.api.main:app --host 127.0.0.1 --port 8000 --reload

phoenix:
	@echo "Starting Phoenix observability server on http://127.0.0.1:6006"
	@echo ""
	uv run python -m phoenix.server.main serve

# Testing targets
test:
	uv run pytest

# Fast unit tests (<5s) - run on every commit
test-fast:
	uv run pytest tests/unit/ -q --tb=short

# Comprehensive tests - run before PRs
test-full:
	uv run pytest tests/ -v --tb=short

# Individual test suites
test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-contract:
	uv run pytest tests/contract/ -v

lint-format:
	uv run ruff check . --fix
	uv run ruff format .

# Validation
validate-ui:
	uv run python scripts/validate_ui.py

# Cleanup
clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

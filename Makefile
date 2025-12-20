.PHONY: help install serve init-db validate-ui test lint-format clean

# Default target
help:
	@echo "synth-lab Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install dependencies with uv"
	@echo "  make init-db      Initialize SQLite database with schema"
	@echo ""
	@echo "Development:"
	@echo "  make serve        Start FastAPI REST API server (port 8000)"
	@echo "  make test         Run pytest test suite"
	@echo "  make lint-format  Run ruff linter and formatter"
	@echo ""
	@echo "Validation:"
	@echo "  make validate-ui  Validate trace visualizer UI files"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        Remove cache files and build artifacts"

# Setup
install:
	uv sync

init-db:
	uv run python scripts/init_db.py

# Development
serve:
	@echo "Starting synth-lab API on http://127.0.0.1:8000"
	@echo "OpenAPI docs: http://127.0.0.1:8000/docs"
	@echo ""
	uv run uvicorn synth_lab.api.main:app --host 127.0.0.1 --port 8000 --reload

test:
	uv run pytest

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

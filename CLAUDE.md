# synth-lab Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-15

## Active Technologies
- Python 3.13+ + duckdb>=0.9.0, rich>=13.0.0 (already installed), typer>=0.9.0 (for CLI) (003-synth-query)
- DuckDB database file (`synths.duckdb`) created from JSON source (`data/synths/synths.json`) (003-synth-query)
- Python 3.13 + jsonschema>=4.20.0 (schema validation), faker>=21.0.0 (data generation), rich>=13.0.0 (output), typer>=0.9.0 (CLI) (004-simplify-synth-schema)
- JSON files (`data/schemas/synth-schema-cleaned.json` for schema definition, `data/synths/synths.json` for generated synths), DuckDB database (`synths.duckdb`) (004-simplify-synth-schema)
- Python 3.13+ (aligning with existing project) (005-ux-research-interviews)
- JSON files for transcripts (`data/transcripts/`), synths loaded from `data/synths/synths.json` (005-ux-research-interviews)
- Python 3.13 (matching project requirement) (006-topic-guides)
- File system (directories under `data/topic_guides/`), markdown files (`summary.md`) (006-topic-guides)
- Python 3.13+ + openai>=2.8.0 (API SDK), Pillow (image processing), rich (CLI output), existing synth-lab modules (008-synth-avatar-generation)
- File system (`data/synths/avatar/` directory for PNG files) (008-synth-avatar-generation)
- Python 3.13+ + FastAPI, uvicorn, SQLite (stdlib), openai>=2.8.0, openai-agents>=0.0.16, typer, rich, pydantic>=2.5.0 (010-rest-api)
- SQLite with JSON1 extension (single file: `output/synthlab.db`) (010-rest-api)
- Python 3.13+ + Typer (CLI framework), FastAPI (REST API), Pydantic>=2.5.0 (models), OpenAI SDK, DuckDB/SQLite (011-remove-cli-commands)
- SQLite database (`output/synthlab.db`) + file system for reports (`output/reports/`) (011-remove-cli-commands)
- TypeScript 5.5.3 + React 18.3.1 + Vite 6.3.4, shadcn/ui, TanStack React Query 5.56, React Router DOM 6.26, Tailwind CSS 3.4 (012-frontend-dashboard)
- N/A (frontend consome API REST do backend) (012-frontend-dashboard)

- Python 3.13+ + faker>=21.0.0, jsonschema>=4.20.0, rich (para output colorido) (002-synthlab-cli)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.13+: Follow standard conventions

## Recent Changes
- 012-frontend-dashboard: Added TypeScript 5.5.3 + React 18.3.1 + Vite 6.3.4, shadcn/ui, TanStack React Query 5.56, React Router DOM 6.26, Tailwind CSS 3.4
- 011-remove-cli-commands: Added Python 3.13+ + Typer (CLI framework), FastAPI (REST API), Pydantic>=2.5.0 (models), OpenAI SDK, DuckDB/SQLite
- 010-rest-api: Added Python 3.13+ + FastAPI, uvicorn, SQLite (stdlib), openai>=2.8.0, openai-agents>=0.0.16, typer, rich, pydantic>=2.5.0


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

# synth-lab Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-15

## Active Technologies
- Python 3.13+ + duckdb>=0.9.0, rich>=13.0.0 (already installed), typer>=0.9.0 (for CLI) (003-synth-query)
- DuckDB database file (`synths.duckdb`) created from JSON source (`data/synths/synths.json`) (003-synth-query)
- Python 3.13 + jsonschema>=4.20.0 (schema validation), faker>=21.0.0 (data generation), rich>=13.0.0 (output), typer>=0.9.0 (CLI) (004-simplify-synth-schema)
- JSON files (`data/schemas/synth-schema-cleaned.json` for schema definition, `data/synths/synths.json` for generated synths), DuckDB database (`synths.duckdb`) (004-simplify-synth-schema)

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
- 004-simplify-synth-schema: Added Python 3.13 + jsonschema>=4.20.0 (schema validation), faker>=21.0.0 (data generation), rich>=13.0.0 (output), typer>=0.9.0 (CLI)
- 003-synth-query: Added Python 3.13+ + duckdb>=0.9.0, rich>=13.0.0 (already installed), typer>=0.9.0 (for CLI)

- 002-synthlab-cli: Added Python 3.13+ + faker>=21.0.0, jsonschema>=4.20.0, rich (para output colorido)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

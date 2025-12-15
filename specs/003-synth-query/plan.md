# Implementation Plan: Synth Data Query Tool

**Branch**: `003-synth-query` | **Date**: 2025-12-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-synth-query/spec.md`

## Summary

Create a command-line query interface `listsynth` that allows users to view and filter synthetic data stored in `data/synths/synths.json` using DuckDB. The tool provides three modes: basic listing (no parameters), filtered queries (`--where` clause), and advanced custom SQL queries (`--full-query`). Data is loaded from JSON into a DuckDB table on first use and queried through SQL with results displayed in formatted tables.

**Technical Approach**: Use DuckDB to create an in-memory database from JSON data (`synths.duckdb`), load data using `read_json_auto()`, and execute user queries with formatted output via Rich library for table display.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: duckdb>=0.9.0, rich>=13.0.0 (already installed), typer>=0.9.0 (for CLI)
**Storage**: DuckDB database file (`synths.duckdb`) created from JSON source (`data/synths/synths.json`)
**Testing**: pytest with unit tests for query building, integration tests for database operations
**Target Platform**: Linux/macOS/Windows command-line environments
**Project Type**: Single project (extends existing synth-lab CLI)
**Performance Goals**: Query execution < 2 seconds for 10,000 records; table formatting < 1 second for 1,000 rows
**Constraints**: Read-only operations; must handle missing/invalid JSON gracefully; memory-efficient for large result sets
**Scale/Scope**: Support datasets up to 1 million records; queries returning up to 10,000 rows displayed efficiently

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Compliance

✅ **I. DRY (Don't Repeat Yourself)**:
- Query building logic will be centralized in a single function
- Database connection management will use a context manager pattern
- Table formatting will be reusable for all query types

✅ **II. Test-Driven Development (TDD)**:
- Will write tests BEFORE implementation for:
  - Query parameter validation
  - SQL query construction for each mode (basic/where/full-query)
  - Database initialization from JSON
  - Error handling for missing files, invalid JSON, SQL errors
- Red-Green-Refactor cycle will be followed strictly
- Minimum 80% coverage required

✅ **III. Type Safety and Explicit Contracts**:
- All functions will have complete type hints
- Will use native Python 3.13+ types (list[str], dict[str, Any])
- mypy strict mode compliance required

✅ **IV. Module Size and Organization**:
- Estimated modules (all < 500 lines):
  - `src/synth_lab/query/cli.py` (~150 lines): Typer CLI interface
  - `src/synth_lab/query/database.py` (~200 lines): DuckDB connection and initialization
  - `src/synth_lab/query/formatter.py` (~150 lines): Rich table formatting
  - `src/synth_lab/query/validator.py` (~100 lines): Parameter validation
- Functions-first approach; classes only for database connection management

✅ **V. Real Data Validation**:
- Each module will have `if __name__ == "__main__":` block
- Will test with actual generated synth data from `data/synths/synths.json`
- NO mocking of DuckDB or core query functionality
- Validation will verify actual query results against expected outputs

✅ **VI. Repository Pattern for Data Access**:
- N/A - This feature uses DuckDB for read-only queries, not ORM/SQLAlchemy
- Database operations encapsulated in `database.py` module

✅ **VII. Observability and Debugging**:
- Will use loguru for all logging
- Log database initialization, query execution, errors
- NO print() statements (use logger.info/debug/error)
- Structured logging with query parameters and row counts

### Additional Standards

✅ **Python Best Practices**:
- Python 3.13+ features
- pathlib.Path for file operations
- NO asyncio.run() inside functions
- Proper import ordering (stdlib → third-party → local)

✅ **Code Style**:
- ruff format (Black-compatible, 100 char line length)
- Google-style docstrings
- snake_case for functions/variables, PascalCase for classes

✅ **Testing Standards**:
- pytest with markers (@pytest.mark.unit, @pytest.mark.integration)
- Unit tests: fast, isolated, no database access
- Integration tests: real DuckDB operations with test JSON data
- Minimum 80% coverage

✅ **Git Workflow**:
- Feature branch: `003-synth-query`
- Frequent commits per phase
- Tests must pass before commits
- Conventional commit format

### Gate Status: ✅ PASSED

All constitutional requirements can be met. No violations or exceptions needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-synth-query/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (DuckDB best practices, Rich formatting)
├── data-model.md        # Phase 1 output (QueryRequest, QueryResult models)
├── quickstart.md        # Phase 1 output (Usage examples)
├── contracts/           # Phase 1 output (CLI interface contract)
│   └── cli-contract.md  # Command-line interface specification
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/synth_lab/
├── __init__.py
├── __main__.py          # Main CLI entry point (will import query commands)
├── gen_synth/           # Existing: synth generation modules
└── query/               # NEW: Query functionality
    ├── __init__.py
    ├── cli.py           # Typer CLI commands for listsynth
    ├── database.py      # DuckDB connection, initialization, query execution
    ├── formatter.py     # Rich table formatting for query results
    └── validator.py     # Input validation for query parameters

tests/
├── unit/
│   └── synth_lab/
│       └── query/       # NEW: Unit tests for query modules
│           ├── test_cli.py
│           ├── test_database.py
│           ├── test_formatter.py
│           └── test_validator.py
├── integration/
│   └── synth_lab/
│       └── query/       # NEW: Integration tests with real DuckDB
│           └── test_query_integration.py
└── fixtures/
    └── query/           # NEW: Test JSON data for queries
        ├── sample_synths.json
        └── invalid_synths.json

data/
└── synths/
    ├── synths.json      # Source data (from gen_synth feature)
    └── synths.duckdb    # DuckDB database (created on first run)
```

**Structure Decision**: Single project structure. The query functionality is a logical extension of the existing synth-lab CLI and will be integrated into the main `__main__.py` entry point. New modules under `src/synth_lab/query/` follow the existing pattern established by `gen_synth/`.

## Complexity Tracking

No constitutional violations. Table not needed.

---

## Phase 0: Research & Technical Decisions

### Research Tasks

1. **DuckDB JSON Loading Best Practices**
   - Research: How to efficiently load JSON with `read_json_auto()`
   - Research: Best practices for persistent vs in-memory DuckDB databases
   - Research: Performance implications of table recreation vs persistent storage
   - Decision needed: Should we recreate table on each run or persist the DuckDB file?

2. **DuckDB Query Patterns**
   - Research: Error handling patterns for DuckDB SQL errors
   - Research: Memory management for large result sets
   - Research: Best practices for parameterized queries in DuckDB

3. **Rich Table Formatting**
   - Research: Rich Table best practices for CLI output
   - Research: Handling wide tables (many columns)
   - Research: Pagination or truncation strategies for large result sets
   - Research: Unicode and special character handling in table cells

4. **CLI Integration with Typer**
   - Research: Mutually exclusive parameters in Typer (--where vs --full-query)
   - Research: Error message formatting best practices
   - Research: Exit codes for different error types

5. **Error Handling Strategies**
   - Research: User-friendly SQL error messages
   - Research: File not found vs invalid JSON error messaging
   - Research: Query timeout handling in DuckDB

### Technical Unknowns to Resolve

- How to initialize DuckDB database on first run?
- Should database be persistent or recreated each time?
- How to handle schema changes in synths.json?
- What's the best way to limit result set size to prevent memory issues?
- How to detect and handle corrupt DuckDB files?

**Output**: `research.md` with all decisions documented

---

## Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

### Data Models

**Extract from spec**: QueryRequest (user input), QueryResult (output), SynthRecord (data schema)

**Output**: `data-model.md` with:
- QueryRequest: mode (basic/where/full-query), where_clause (optional), full_query (optional)
- QueryResult: columns (list[str]), rows (list[dict]), row_count (int)
- DatabaseConfig: db_path, json_path, table_name
- Validation rules for query parameters

### API Contracts

**Extract from functional requirements**:
- FR-001: CLI command named `listsynth`
- FR-002: `--where` parameter (optional, string)
- FR-003: `--full-query` parameter (optional, string)
- FR-004: Mutual exclusivity validation

**Output**: `contracts/cli-contract.md` with:
- Command signature: `listsynth [--where TEXT] [--full-query TEXT]`
- Parameter descriptions and validation rules
- Exit codes: 0 (success), 1 (user error), 2 (system error)
- Output format specification (Rich table)
- Error message formats

### Quick Start Guide

**Output**: `quickstart.md` with:
- Installation: `uv pip install -e .` (DuckDB will be added to dependencies)
- Basic usage: `synthlab listsynth`
- Filtered query: `synthlab listsynth --where "age > 30"`
- Custom query: `synthlab listsynth --full-query "SELECT city, COUNT(*) FROM synths GROUP BY city"`
- Error scenarios and troubleshooting

### Agent Context Update

Run: `.specify/scripts/bash/update-agent-context.sh claude`

Will add to CLAUDE.md:
- `duckdb>=0.9.0` (new dependency)
- `typer>=0.9.0` (new dependency)
- Command: `synthlab listsynth [options]`

**Outputs**:
- `data-model.md`
- `contracts/cli-contract.md`
- `quickstart.md`
- Updated `CLAUDE.md`

---

## Phase 2: Implementation Planning

**Prerequisites**: Phase 0 and Phase 1 complete, Constitution Check re-verified

**Output**: Task list generation deferred to `/speckit.tasks` command

This plan document serves as input for `/speckit.tasks`, which will:
1. Read this plan + spec
2. Generate dependency-ordered tasks in `tasks.md`
3. Follow TDD workflow from constitution
4. Create tasks for each module with test-first approach

---

## Notes

### User-Provided Technical Guidance

From user input, the data loading approach is specified:

```python
import duckdb

con = duckdb.connect("synths.duckdb")

con.execute("""
CREATE TABLE synths AS
SELECT *
FROM read_json_auto('data/synths/synths.json')
""")
```

Query pattern:
```sql
SELECT *
FROM synths
<WHERE <parameter if available>>
```

**Decision**: Use persistent DuckDB file (`synths.duckdb`) rather than in-memory database. This improves performance on subsequent runs and avoids re-parsing JSON each time.

**Additional Considerations**:
- Need to handle case where synths.json is updated (detect and recreate table)
- Need to handle case where synths.duckdb exists but synths.json is missing
- Should validate synths.json modification time vs database creation time

### Integration Points

This feature integrates with:
- `gen_synth` feature: Reads output from `data/synths/synths.json`
- Existing CLI (`__main__.py`): Add `listsynth` command to main CLI group

### Risk Areas

1. **Large result sets**: Need to handle queries returning millions of rows
2. **Schema evolution**: synths.json schema may change over time
3. **Concurrent access**: Multiple listsynth commands running simultaneously
4. **Corrupt database**: DuckDB file corruption handling

### Success Metrics

From spec success criteria:
- Query execution < 2 seconds for 10,000 records (SC-001)
- 100% accuracy for WHERE parameter (SC-002)
- Correct results for all valid SELECT statements (SC-003)
- Helpful error messages for 100% of invalid queries (SC-004)
- Readable output for 0-1,000 rows (SC-005)
- 95% first-attempt success rate (SC-006)

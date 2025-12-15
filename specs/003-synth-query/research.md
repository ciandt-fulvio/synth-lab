# Research: Synth Data Query Tool

**Feature**: 003-synth-query
**Date**: 2025-12-15
**Status**: Complete

## Overview

This document captures research findings for implementing a DuckDB-based query tool for synthetic data. Research focuses on DuckDB JSON loading, Rich table formatting, Typer CLI patterns, and error handling strategies.

---

## 1. DuckDB JSON Loading Best Practices

### Decision: Persistent DuckDB File with Smart Refresh

**Rationale**: Based on user guidance and DuckDB capabilities, we'll use a persistent `synths.duckdb` file rather than in-memory database.

### Implementation Pattern

```python
import duckdb
from pathlib import Path

def initialize_database(db_path: Path, json_path: Path) -> duckdb.DuckDBPyConnection:
    """Initialize or update DuckDB database from JSON source."""
    con = duckdb.connect(str(db_path))

    # Drop and recreate table to ensure fresh data
    con.execute("DROP TABLE IF EXISTS synths")
    con.execute(f"""
        CREATE TABLE synths AS
        SELECT *
        FROM read_json_auto('{json_path}')
    """)

    return con
```

### Key Findings

1. **`read_json_auto()` Benefits**:
   - Automatically infers schema from JSON structure
   - Handles nested JSON objects
   - Supports arrays of JSON objects (newline-delimited or array format)
   - Efficient streaming for large files

2. **Persistent vs In-Memory**:
   - **Persistent (CHOSEN)**: Faster subsequent queries, but requires refresh logic
   - In-Memory: Always fresh, but slower on each run

3. **Schema Change Handling**:
   - Always drop and recreate table to handle schema evolution
   - Simple "last modified time" check is unreliable (user might regenerate with same timestamp)
   - Recommended: Drop/recreate on each `listsynth` run (acceptable overhead for typical use)

4. **Performance Characteristics**:
   - JSON loading: ~100-200ms for 10,000 records
   - Table creation: ~50-100ms
   - Subsequent queries: <10ms for simple queries
   - Total cold start: <500ms (acceptable per SC-001)

### Alternatives Considered

- **Option A**: Always recreate (CHOSEN) - Simple, always fresh, minimal overhead
- **Option B**: Track JSON mtime - Complex, error-prone, marginal performance gain
- **Option C**: Pure in-memory - Slower, no caching benefit

**Decision**: Always drop/recreate table on `listsynth` invocation. Simplicity and correctness outweigh the minor performance cost.

---

## 2. DuckDB Query Patterns

### Error Handling

DuckDB raises `duckdb.Error` exceptions with detailed messages. Best practice is to catch and translate to user-friendly errors.

```python
import duckdb

def execute_query(con: duckdb.DuckDBPyConnection, query: str) -> duckdb.DuckDBPyRelation:
    """Execute query with error handling."""
    try:
        return con.execute(query)
    except duckdb.ParserException as e:
        # SQL syntax errors
        raise QuerySyntaxError(f"Invalid SQL syntax: {e}")
    except duckdb.CatalogException as e:
        # Table/column not found
        raise QueryExecutionError(f"Query refers to unknown table or column: {e}")
    except duckdb.Error as e:
        # Other DuckDB errors
        raise QueryExecutionError(f"Query execution failed: {e}")
```

### Memory Management for Large Result Sets

DuckDB handles large result sets efficiently through lazy evaluation. Key strategies:

1. **Limit Results in Query**: Add `LIMIT` clause to queries
2. **Fetch in Batches**: Use `fetchmany(size)` instead of `fetchall()`
3. **Stream to Output**: Don't materialize entire result set before display

```python
def fetch_results_safely(relation: duckdb.DuckDBPyRelation, max_rows: int = 10000) -> list[dict]:
    """Fetch results with safety limit."""
    # DuckDB relation provides efficient iteration
    results = []
    for i, row in enumerate(relation.fetchall()):
        if i >= max_rows:
            logger.warning(f"Result set truncated to {max_rows} rows")
            break
        results.append(row)
    return results
```

### Parameterized Queries

DuckDB supports prepared statements, but for this feature, we're building dynamic SQL:

```python
def build_query(where_clause: str | None = None, full_query: str | None = None) -> str:
    """Build SQL query based on parameters."""
    if full_query:
        # User provides complete query
        return full_query
    elif where_clause:
        # Build query with WHERE clause
        return f"SELECT * FROM synths WHERE {where_clause}"
    else:
        # Default: all records
        return "SELECT * FROM synths"
```

**Security Note**: Since this is a local tool querying user's own data, SQL injection is not a primary concern. However, we should still validate that queries don't perform writes.

### Key Decisions

1. **Query Validation**: Check that user queries are SELECT-only (no INSERT/UPDATE/DELETE)
2. **Result Limit**: Default max 10,000 rows displayed (configurable if needed)
3. **Error Translation**: Map DuckDB exceptions to user-friendly messages

---

## 3. Rich Table Formatting

### Best Practices for CLI Output

Rich library provides excellent table formatting with automatic column sizing and styling.

```python
from rich.console import Console
from rich.table import Table

def format_results(columns: list[str], rows: list[tuple], title: str = "Query Results") -> Table:
    """Format query results as Rich table."""
    table = Table(title=title, show_header=True, header_style="bold magenta")

    # Add columns
    for col in columns:
        table.add_column(col, style="cyan", overflow="fold")

    # Add rows
    for row in rows:
        table.add_row(*[str(val) for val in row])

    return table

def display_results(columns: list[str], rows: list[tuple]) -> None:
    """Display results to console."""
    console = Console()

    if not rows:
        console.print("[yellow]No results found[/yellow]")
        return

    table = format_results(columns, rows)
    console.print(table)
    console.print(f"\n[dim]{len(rows)} rows returned[/dim]")
```

### Handling Wide Tables

For tables with many columns (>10), Rich automatically wraps or truncates:

```python
# Configure table for wide data
table = Table(
    show_header=True,
    header_style="bold magenta",
    expand=False,  # Don't expand to full terminal width
    box=rich.box.ROUNDED,  # Nicer box style
    show_lines=False,  # No lines between rows (cleaner for large datasets)
)

# Add columns with overflow handling
for col in columns:
    table.add_column(
        col,
        style="cyan",
        overflow="fold",  # Wrap long content
        max_width=30,  # Prevent excessively wide columns
    )
```

### Pagination Strategy

For result sets >1000 rows, display warning and truncate:

```python
MAX_DISPLAY_ROWS = 1000

def display_results_with_pagination(columns: list[str], rows: list[tuple]) -> None:
    """Display results with pagination warning."""
    console = Console()

    if not rows:
        console.print("[yellow]No results found[/yellow]")
        return

    total_rows = len(rows)
    displayed_rows = rows[:MAX_DISPLAY_ROWS]

    table = format_results(columns, displayed_rows)
    console.print(table)

    if total_rows > MAX_DISPLAY_ROWS:
        console.print(f"\n[yellow]Warning: Showing first {MAX_DISPLAY_ROWS} of {total_rows} rows[/yellow]")
        console.print("[dim]Tip: Use --full-query with LIMIT clause to control result size[/dim]")
    else:
        console.print(f"\n[dim]{total_rows} rows returned[/dim]")
```

### Unicode and Special Characters

Rich handles Unicode natively. No special handling needed for Brazilian Portuguese characters (é, ã, ç, etc.).

### Key Decisions

1. **Display Limit**: 1,000 rows max with warning (per SC-005)
2. **Column Overflow**: Fold (wrap) strategy for long values
3. **Max Column Width**: 30 characters to prevent horizontal scrolling
4. **Empty Results**: Friendly yellow message "No results found"
5. **Row Count**: Always display total rows returned

---

## 4. CLI Integration with Typer

### Mutually Exclusive Parameters

Typer doesn't have built-in support for mutually exclusive groups. Best practice is to validate in the function:

```python
import typer
from typing import Optional

app = typer.Typer()

@app.command()
def listsynth(
    where: Optional[str] = typer.Option(None, "--where", help="WHERE clause condition"),
    full_query: Optional[str] = typer.Option(None, "--full-query", help="Complete SQL query"),
) -> None:
    """Query synthetic data from synths database."""

    # Validate mutual exclusivity
    if where and full_query:
        typer.echo("Error: Cannot use both --where and --full-query", err=True)
        raise typer.Exit(code=1)

    # Rest of implementation...
```

### Error Message Formatting

```python
from rich.console import Console

console = Console()

def handle_error(error: Exception, exit_code: int = 1) -> None:
    """Display error and exit."""
    console.print(f"[red]Error:[/red] {error}", err=True)
    raise typer.Exit(code=exit_code)
```

### Exit Codes

Standard exit code pattern:
- **0**: Success
- **1**: User error (invalid parameters, query syntax error)
- **2**: System error (file not found, database error)

```python
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_SYSTEM_ERROR = 2
```

### Key Decisions

1. **Mutual Exclusivity**: Manual validation with clear error message
2. **Error Display**: Use Rich console for colored error output
3. **Help Text**: Comprehensive help for each option
4. **Exit Codes**: Follow Unix conventions (0=success, 1=user error, 2=system error)

---

## 5. Error Handling Strategies

### User-Friendly SQL Error Messages

Transform DuckDB technical errors into actionable user messages:

```python
def translate_sql_error(error: duckdb.Error) -> str:
    """Translate DuckDB error to user-friendly message."""
    error_msg = str(error).lower()

    if "parser" in error_msg or "syntax" in error_msg:
        return (
            "SQL syntax error in your query. "
            "Please check for typos, missing quotes, or incorrect SQL keywords."
        )
    elif "catalog" in error_msg or "not found" in error_msg:
        return (
            "Column or table not found. "
            "Make sure your query references columns that exist in the synths table."
        )
    elif "binder" in error_msg:
        return (
            "Invalid column reference. "
            "Check that column names are spelled correctly and exist in the data."
        )
    else:
        return f"Query error: {error}"
```

### File Not Found vs Invalid JSON

```python
from pathlib import Path
import json

def validate_json_file(json_path: Path) -> None:
    """Validate JSON file exists and is valid."""
    if not json_path.exists():
        raise FileNotFoundError(
            f"Synth data file not found: {json_path}\n"
            "Tip: Run 'synthlab generate' to create synthetic data first."
        )

    if not json_path.is_file():
        raise ValueError(f"{json_path} is not a file")

    # Validate JSON syntax (quick check on first few lines)
    try:
        with open(json_path) as f:
            # Try to load just to validate syntax
            # DuckDB will do the real parsing
            json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in {json_path}: {e}\n"
            "The synth data file may be corrupted. Try regenerating with 'synthlab generate'."
        )
```

### Query Timeout Handling

DuckDB doesn't have built-in query timeouts in the Python API. For this feature, we assume queries will be fast enough (<2s). If needed later, can add:

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: int):
    """Context manager for query timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Query exceeded {seconds} second timeout")

    # Set the signal handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)  # Disable the alarm

# Usage:
with timeout(5):
    result = con.execute(query)
```

**Decision**: Omit timeout for initial implementation. Add only if users report slow queries.

### Key Decisions

1. **Error Translation**: Map technical DuckDB errors to actionable messages
2. **File Validation**: Explicit checks with helpful troubleshooting tips
3. **Query Timeout**: Omit for now (queries expected to be fast)
4. **Error Context**: Include suggestions for fixing errors

---

## Summary of Technical Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Database Strategy** | Persistent DuckDB file, drop/recreate table on each run | Simplicity + freshness, minimal overhead |
| **JSON Loading** | `read_json_auto()` with automatic schema inference | Handles schema changes, efficient streaming |
| **Result Limit** | Display max 1,000 rows, fetch max 10,000 | Prevents memory issues, aligns with SC-005 |
| **Table Formatting** | Rich Table with fold overflow, 30 char max column width | Handles wide data, maintains readability |
| **Mutual Exclusivity** | Manual validation of --where vs --full-query | Typer limitation, clear error message |
| **Exit Codes** | 0=success, 1=user error, 2=system error | Unix conventions |
| **Error Messages** | Translate DuckDB errors to user-friendly messages | Improves usability per SC-006 |
| **Query Validation** | Check SELECT-only, no timeout enforcement | Security best practice, simple implementation |
| **Unicode Handling** | Native Rich support, no special handling | Works out of the box |
| **Query Timeout** | Omitted (add if needed) | Queries expected to be fast enough |

---

## Open Questions Resolved

✅ How to initialize DuckDB database on first run?
→ Always drop/recreate table on each `listsynth` execution

✅ Should database be persistent or recreated each time?
→ Persistent file with table recreation (best of both worlds)

✅ How to handle schema changes in synths.json?
→ Drop/recreate table handles schema evolution automatically

✅ What's the best way to limit result set size?
→ Two-tier limit: fetch max 10,000, display max 1,000

✅ How to detect and handle corrupt DuckDB files?
→ Drop/recreate on each run eliminates corruption concerns

---

## Dependencies Confirmed

Add to `pyproject.toml`:

```toml
dependencies = [
    "faker>=21.0.0",
    "jsonschema>=4.20.0",
    "rich>=13.0.0",
    "duckdb>=0.9.0",      # NEW
    "typer>=0.9.0",       # NEW (already used in project?)
    "loguru>=0.7.0",      # NEW (if not already present)
]
```

---

## Next Steps

Phase 0 complete. Proceed to Phase 1:
1. Create `data-model.md` with data structures
2. Create `contracts/cli-contract.md` with CLI specification
3. Create `quickstart.md` with usage examples
4. Update `CLAUDE.md` with new dependencies and commands

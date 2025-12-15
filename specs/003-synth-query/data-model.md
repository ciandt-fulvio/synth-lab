# Data Model: Synth Data Query Tool

**Feature**: 003-synth-query
**Date**: 2025-12-15
**Status**: Design Complete

## Overview

This document defines the data structures and models for the synth query feature. The system handles query requests, executes them against DuckDB, and formats results for display.

---

## Core Data Models

### 1. QueryMode (Enum)

Represents the three query execution modes.

```python
from enum import Enum

class QueryMode(Enum):
    """Query execution modes."""
    BASIC = "basic"           # SELECT * FROM synths (no parameters)
    WHERE = "where"           # SELECT * FROM synths WHERE <condition>
    FULL_QUERY = "full_query" # User-provided SELECT query
```

**Usage**:
- Determined from CLI parameters
- Drives query building logic
- Used in logging and error messages

---

### 2. QueryRequest

Represents a user's query request with validation.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class QueryRequest:
    """Validated query request from user input."""

    mode: QueryMode
    where_clause: Optional[str] = None
    full_query: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate query request consistency."""
        # Mutual exclusivity check
        if self.where_clause and self.full_query:
            raise ValueError("Cannot specify both where_clause and full_query")

        # Mode-specific validation
        if self.mode == QueryMode.WHERE and not self.where_clause:
            raise ValueError("WHERE mode requires where_clause")

        if self.mode == QueryMode.FULL_QUERY and not self.full_query:
            raise ValueError("FULL_QUERY mode requires full_query")

        # Basic mode should have no clauses
        if self.mode == QueryMode.BASIC and (self.where_clause or self.full_query):
            raise ValueError("BASIC mode cannot have where_clause or full_query")

    def to_sql(self) -> str:
        """Convert request to SQL query string."""
        if self.mode == QueryMode.FULL_QUERY:
            return self.full_query  # type: ignore

        if self.mode == QueryMode.WHERE:
            return f"SELECT * FROM synths WHERE {self.where_clause}"

        # BASIC mode
        return "SELECT * FROM synths"
```

**Validation Rules**:
- ✅ Mutual exclusivity: Only one of `where_clause` or `full_query` can be set
- ✅ Mode consistency: Parameters must match the specified mode
- ✅ Immutability: Frozen dataclass prevents accidental modification

**Examples**:

```python
# Basic query (all records)
req1 = QueryRequest(mode=QueryMode.BASIC)
# SQL: "SELECT * FROM synths"

# Filtered query
req2 = QueryRequest(mode=QueryMode.WHERE, where_clause="age > 30")
# SQL: "SELECT * FROM synths WHERE age > 30"

# Custom query
req3 = QueryRequest(
    mode=QueryMode.FULL_QUERY,
    full_query="SELECT city, COUNT(*) as total FROM synths GROUP BY city"
)
# SQL: "SELECT city, COUNT(*) as total FROM synths GROUP BY city"

# Invalid: both where and full_query
req4 = QueryRequest(
    mode=QueryMode.WHERE,
    where_clause="age > 30",
    full_query="SELECT * FROM synths"
)
# Raises: ValueError("Cannot specify both where_clause and full_query")
```

---

### 3. QueryResult

Represents the results of a executed query.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class QueryResult:
    """Results from executing a query."""

    columns: list[str]           # Column names
    rows: list[tuple]            # Data rows as tuples
    row_count: int               # Total rows in result set
    displayed_count: int         # Rows actually displayed (may be truncated)
    truncated: bool              # True if result set was truncated for display

    @classmethod
    def from_duckdb_result(
        cls,
        result: "duckdb.DuckDBPyRelation",  # type: ignore
        max_rows: int = 10000,
        display_limit: int = 1000
    ) -> "QueryResult":
        """
        Create QueryResult from DuckDB query result.

        Args:
            result: DuckDB query result relation
            max_rows: Maximum rows to fetch from database
            display_limit: Maximum rows to display to user

        Returns:
            QueryResult with potentially truncated data
        """
        # Get column names
        columns = [desc[0] for desc in result.description]

        # Fetch rows (up to max_rows)
        all_rows = result.fetchall()
        row_count = len(all_rows)

        # Truncate for display if needed
        displayed_rows = all_rows[:display_limit]
        displayed_count = len(displayed_rows)
        truncated = row_count > display_limit

        return cls(
            columns=columns,
            rows=displayed_rows,
            row_count=row_count,
            displayed_count=displayed_count,
            truncated=truncated
        )

    @property
    def is_empty(self) -> bool:
        """Check if result set is empty."""
        return self.row_count == 0
```

**Usage**:
- Created from DuckDB query execution
- Handles result set truncation transparently
- Provides metadata for user feedback

**Examples**:

```python
# Empty result
result1 = QueryResult(
    columns=["id", "name", "age"],
    rows=[],
    row_count=0,
    displayed_count=0,
    truncated=False
)
# result1.is_empty → True

# Normal result (not truncated)
result2 = QueryResult(
    columns=["name", "city"],
    rows=[("João", "São Paulo"), ("Maria", "Rio de Janeiro")],
    row_count=2,
    displayed_count=2,
    truncated=False
)

# Large result (truncated for display)
result3 = QueryResult(
    columns=["id", "name"],
    rows=[(i, f"User{i}") for i in range(1000)],  # First 1000 rows
    row_count=5000,  # Total in database
    displayed_count=1000,
    truncated=True
)
# User sees warning: "Showing first 1000 of 5000 rows"
```

---

### 4. DatabaseConfig

Configuration for DuckDB database connection.

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration for DuckDB database."""

    db_path: Path                # Path to DuckDB database file
    json_path: Path              # Path to source JSON file
    table_name: str = "synths"   # Name of table in database

    def __post_init__(self) -> None:
        """Validate configuration paths."""
        # Ensure parent directories exist
        if not self.json_path.parent.exists():
            raise ValueError(f"JSON parent directory does not exist: {self.json_path.parent}")

        # Note: db_path parent is created if needed during initialization

    @classmethod
    def default(cls) -> "DatabaseConfig":
        """Create default configuration for synth-lab."""
        return cls(
            db_path=Path("data/synths/synths.duckdb"),
            json_path=Path("data/synths/synths.json"),
            table_name="synths"
        )
```

**Validation Rules**:
- ✅ JSON source directory must exist
- ✅ Database directory created automatically if needed
- ✅ Immutable configuration

---

## Error Models

### QueryError Hierarchy

```python
class QueryError(Exception):
    """Base exception for query-related errors."""
    pass

class QuerySyntaxError(QueryError):
    """SQL syntax error in user query."""
    pass

class QueryExecutionError(QueryError):
    """Error during query execution (e.g., invalid column)."""
    pass

class DatabaseInitializationError(QueryError):
    """Error initializing database from JSON."""
    pass

class InvalidDataFileError(QueryError):
    """JSON data file is missing or invalid."""
    pass
```

**Usage in Error Handling**:

```python
try:
    result = execute_query(query_request)
except QuerySyntaxError as e:
    # User made SQL syntax mistake
    display_error(f"SQL syntax error: {e}")
    sys.exit(EXIT_USER_ERROR)
except QueryExecutionError as e:
    # Query is valid SQL but refers to non-existent column, etc.
    display_error(f"Query error: {e}")
    sys.exit(EXIT_USER_ERROR)
except InvalidDataFileError as e:
    # synths.json missing or corrupted
    display_error(f"Data file error: {e}")
    sys.exit(EXIT_SYSTEM_ERROR)
except DatabaseInitializationError as e:
    # DuckDB initialization failed
    display_error(f"Database error: {e}")
    sys.exit(EXIT_SYSTEM_ERROR)
```

---

## Data Flow

### Query Execution Pipeline

```text
1. User Input (CLI)
   ↓
2. QueryRequest (validated)
   ↓
3. SQL Query String
   ↓
4. DuckDB Execution
   ↓
5. QueryResult (with metadata)
   ↓
6. Formatted Table Display
```

### Detailed Flow

```python
# 1. CLI captures user input
where_clause = "age > 30"  # from --where option

# 2. Create validated QueryRequest
request = QueryRequest(mode=QueryMode.WHERE, where_clause=where_clause)

# 3. Convert to SQL
sql = request.to_sql()
# → "SELECT * FROM synths WHERE age > 30"

# 4. Execute against DuckDB
connection = get_database_connection()
result_relation = connection.execute(sql)

# 5. Create QueryResult with metadata
result = QueryResult.from_duckdb_result(result_relation)

# 6. Format and display
table = format_results(result)
display_table(table)

if result.truncated:
    display_truncation_warning(result.row_count, result.displayed_count)
```

---

## Schema Assumptions

### Synth Record Structure

The actual synth record schema is defined by the `gen_synth` feature. Based on the generated JSON, we expect:

```json
{
  "id": "uuid-string",
  "demographics": {
    "name": "string",
    "age": number,
    "gender": "string",
    "city": "string",
    "state": "string",
    // ... other demographic fields
  },
  "psychographics": {
    "openness": number,
    "conscientiousness": number,
    "extraversion": number,
    "agreeableness": number,
    "neuroticism": number
    // ... other psychographic fields
  },
  "behaviors": {
    // ... behavioral fields
  }
}
```

**Note**: DuckDB's `read_json_auto()` flattens nested structures, so queries can reference fields like:
- `demographics.name` or just `name` (depending on flattening behavior)
- `psychographics.openness` or `openness`

**Testing Strategy**: Use real generated synth data to validate schema assumptions.

---

## Validation Rules Summary

### Query Request Validation

| Rule | Validation | Error |
|------|------------|-------|
| Mutual Exclusivity | `where_clause` XOR `full_query` XOR neither | ValueError |
| Mode Consistency | Parameters match declared mode | ValueError |
| WHERE Mode | Must have `where_clause` | ValueError |
| FULL_QUERY Mode | Must have `full_query` | ValueError |
| BASIC Mode | No where_clause or full_query | ValueError |

### Database Configuration Validation

| Rule | Validation | Error |
|------|------------|-------|
| JSON Path Parent | Parent directory must exist | ValueError |
| DB Path Parent | Created automatically if missing | N/A |

### Query Result Validation

| Rule | Validation | Behavior |
|------|------------|----------|
| Row Limit | Max 10,000 rows fetched | Fetch limit |
| Display Limit | Max 1,000 rows displayed | Truncation with warning |
| Empty Result | 0 rows returned | Special "No results" message |

---

## Type Hints

All modules use strict type hints:

```python
from typing import Optional
from pathlib import Path
import duckdb

def execute_query(
    config: DatabaseConfig,
    request: QueryRequest
) -> QueryResult:
    """Execute a query against the synth database."""
    ...

def format_results(result: QueryResult) -> "Table":  # Rich Table
    """Format query results as Rich table."""
    ...

def validate_query_security(sql: str) -> None:
    """Ensure query is SELECT-only."""
    ...
```

---

## Next Steps

1. Use these models in `contracts/cli-contract.md` to define CLI behavior
2. Reference in `quickstart.md` for usage examples
3. Implement in Phase 2 (tasks generation) with TDD approach

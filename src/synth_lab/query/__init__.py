"""
Synth Data Query Tool.

This module provides tools for querying synthetic data stored in JSON format
using DuckDB as a SQL query engine. Results are displayed in formatted tables
using the Rich library.

Key Components:
- QueryMode: Enum for query execution modes (BASIC, WHERE, FULL_QUERY)
- Error hierarchy: Custom exceptions for query-related errors
- QueryRequest: Validated query request dataclass
- QueryResult: Query execution results with metadata
- DatabaseConfig: DuckDB database configuration

Usage:
    from synth_lab.query import QueryMode, QueryRequest

    # Basic query (all records)
    request = QueryRequest(mode=QueryMode.BASIC)

    # Filtered query
    request = QueryRequest(mode=QueryMode.WHERE, where_clause="age > 30")

    # Custom SQL query
    request = QueryRequest(
        mode=QueryMode.FULL_QUERY,
        full_query="SELECT city, COUNT(*) FROM synths GROUP BY city"
    )

Third-party Documentation:
- DuckDB: https://duckdb.org/docs/
- Rich (tables): https://rich.readthedocs.io/en/stable/tables.html
- Typer (CLI): https://typer.tiangolo.com/
"""

from enum import Enum


class QueryMode(Enum):
    """Query execution modes for synthetic data queries."""

    BASIC = "basic"           # SELECT * FROM synths (no parameters)
    WHERE = "where"           # SELECT * FROM synths WHERE <condition>
    FULL_QUERY = "full_query"  # User-provided SELECT query


# Error Hierarchy for Query Operations

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


# Exit codes for CLI
EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_SYSTEM_ERROR = 2


__all__ = [
    "QueryMode",
    "QueryError",
    "QuerySyntaxError",
    "QueryExecutionError",
    "DatabaseInitializationError",
    "InvalidDataFileError",
    "EXIT_SUCCESS",
    "EXIT_USER_ERROR",
    "EXIT_SYSTEM_ERROR",
]

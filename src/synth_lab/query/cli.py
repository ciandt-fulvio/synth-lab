"""
CLI commands for querying synthetic data.

This module provides the `listsynth` command for the synth-lab CLI.

Sample Input (command line):
    synthlab listsynth
    synthlab listsynth --where "age > 30"
    synthlab listsynth --full-query "SELECT city, COUNT(*) FROM synths GROUP BY city"

Expected Output:
    Formatted table with query results displayed to console

Third-party Documentation:
- Typer: https://typer.tiangolo.com/
"""

import typer
from typing import Optional
from pathlib import Path
from loguru import logger

from synth_lab.query import (
    QueryMode,
    QuerySyntaxError,
    QueryExecutionError,
    InvalidDataFileError,
    DatabaseInitializationError,
    EXIT_SUCCESS,
    EXIT_USER_ERROR,
    EXIT_SYSTEM_ERROR,
)
from synth_lab.query.validator import QueryRequest
from synth_lab.query.database import DatabaseConfig, initialize_database, execute_query
from synth_lab.query.formatter import display_results
from rich.console import Console
import sys as _sys

app = typer.Typer()
console = Console()
console_err = Console(stderr=True)


@app.command()
def listsynth(
    where: Optional[str] = typer.Option(
        None, "--where", help="SQL WHERE clause condition (without WHERE keyword)"
    ),
    full_query: Optional[str] = typer.Option(
        None, "--full-query", help="Complete SQL SELECT query"
    ),
) -> None:
    """
    Query synthetic data from the synths database.

    Display modes:
      - No options: Show all records
      - --where: Filter records with SQL WHERE condition
      - --full-query: Execute custom SQL SELECT query

    Examples:
      synthlab listsynth
      synthlab listsynth --where "age > 30"
      synthlab listsynth --where "city = 'São Paulo' AND age BETWEEN 25 AND 40"
      synthlab listsynth --full-query "SELECT city, COUNT(*) FROM synths GROUP BY city"
    """
    # Validate mutual exclusivity
    if where and full_query:
        console_err.print(
            "[red]Error:[/red] Cannot use both --where and --full-query\n"
            "Choose one: use --where for simple filters or --full-query for custom SQL"
        )
        raise typer.Exit(code=EXIT_USER_ERROR)

    try:
        # Determine query mode
        if full_query:
            mode = QueryMode.FULL_QUERY
            request = QueryRequest(mode=mode, full_query=full_query)
        elif where:
            mode = QueryMode.WHERE
            request = QueryRequest(mode=mode, where_clause=where)
        else:
            mode = QueryMode.BASIC
            request = QueryRequest(mode=mode)

        logger.info(f"Query mode: {mode.value}")

        # Get database configuration
        config = DatabaseConfig.default()
        logger.debug(f"Database config: {config}")

        # Initialize database
        con = initialize_database(config.db_path, config.json_path)

        # Build and execute query
        sql = request.to_sql()
        logger.info(f"Executing SQL: {sql[:100]}...")

        result = execute_query(con, sql)

        # Fetch and display results
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()

        display_results(columns, rows)

        # Cleanup
        con.close()
        logger.info("Query completed successfully")

        raise typer.Exit(code=EXIT_SUCCESS)

    except (QuerySyntaxError, QueryExecutionError) as e:
        # User errors (invalid SQL, etc.)
        console_err.print(f"[red]Error:[/red] {e}")
        logger.error(f"User error: {e}")
        raise typer.Exit(code=EXIT_USER_ERROR)

    except (InvalidDataFileError, DatabaseInitializationError) as e:
        # System errors (missing file, database issues)
        console_err.print(f"[red]Error:[/red] {e}")
        logger.error(f"System error: {e}")
        raise typer.Exit(code=EXIT_SYSTEM_ERROR)

    except Exception as e:
        # Unexpected errors
        console_err.print(f"[red]Unexpected error:[/red] {e}")
        logger.exception("Unexpected error during query")
        raise typer.Exit(code=EXIT_SYSTEM_ERROR)


if __name__ == "__main__":
    app()

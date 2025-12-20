"""
Rich table formatting for query results.

This module formats query results into beautiful CLI tables using the Rich library.

Sample Input:
    columns = ["id", "name", "age"]
    rows = [("test-001", "João Silva", 34), ("test-002", "Maria", 28)]
    table = format_results(columns, rows, "Query Results")

Expected Output:
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    │          Query Results              │
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ id       │ name       │ age        │
    ├──────────┼────────────┼────────────┤
    │ test-001 │ João Silva │ 34         │
    │ test-002 │ Maria      │ 28         │
    └──────────┴────────────┴────────────┘

Third-party Documentation:
- Rich Tables: https://rich.readthedocs.io/en/stable/tables.html
- Rich Console: https://rich.readthedocs.io/en/stable/console.html
"""

import rich.box
from loguru import logger
from rich.console import Console
from rich.table import Table


def format_results(
    columns: list[str], rows: list[tuple], title: str = "Query Results"
) -> Table:
    """
    Format query results as Rich table.
    
    Args:
        columns: Column names
        rows: Data rows as tuples
        title: Table title
        
    Returns:
        Rich Table instance ready for display
    """
    table = Table(
        title=title,
        show_header=True,
        header_style="bold magenta",
        expand=False,
        box=rich.box.ROUNDED,
        show_lines=False,
    )

    # Add columns with overflow handling
    for col in columns:
        table.add_column(
            col, style="cyan", overflow="fold", max_width=30
        )

    # Add rows
    for row in rows:
        table.add_row(*[str(val) for val in row])

    logger.debug(f"Formatted table with {len(columns)} columns and {len(rows)} rows")

    return table


def display_results(columns: list[str], rows: list[tuple]) -> None:
    """
    Display results to console.
    
    Args:
        columns: Column names
        rows: Data rows as tuples
    """
    console = Console()

    if not rows:
        console.print("[yellow]No results found[/yellow]")
        console.print("\n[dim]0 rows returned[/dim]")
        logger.info("Query returned no results")
        return

    table = format_results(columns, rows)
    console.print(table)
    console.print(f"\n[dim]{len(rows)} rows returned[/dim]")
    logger.info(f"Displayed {len(rows)} rows")


def display_results_with_truncation_warning(
    columns: list[str], rows: list[tuple], total_rows: int, displayed_rows: int
) -> None:
    """
    Display results with truncation warning for large result sets.
    
    Args:
        columns: Column names
        rows: Data rows to display (already truncated)
        total_rows: Total rows in full result set
        displayed_rows: Number of rows being displayed
    """
    console = Console()

    if not rows:
        console.print("[yellow]No results found[/yellow]")
        console.print("\n[dim]0 rows returned[/dim]")
        return

    table = format_results(columns, rows)
    console.print(table)

    if total_rows > displayed_rows:
        console.print(
            f"\n[yellow]Warning: Showing first {displayed_rows} of {total_rows} rows[/yellow]"
        )
        console.print(
            "[dim]Tip: Use --full-query with LIMIT clause to control result size[/dim]"
        )
        console.print(f"\n[dim]{displayed_rows} rows displayed ({total_rows} total)[/dim]")
        logger.warning(f"Result set truncated: showing {displayed_rows} of {total_rows} rows")
    else:
        console.print(f"\n[dim]{total_rows} rows returned[/dim]")
        logger.info(f"Displayed all {total_rows} rows")


if __name__ == "__main__":
    """Validation block with real data."""
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Format empty result
    total_tests += 1
    try:
        columns = ["id", "name", "age"]
        rows = []
        table = format_results(columns, rows)
        if not isinstance(table, Table):
            all_validation_failures.append("Empty result: Table type mismatch")
        if len(table.columns) != 3:
            all_validation_failures.append(f"Empty result: Expected 3 columns, got {len(table.columns)}")
    except Exception as e:
        all_validation_failures.append(f"Empty result formatting: {e}")

    # Test 2: Format normal result
    total_tests += 1
    try:
        columns = ["id", "name", "age"]
        rows = [("test-001", "João Silva", 34), ("test-002", "Maria", 28)]
        table = format_results(columns, rows)
        if not isinstance(table, Table):
            all_validation_failures.append("Normal result: Table type mismatch")
        if table.row_count != 2:
            all_validation_failures.append(f"Normal result: Expected 2 rows, got {table.row_count}")
    except Exception as e:
        all_validation_failures.append(f"Normal result formatting: {e}")

    # Test 3: Unicode handling
    total_tests += 1
    try:
        columns = ["nome", "cidade"]
        rows = [("João", "São Paulo"), ("María", "Brasília")]
        table = format_results(columns, rows)
        if table.row_count != 2:
            all_validation_failures.append(f"Unicode test: Expected 2 rows, got {table.row_count}")
    except Exception as e:
        all_validation_failures.append(f"Unicode handling: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Formatter module is validated and ready")
        sys.exit(0)

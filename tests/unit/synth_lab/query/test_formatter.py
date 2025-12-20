"""Unit tests for formatter module."""

import pytest
from rich.table import Table


# T015: Unit test for empty QueryResult formatting
@pytest.mark.unit
def test_format_empty_result():
    """Test formatting of empty QueryResult."""
    from synth_lab.query.formatter import format_results

    columns = ["id", "name", "age"]
    rows = []

    table = format_results(columns, rows, title="Query Results")

    assert isinstance(table, Table)
    assert table.title == "Query Results"
    # Table should have columns even if no rows
    assert len(table.columns) == 3


# T016: Unit test for normal QueryResult formatting
@pytest.mark.unit
def test_format_normal_result():
    """Test formatting of normal QueryResult with data."""
    from synth_lab.query.formatter import format_results

    columns = ["id", "name", "age"]
    rows = [
        ("test-001", "João Silva", 34),
        ("test-002", "Maria Santos", 28),
    ]

    table = format_results(columns, rows, title="Query Results")

    assert isinstance(table, Table)
    assert table.title == "Query Results"
    assert len(table.columns) == 3
    assert table.row_count == 2


# T057: Unit test for QueryResult truncation (US3)
@pytest.mark.unit
def test_format_truncated_result():
    """Test formatting with truncation warning for large result sets."""
    from synth_lab.query.formatter import format_results

    columns = ["id", "name"]
    # Simulate large result set (first 1000 of 5000)
    rows = [(f"id-{i}", f"Name{i}") for i in range(1000)]

    table = format_results(columns, rows, title="Query Results")

    assert isinstance(table, Table)
    assert table.row_count == 1000


@pytest.mark.unit
def test_format_results_unicode():
    """Test formatting with Brazilian Portuguese characters."""
    from synth_lab.query.formatter import format_results

    columns = ["nome", "cidade"]
    rows = [
        ("João", "São Paulo"),
        ("María", "Brasília"),
    ]

    table = format_results(columns, rows)

    assert isinstance(table, Table)
    assert table.row_count == 2

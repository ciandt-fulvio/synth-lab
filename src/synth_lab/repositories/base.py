"""
Base repository class for synth-lab.

Provides common patterns for data access including pagination, connection management,
and error handling.

References:
    - Database module: synth_lab.infrastructure.database
"""

import sqlite3
from typing import TypeVar

from synth_lab.infrastructure.database import DatabaseManager, get_database
from synth_lab.models.pagination import PaginationMeta, PaginationParams

T = TypeVar("T")


class BaseRepository:
    """Base class for all repositories with common functionality."""

    def __init__(self, db: DatabaseManager | None = None):
        """
        Initialize repository.

        Args:
            db: Database manager instance. Defaults to global instance.
        """
        self.db = db or get_database()

    def _paginate_query(
        self,
        base_query: str,
        params: PaginationParams,
        count_query: str | None = None,
        query_params: tuple | None = None,
    ) -> tuple[list[sqlite3.Row], PaginationMeta]:
        """
        Execute a paginated query.

        Args:
            base_query: SQL query without LIMIT/OFFSET (should not end with ;)
            params: Pagination parameters
            count_query: Custom count query. If None, wraps base_query with COUNT(*)
            query_params: Parameters for the query

        Returns:
            Tuple of (rows, pagination_meta)
        """
        # Get total count
        if count_query is None:
            count_query = f"SELECT COUNT(*) as count FROM ({base_query})"

        count_row = self.db.fetchone(count_query, query_params)
        total = count_row["count"] if count_row else 0

        # Apply sorting if specified
        if params.sort_by:
            # Validate sort_by to prevent SQL injection
            # Only allow alphanumeric and underscore
            if params.sort_by.replace("_", "").isalnum():
                base_query = f"{base_query} ORDER BY {params.sort_by} {params.sort_order.upper()}"

        # Apply pagination
        paginated_query = f"{base_query} LIMIT ? OFFSET ?"
        pagination_params = (
            (*query_params, params.limit, params.offset)
            if query_params
            else (params.limit, params.offset)
        )

        rows = self.db.fetchall(paginated_query, pagination_params)

        meta = PaginationMeta.from_params(total, params)
        return rows, meta

    def _row_to_dict(self, row: sqlite3.Row | None) -> dict | None:
        """Convert a SQLite row to a dictionary."""
        if row is None:
            return None
        return dict(row)

    def _rows_to_dicts(self, rows: list[sqlite3.Row]) -> list[dict]:
        """Convert SQLite rows to a list of dictionaries."""
        return [dict(row) for row in rows]


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        db = DatabaseManager(test_db_path)

        # Create test table
        db.execute("""
            CREATE TABLE test_items (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)

        # Insert test data
        for i in range(25):
            db.execute(
                "INSERT INTO test_items (id, name, value) VALUES (?, ?, ?)",
                (i + 1, f"Item {i + 1}", i * 10),
            )

        repo = BaseRepository(db)

        # Test 1: Basic pagination
        total_tests += 1
        try:
            params = PaginationParams(limit=10, offset=0)
            rows, meta = repo._paginate_query(
                "SELECT * FROM test_items",
                params,
            )
            if len(rows) != 10:
                all_validation_failures.append(f"Expected 10 rows, got {len(rows)}")
            if meta.total != 25:
                all_validation_failures.append(f"Expected total 25, got {meta.total}")
            if meta.has_next is not True:
                all_validation_failures.append(f"has_next should be True, got {meta.has_next}")
        except Exception as e:
            all_validation_failures.append(f"Basic pagination failed: {e}")

        # Test 2: Pagination with offset
        total_tests += 1
        try:
            params = PaginationParams(limit=10, offset=20)
            rows, meta = repo._paginate_query(
                "SELECT * FROM test_items",
                params,
            )
            if len(rows) != 5:
                all_validation_failures.append(f"Expected 5 rows with offset 20, got {len(rows)}")
            if meta.has_next is not False:
                all_validation_failures.append(f"has_next should be False, got {meta.has_next}")
        except Exception as e:
            all_validation_failures.append(f"Pagination with offset failed: {e}")

        # Test 3: Pagination with sorting
        total_tests += 1
        try:
            params = PaginationParams(limit=5, offset=0, sort_by="value", sort_order="desc")
            rows, meta = repo._paginate_query(
                "SELECT * FROM test_items",
                params,
            )
            if len(rows) != 5:
                all_validation_failures.append(f"Expected 5 rows, got {len(rows)}")
            # First row should be the highest value (240)
            if rows[0]["value"] != 240:
                all_validation_failures.append(
                    f"First value should be 240 (desc), got {rows[0]['value']}"
                )
        except Exception as e:
            all_validation_failures.append(f"Pagination with sorting failed: {e}")

        # Test 4: row_to_dict
        total_tests += 1
        try:
            row = db.fetchone("SELECT * FROM test_items WHERE id = 1")
            result = repo._row_to_dict(row)
            if result is None:
                all_validation_failures.append("row_to_dict returned None")
            elif result.get("name") != "Item 1":
                all_validation_failures.append(f"name mismatch: {result.get('name')}")
        except Exception as e:
            all_validation_failures.append(f"row_to_dict failed: {e}")

        # Test 5: row_to_dict with None
        total_tests += 1
        try:
            result = repo._row_to_dict(None)
            if result is not None:
                all_validation_failures.append(f"row_to_dict(None) should be None: {result}")
        except Exception as e:
            all_validation_failures.append(f"row_to_dict None test failed: {e}")

        # Test 6: rows_to_dicts
        total_tests += 1
        try:
            rows = db.fetchall("SELECT * FROM test_items LIMIT 3")
            result = repo._rows_to_dicts(rows)
            if len(result) != 3:
                all_validation_failures.append(f"Expected 3 dicts, got {len(result)}")
            if not isinstance(result[0], dict):
                all_validation_failures.append(f"Expected dict, got {type(result[0])}")
        except Exception as e:
            all_validation_failures.append(f"rows_to_dicts failed: {e}")

        # Test 7: Pagination with query params
        total_tests += 1
        try:
            params = PaginationParams(limit=10, offset=0)
            rows, meta = repo._paginate_query(
                "SELECT * FROM test_items WHERE value > ?",
                params,
                query_params=(100,),
            )
            # Values > 100 are: 110, 120, ..., 240 (14 items)
            if meta.total != 14:
                all_validation_failures.append(f"Expected total 14, got {meta.total}")
        except Exception as e:
            all_validation_failures.append(f"Pagination with params failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)

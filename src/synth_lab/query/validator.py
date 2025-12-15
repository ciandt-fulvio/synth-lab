"""
Query request validation and SQL generation.

This module provides the QueryRequest dataclass for validating user query requests
and converting them to SQL queries.

Sample Input:
    # Basic mode (no parameters)
    request = QueryRequest(mode=QueryMode.BASIC)
    
    # WHERE mode
    request = QueryRequest(mode=QueryMode.WHERE, where_clause="age > 30")
    
    # FULL_QUERY mode
    request = QueryRequest(
        mode=QueryMode.FULL_QUERY,
        full_query="SELECT city, COUNT(*) FROM synths GROUP BY city"
    )

Expected Output:
    # Basic: "SELECT * FROM synths"
    # WHERE: "SELECT * FROM synths WHERE age > 30"
    # FULL_QUERY: "SELECT city, COUNT(*) FROM synths GROUP BY city"

Third-party Documentation:
- Python dataclasses: https://docs.python.org/3/library/dataclasses.html
"""

from dataclasses import dataclass
from typing import Optional
from synth_lab.query import QueryMode, QuerySyntaxError


@dataclass(frozen=True)
class QueryRequest:
    """
    Validated query request from user input.
    
    This dataclass validates mutual exclusivity of parameters and
    mode-parameter consistency.
    """

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
        """
        Convert request to SQL query string.
        
        Returns:
            SQL query string ready for execution.
        """
        if self.mode == QueryMode.FULL_QUERY:
            return self.full_query  # type: ignore

        if self.mode == QueryMode.WHERE:
            return f"SELECT * FROM synths WHERE {self.where_clause}"

        # BASIC mode
        return "SELECT * FROM synths"


def validate_query_security(sql: str) -> None:
    """
    Ensure query is SELECT-only (no writes).
    
    Args:
        sql: SQL query string to validate
        
    Raises:
        QuerySyntaxError: If query contains forbidden operations
    """
    sql_upper = sql.strip().upper()

    # Check for forbidden operations
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    for operation in forbidden:
        if operation in sql_upper:
            raise QuerySyntaxError(
                f"Only SELECT queries are allowed\n"
                f"Found: {operation} operation\n"
                f"This tool is read-only"
            )

    # Ensure query starts with SELECT
    if not sql_upper.startswith("SELECT"):
        raise QuerySyntaxError(
            "Query must be a SELECT statement\n"
            f"Found: {sql[:20]}..."
        )


if __name__ == "__main__":
    """Validation block with real data."""
    import sys
    
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Basic mode query building
    total_tests += 1
    try:
        req = QueryRequest(mode=QueryMode.BASIC)
        sql = req.to_sql()
        expected = "SELECT * FROM synths"
        if sql != expected:
            all_validation_failures.append(f"Basic mode: Expected {expected}, got {sql}")
    except Exception as e:
        all_validation_failures.append(f"Basic mode: Exception {e}")
    
    # Test 2: WHERE mode query building
    total_tests += 1
    try:
        req = QueryRequest(mode=QueryMode.WHERE, where_clause="age > 30")
        sql = req.to_sql()
        expected = "SELECT * FROM synths WHERE age > 30"
        if sql != expected:
            all_validation_failures.append(f"WHERE mode: Expected {expected}, got {sql}")
    except Exception as e:
        all_validation_failures.append(f"WHERE mode: Exception {e}")
    
    # Test 3: Mutual exclusivity validation
    total_tests += 1
    try:
        req = QueryRequest(mode=QueryMode.WHERE, where_clause="age > 30", full_query="SELECT *")
        all_validation_failures.append("Mutual exclusivity: Expected ValueError but none raised")
    except ValueError:
        # Expected - test passes
        pass
    except Exception as e:
        all_validation_failures.append(f"Mutual exclusivity: Expected ValueError, got {type(e).__name__}")
    
    # Test 4: Security validation (reject INSERT)
    total_tests += 1
    try:
        validate_query_security("INSERT INTO synths VALUES (1, 'test')")
        all_validation_failures.append("Security: Expected QuerySyntaxError for INSERT")
    except QuerySyntaxError:
        # Expected - test passes
        pass
    except Exception as e:
        all_validation_failures.append(f"Security: Expected QuerySyntaxError, got {type(e).__name__}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("QueryRequest validator is validated and ready")
        sys.exit(0)

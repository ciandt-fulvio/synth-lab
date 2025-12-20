"""
DuckDB database operations for synth data queries.

This module handles DuckDB database initialization from JSON files and
query execution with error handling.

Sample Input:
    config = DatabaseConfig.default()
    # db_path: Path("output/synths/synths.duckdb")
    # json_path: Path("output/synths/synths.json")
    
    con = initialize_database(config.db_path, config.json_path)
    result = execute_query(con, "SELECT * FROM synths LIMIT 10")

Expected Output:
    # Database initialized with table from JSON
    # Query results returned as DuckDB relation

Third-party Documentation:
- DuckDB Python API: https://duckdb.org/docs/api/python/overview
- DuckDB read_json_auto: https://duckdb.org/docs/data/json/overview
"""

from dataclasses import dataclass
from pathlib import Path
import duckdb
import json
from loguru import logger

from synth_lab.query import (
    QuerySyntaxError,
    QueryExecutionError,
    DatabaseInitializationError,
    InvalidDataFileError,
)


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration for DuckDB database."""

    db_path: Path
    json_path: Path
    table_name: str = "synths"

    def __post_init__(self) -> None:
        """Validate configuration paths."""
        # Ensure parent directories will be created if needed
        # JSON parent must exist for the file to be readable
        if not self.json_path.parent.exists():
            raise ValueError(f"JSON parent directory does not exist: {self.json_path.parent}")

    @classmethod
    def default(cls) -> "DatabaseConfig":
        """Create default configuration for synth-lab."""
        return cls(
            db_path=Path("output/synths/synths.duckdb"),
            json_path=Path("output/synths/synths.json"),
            table_name="synths",
        )


def validate_json_file(json_path: Path) -> None:
    """
    Validate JSON file exists and is valid.
    
    Args:
        json_path: Path to JSON file
        
    Raises:
        InvalidDataFileError: If file is missing or invalid
    """
    if not json_path.exists():
        raise InvalidDataFileError(
            f"Synth data file not found: {json_path}\n"
            "Tip: Run 'synthlab generate' to create synthetic data first."
        )

    if not json_path.is_file():
        raise InvalidDataFileError(f"{json_path} is not a file")

    # Quick JSON syntax validation
    try:
        with open(json_path) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        raise InvalidDataFileError(
            f"Invalid JSON in {json_path}: {e}\n"
            "The synth data file may be corrupted. Try regenerating with 'synthlab generate'."
        )


def initialize_database(db_path: Path, json_path: Path) -> duckdb.DuckDBPyConnection:
    """
    Initialize or update DuckDB database from JSON source.
    
    Args:
        db_path: Path to DuckDB database file
        json_path: Path to source JSON file
        
    Returns:
        DuckDB connection with synths table loaded
        
    Raises:
        InvalidDataFileError: If JSON file is missing or invalid
        DatabaseInitializationError: If database initialization fails
    """
    # Validate JSON file first
    validate_json_file(json_path)
    
    try:
        # Create database directory if needed
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        con = duckdb.connect(str(db_path))
        logger.info(f"Connected to database: {db_path}")
        
        # Drop and recreate table to ensure fresh data
        con.execute("DROP TABLE IF EXISTS synths")
        logger.debug("Dropped existing synths table")
        
        con.execute(f"""
            CREATE TABLE synths AS
            SELECT *
            FROM read_json_auto('{json_path}')
        """)
        logger.info(f"Created synths table from {json_path}")
        
        # Log table stats
        count_result = con.execute("SELECT COUNT(*) FROM synths").fetchone()
        logger.info(f"Loaded {count_result[0]} records into synths table")
        
        return con
        
    except duckdb.IOException as e:
        raise DatabaseInitializationError(f"DuckDB could not read JSON file: {e}")
    except duckdb.Error as e:
        raise DatabaseInitializationError(f"Database initialization failed: {e}")
    except Exception as e:
        raise DatabaseInitializationError(f"Unexpected error during initialization: {e}")


def execute_query(
    con: duckdb.DuckDBPyConnection, query: str
) -> duckdb.DuckDBPyRelation:
    """
    Execute query with error handling.
    
    Args:
        con: DuckDB connection
        query: SQL query string
        
    Returns:
        DuckDB relation with query results
        
    Raises:
        QuerySyntaxError: For SQL syntax errors
        QueryExecutionError: For execution errors
    """
    try:
        logger.debug(f"Executing query: {query[:100]}...")
        result = con.execute(query)
        logger.debug("Query executed successfully")
        return result
        
    except duckdb.ParserException as e:
        # SQL syntax errors
        raise QuerySyntaxError(
            f"Invalid SQL syntax in your query\n"
            f"Details: {e}\n"
            f"Please check for typos, missing quotes, or incorrect SQL keywords"
        )
    except duckdb.CatalogException as e:
        # Table/column not found
        raise QueryExecutionError(
            f"Column or table not found\n"
            f"Details: {e}\n"
            f"Make sure your query references columns that exist in the synths table"
        )
    except duckdb.BinderException as e:
        # Invalid column references
        raise QueryExecutionError(
            f"Invalid column reference\n"
            f"Details: {e}\n"
            f"Check that column names are spelled correctly"
        )
    except duckdb.Error as e:
        # Other DuckDB errors
        raise QueryExecutionError(f"Query execution failed: {e}")


if __name__ == "__main__":
    """Validation block with real data."""
    import sys
    import tempfile
    
    all_validation_failures = []
    total_tests = 0
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create test JSON data
        test_json = tmp_path / "test_synths.json"
        test_json.write_text('[{"id": "t1", "name": "Test", "age": 25}]')
        
        # Test 1: DatabaseConfig creation
        total_tests += 1
        try:
            config = DatabaseConfig(
                db_path=tmp_path / "test.duckdb",
                json_path=test_json,
                table_name="synths"
            )
            if config.table_name != "synths":
                all_validation_failures.append("DatabaseConfig: table_name mismatch")
        except Exception as e:
            all_validation_failures.append(f"DatabaseConfig creation: {e}")
        
        # Test 2: Database initialization
        total_tests += 1
        try:
            con = initialize_database(tmp_path / "test.duckdb", test_json)
            if con is None:
                all_validation_failures.append("Database initialization: Connection is None")
            else:
                # Test 3: Query execution
                total_tests += 1
                try:
                    result = execute_query(con, "SELECT * FROM synths")
                    rows = result.fetchall()
                    if len(rows) != 1:
                        all_validation_failures.append(f"Query execution: Expected 1 row, got {len(rows)}")
                except Exception as e:
                    all_validation_failures.append(f"Query execution: {e}")
                
                con.close()
        except Exception as e:
            all_validation_failures.append(f"Database initialization: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Database module is validated and ready")
        sys.exit(0)

"""Integration tests for query functionality with real DuckDB."""

import pytest
import duckdb
from pathlib import Path


# T017: Integration test for database initialization from JSON
@pytest.mark.integration
def test_database_initialization(test_data_dir):
    """Test database initialization from JSON file."""
    from synth_lab.query.database import initialize_database
    
    db_path = test_data_dir / "synths.duckdb"
    json_path = test_data_dir / "synths.json"
    
    con = initialize_database(db_path, json_path)
    
    # Verify connection is open
    assert con is not None
    
    # Verify table exists
    result = con.execute("SELECT COUNT(*) FROM synths").fetchone()
    assert result[0] == 5  # sample_synths.json has 5 records
    
    con.close()


# T018: Integration test for basic query execution (all records)
@pytest.mark.integration
def test_basic_query_execution(test_db_connection):
    """Test basic query returns all records."""
    from synth_lab.query.validator import QueryRequest
    from synth_lab.query import QueryMode
    from synth_lab.query.database import execute_query
    
    request = QueryRequest(mode=QueryMode.BASIC)
    sql = request.to_sql()
    
    result = test_db_connection.execute(sql)
    rows = result.fetchall()
    
    assert len(rows) == 5  # sample_synths.json has 5 records
    assert len(rows[0]) > 0  # Should have columns


# T019: Integration test for empty result handling
@pytest.mark.integration
def test_empty_result_handling(test_db_connection):
    """Test query that returns no results."""
    sql = "SELECT * FROM synths WHERE age > 1000"
    
    result = test_db_connection.execute(sql)
    rows = result.fetchall()
    
    assert len(rows) == 0


# T020: Integration test for missing data file error
@pytest.mark.integration
def test_missing_data_file(empty_data_dir):
    """Test error handling when JSON data file is missing."""
    from synth_lab.query.database import initialize_database
    from synth_lab.query import InvalidDataFileError
    
    db_path = empty_data_dir / "synths.duckdb"
    json_path = empty_data_dir / "synths.json"  # This file doesn't exist
    
    with pytest.raises((InvalidDataFileError, FileNotFoundError, duckdb.IOException)):
        initialize_database(db_path, json_path)

"""Pytest configuration and fixtures for integration tests."""

import pytest
import duckdb
from pathlib import Path
import json
import tempfile
import shutil


@pytest.fixture
def sample_json_path() -> Path:
    """Path to sample synth data JSON file."""
    return Path(__file__).parent.parent.parent.parent / "fixtures" / "query" / "sample_synths.json"


@pytest.fixture
def invalid_json_path() -> Path:
    """Path to invalid JSON file for error testing."""
    return Path(__file__).parent.parent.parent.parent / "fixtures" / "query" / "invalid_synths.json"


@pytest.fixture
def test_data_dir(tmp_path):
    """Create temporary data directory with sample synth data."""
    data_dir = tmp_path / "data" / "synths"
    data_dir.mkdir(parents=True)
    
    # Copy sample data to temp location
    sample_json_path = Path(__file__).parent.parent.parent.parent / "fixtures" / "query" / "sample_synths.json"
    shutil.copy(sample_json_path, data_dir / "synths.json")
    
    return data_dir


@pytest.fixture
def test_db_connection(test_data_dir):
    """Create and initialize DuckDB connection for testing."""
    db_path = test_data_dir / "synths.duckdb"
    json_path = test_data_dir / "synths.json"
    
    con = duckdb.connect(str(db_path))
    
    # Initialize table from JSON
    con.execute("DROP TABLE IF EXISTS synths")
    con.execute(f"""
        CREATE TABLE synths AS
        SELECT *
        FROM read_json_auto('{json_path}')
    """)
    
    yield con
    
    # Cleanup
    con.close()


@pytest.fixture
def empty_data_dir(tmp_path):
    """Create temporary data directory with NO synth data (for error testing)."""
    data_dir = tmp_path / "data" / "synths"
    data_dir.mkdir(parents=True)
    return data_dir

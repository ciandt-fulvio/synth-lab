"""Pytest configuration and fixtures for unit tests."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_json_path() -> Path:
    """Path to sample synth data JSON file."""
    return Path(__file__).parent.parent.parent.parent / "fixtures" / "query" / "sample_synths.json"


@pytest.fixture
def invalid_json_path() -> Path:
    """Path to invalid JSON file for error testing."""
    return Path(__file__).parent.parent.parent.parent / "fixtures" / "query" / "invalid_synths.json"


@pytest.fixture
def temp_db_path(tmp_path) -> Path:
    """Temporary database path for testing."""
    return tmp_path / "test_synths.duckdb"

"""Tests for storage module (SQLite-based)."""

import tempfile
from pathlib import Path

import pytest

import synth_lab.infrastructure.config as config_module
from synth_lab.gen_synth import storage


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"

        # Temporarily override DB_PATH
        original_db_path = config_module.DB_PATH
        config_module.DB_PATH = test_db_path

        # Initialize the test database
        from synth_lab.infrastructure.database import init_database

        init_database(test_db_path)

        yield test_db_path

        # Restore original DB_PATH
        config_module.DB_PATH = original_db_path


def test_save_synth_to_database(temp_db, sample_synth):
    """Test saving synth to database."""
    storage.save_synth(sample_synth)

    # Verify it was saved
    loaded = storage.get_synth_by_id(sample_synth["id"])
    assert loaded is not None
    assert loaded["id"] == sample_synth["id"]
    assert loaded["nome"] == sample_synth["nome"]


def test_save_synth_with_json_fields(temp_db, sample_synth):
    """Test saving synth with JSON fields (demografia, psicografia, etc.)."""
    storage.save_synth(sample_synth)

    loaded = storage.get_synth_by_id(sample_synth["id"])
    assert loaded is not None

    # Check JSON fields are properly stored and loaded
    assert loaded["demografia"]["idade"] == sample_synth["demografia"]["idade"]
    assert (
        loaded["psicografia"]["personalidade_big_five"]["abertura"]
        == sample_synth["psicografia"]["personalidade_big_five"]["abertura"]
    )


def test_save_multiple_synths(temp_db, sample_synth):
    """Test saving multiple synths to database."""
    # Save first synth
    synth1 = sample_synth.copy()
    synth1["id"] = "synth01"
    storage.save_synth(synth1)

    # Save second synth
    synth2 = sample_synth.copy()
    synth2["id"] = "synth02"
    synth2["nome"] = "Another Person"
    storage.save_synth(synth2)

    # Verify both exist
    count = storage.count_synths()
    assert count == 2

    synths = storage.load_synths()
    assert len(synths) == 2

    ids = [s["id"] for s in synths]
    assert "synth01" in ids
    assert "synth02" in ids


def test_load_synths_from_database(temp_db, sample_synth):
    """Test loading all synths from database."""
    # Save some synths first
    storage.save_synth(sample_synth)

    # Load them back
    synths = storage.load_synths()
    assert len(synths) == 1
    assert synths[0]["id"] == sample_synth["id"]


def test_get_synth_by_id_found(temp_db, sample_synth):
    """Test getting a synth by ID when it exists."""
    storage.save_synth(sample_synth)

    synth = storage.get_synth_by_id(sample_synth["id"])
    assert synth is not None
    assert synth["id"] == sample_synth["id"]


def test_get_synth_by_id_not_found(temp_db):
    """Test getting a synth by ID when it doesn't exist."""
    synth = storage.get_synth_by_id("nonexistent")
    assert synth is None


def test_count_synths_empty(temp_db):
    """Test counting synths when database is empty."""
    count = storage.count_synths()
    assert count == 0


def test_count_synths_with_data(temp_db, sample_synth):
    """Test counting synths with data in database."""
    # Save some synths
    synth1 = sample_synth.copy()
    synth1["id"] = "synth01"
    storage.save_synth(synth1)

    synth2 = sample_synth.copy()
    synth2["id"] = "synth02"
    storage.save_synth(synth2)

    count = storage.count_synths()
    assert count == 2


def test_save_synth_update_existing(temp_db, sample_synth):
    """Test that saving a synth with existing ID updates it."""
    # Save original
    storage.save_synth(sample_synth)

    # Update with same ID
    updated = sample_synth.copy()
    updated["nome"] = "Updated Name"
    storage.save_synth(updated)

    # Verify update
    loaded = storage.get_synth_by_id(sample_synth["id"])
    assert loaded["nome"] == "Updated Name"

    # Verify count is still 1 (not 2)
    count = storage.count_synths()
    assert count == 1


def test_deprecated_functions_work(temp_db, sample_synth):
    """Test that deprecated functions still work for backwards compatibility."""
    # These should work but log warnings
    storage.save_synth(sample_synth)

    synths = storage.load_consolidated_synths()
    assert len(synths) == 1
    assert synths[0]["id"] == sample_synth["id"]

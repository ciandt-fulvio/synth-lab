"""Tests for storage module."""

import json
import pytest
from pathlib import Path
from synth_lab.gen_synth import storage


def test_save_synth_consolidated_only(temp_output_dir, sample_synth):
    """Test saving synth to consolidated file only."""
    storage.save_synth(sample_synth, output_dir=temp_output_dir, save_individual=False)

    # Check consolidated file exists
    consolidated_path = temp_output_dir / "synths.json"
    assert consolidated_path.exists()

    # Check individual file does NOT exist
    individual_path = temp_output_dir / f"{sample_synth['id']}.json"
    assert not individual_path.exists()

    # Verify content
    with open(consolidated_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["id"] == sample_synth["id"]


def test_save_synth_with_individual(temp_output_dir, sample_synth):
    """Test saving synth to both consolidated and individual files."""
    storage.save_synth(sample_synth, output_dir=temp_output_dir, save_individual=True)

    # Check both files exist
    consolidated_path = temp_output_dir / "synths.json"
    individual_path = temp_output_dir / f"{sample_synth['id']}.json"
    assert consolidated_path.exists()
    assert individual_path.exists()

    # Verify content in both files
    with open(consolidated_path, "r", encoding="utf-8") as f:
        consolidated_data = json.load(f)
    assert len(consolidated_data) == 1

    with open(individual_path, "r", encoding="utf-8") as f:
        individual_data = json.load(f)
    assert individual_data["id"] == sample_synth["id"]


def test_save_synth_multiple_consolidated(temp_output_dir, sample_synth):
    """Test saving multiple synths to consolidated file."""
    # Save first synth
    synth1 = sample_synth.copy()
    synth1["id"] = "synth01"
    storage.save_synth(synth1, output_dir=temp_output_dir)

    # Save second synth
    synth2 = sample_synth.copy()
    synth2["id"] = "synth02"
    storage.save_synth(synth2, output_dir=temp_output_dir)

    # Verify consolidated file has both
    consolidated_path = temp_output_dir / "synths.json"
    with open(consolidated_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]["id"] == "synth01"
    assert data[1]["id"] == "synth02"


def test_load_consolidated_synths_existing(temp_output_dir, sample_synth):
    """Test loading synths from existing consolidated file."""
    # Save some synths first
    storage.save_synth(sample_synth, output_dir=temp_output_dir)

    # Load them back
    synths = storage.load_consolidated_synths(output_dir=temp_output_dir)
    assert len(synths) == 1
    assert synths[0]["id"] == sample_synth["id"]


def test_load_consolidated_synths_nonexistent(temp_output_dir):
    """Test loading synths when consolidated file doesn't exist."""
    synths = storage.load_consolidated_synths(output_dir=temp_output_dir)
    assert synths == []


def test_save_synth_creates_directory(sample_synth):
    """Test that save_synth creates output directory if it doesn't exist."""
    import tempfile
    import shutil

    temp_parent = Path(tempfile.mkdtemp())
    try:
        new_dir = temp_parent / "new_synths_dir"
        assert not new_dir.exists()

        storage.save_synth(sample_synth, output_dir=new_dir)
        assert new_dir.exists()

        # Verify file was saved
        consolidated_path = new_dir / "synths.json"
        assert consolidated_path.exists()
    finally:
        shutil.rmtree(temp_parent, ignore_errors=True)


def test_save_synth_preserves_existing_data(temp_output_dir, sample_synth):
    """Test that saving new synth preserves existing synths in consolidated file."""
    # Create initial synth
    synth1 = sample_synth.copy()
    synth1["id"] = "existing01"
    storage.save_synth(synth1, output_dir=temp_output_dir)

    # Add new synth
    synth2 = sample_synth.copy()
    synth2["id"] = "new02"
    storage.save_synth(synth2, output_dir=temp_output_dir)

    # Verify both exist
    synths = storage.load_consolidated_synths(output_dir=temp_output_dir)
    assert len(synths) == 2
    ids = [s["id"] for s in synths]
    assert "existing01" in ids
    assert "new02" in ids

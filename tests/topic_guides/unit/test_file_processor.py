"""
Unit Tests: File Processing Utilities

Tests the logic for scanning directories, filtering files, and hash detection.
"""

import tempfile
from pathlib import Path

import pytest


class TestFileScanning:
    """Unit tests for directory scanning and filtering logic."""

    def test_scan_directory_excludes_summary_md(self, tmp_path):
        """Test that scan_directory excludes summary.md file."""
        from synth_lab.topic_guides.file_processor import scan_directory

        # Create test directory with files
        guide_dir = tmp_path / "test-guide"
        guide_dir.mkdir()
        (guide_dir / "summary.md").write_text("# Summary")
        (guide_dir / "image.png").write_bytes(b"fake image")
        (guide_dir / "doc.pdf").write_bytes(b"fake pdf")

        files = scan_directory(guide_dir)

        # Should not include summary.md
        filenames = [f.name for f in files]
        assert "summary.md" not in filenames
        assert "image.png" in filenames
        assert "doc.pdf" in filenames

    def test_scan_directory_returns_pathlib_paths(self, tmp_path):
        """Test that scan_directory returns Path objects."""
        from synth_lab.topic_guides.file_processor import scan_directory

        guide_dir = tmp_path / "test-guide"
        guide_dir.mkdir()
        (guide_dir / "file.txt").write_text("test")

        files = scan_directory(guide_dir)

        assert len(files) == 1
        assert isinstance(files[0], Path)
        assert files[0].name == "file.txt"

    def test_scan_directory_empty_directory(self, tmp_path):
        """Test scanning empty directory returns empty list."""
        from synth_lab.topic_guides.file_processor import scan_directory

        guide_dir = tmp_path / "empty-guide"
        guide_dir.mkdir()

        files = scan_directory(guide_dir)

        assert len(files) == 0

    def test_is_supported_type_validates_extensions(self):
        """Test that is_supported_type correctly identifies supported file types."""
        from synth_lab.topic_guides.file_processor import is_supported_type

        # Supported types
        assert is_supported_type(Path("image.png")) is True
        assert is_supported_type(Path("photo.jpg")) is True
        assert is_supported_type(Path("photo.jpeg")) is True
        assert is_supported_type(Path("doc.pdf")) is True
        assert is_supported_type(Path("notes.md")) is True
        assert is_supported_type(Path("readme.txt")) is True

        # Unsupported types
        assert is_supported_type(Path("logo.svg")) is False
        assert is_supported_type(Path("video.mp4")) is False
        assert is_supported_type(Path("archive.zip")) is False


class TestHashDetection:
    """Unit tests for hash-based change detection."""

    def test_file_hash_changes_on_modification(self, tmp_path):
        """Test that compute_file_hash detects file changes."""
        from synth_lab.topic_guides.file_processor import compute_file_hash

        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        hash_before = compute_file_hash(test_file)

        # Modify file
        test_file.write_text("modified content")

        hash_after = compute_file_hash(test_file)

        assert hash_before != hash_after

    def test_file_hash_consistent_for_same_content(self, tmp_path):
        """Test that same content produces same hash."""
        from synth_lab.topic_guides.file_processor import compute_file_hash

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        content = "same content in both files"
        file1.write_text(content)
        file2.write_text(content)

        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)

        assert hash1 == hash2

    def test_file_hash_different_for_different_content(self, tmp_path):
        """Test that different content produces different hashes."""
        from synth_lab.topic_guides.file_processor import compute_file_hash

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("content A")
        file2.write_text("content B")

        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)

        assert hash1 != hash2

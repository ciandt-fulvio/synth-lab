"""
Integration Tests: Topic Guide Directory Creation

Tests the full workflow of creating topic guide directories including
file system operations and summary.md initialization.
"""

import tempfile
from pathlib import Path

import pytest


class TestTopicGuideDirectoryCreation:
    """Integration tests for topic guide directory creation workflow."""

    def test_create_directory_structure(self, tmp_path):
        """
        Test that topic guide directory is created with correct structure.

        Expected structure:
        data/topic_guides/<name>/
        └── summary.md
        """
        # This will be implemented after we create the actual functions
        # For now, this is a placeholder that should FAIL
        from synth_lab.services.topic_guides.cli import create_topic_guide

        guide_name = "test-guide"
        guides_dir = tmp_path / "topic_guides"

        create_topic_guide(name=guide_name, base_dir=guides_dir)

        guide_path = guides_dir / guide_name
        assert guide_path.exists(), f"Topic guide directory should exist at {guide_path}"
        assert guide_path.is_dir(), "Topic guide path should be a directory"

        summary_path = guide_path / "summary.md"
        assert summary_path.exists(), "summary.md should exist"
        assert summary_path.is_file(), "summary.md should be a file"

    def test_summary_md_initial_content(self, tmp_path):
        """
        Test that summary.md is initialized with correct template.

        Expected content:
        # contexto para o guide: <name>

        ## FILE DESCRIPTION
        """
        from synth_lab.services.topic_guides.cli import create_topic_guide

        guide_name = "content-test"
        guides_dir = tmp_path / "topic_guides"

        create_topic_guide(name=guide_name, base_dir=guides_dir)

        summary_path = guides_dir / guide_name / "summary.md"
        content = summary_path.read_text()

        assert f"# contexto para o guide: {guide_name}" in content
        assert "## FILE DESCRIPTION" in content

    def test_duplicate_creation_raises_error(self, tmp_path):
        """Test that creating duplicate topic guide raises appropriate error."""
        from synth_lab.services.topic_guides.cli import create_topic_guide

        guide_name = "duplicate-test"
        guides_dir = tmp_path / "topic_guides"

        # Create first time
        create_topic_guide(name=guide_name, base_dir=guides_dir)

        # Try to create again - should raise error
        with pytest.raises(FileExistsError):
            create_topic_guide(name=guide_name, base_dir=guides_dir)

    def test_nested_directory_creation(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        from synth_lab.services.topic_guides.cli import create_topic_guide

        # Use a path that doesn't exist yet
        guides_dir = tmp_path / "deep" / "nested" / "topic_guides"

        create_topic_guide(name="nested-guide", base_dir=guides_dir)

        assert guides_dir.exists()
        assert (guides_dir / "nested-guide").exists()
        assert (guides_dir / "nested-guide" / "summary.md").exists()

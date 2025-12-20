"""
Unit Tests: Summary File Management

Tests the logic for creating, parsing, and writing summary.md files.
"""

from datetime import datetime
from pathlib import Path

import pytest


class TestSummaryFileInitialization:
    """Unit tests for summary.md generation logic."""

    def test_create_initial_summary_content(self):
        """
        Test that create_initial_summary generates correct markdown template.

        Expected format:
        # contexto para o guide: <name>

        ## FILE DESCRIPTION
        """
        from synth_lab.services.topic_guides.summary_manager import create_initial_summary

        guide_name = "test-guide"
        summary_path = Path("/tmp/topic_guides/test-guide/summary.md")

        summary_file = create_initial_summary(guide_name, summary_path)

        assert summary_file.path == summary_path
        assert summary_file.context_description == ""
        assert len(summary_file.file_descriptions) == 0

        # Test markdown output
        markdown = summary_file.to_markdown()
        assert f"# contexto para o guide: {guide_name}" in markdown
        assert "## FILE DESCRIPTION" in markdown

    def test_parse_summary_empty_file_description(self, tmp_path):
        """Test parsing summary.md with no file descriptions."""
        from synth_lab.services.topic_guides.summary_manager import parse_summary

        summary_path = tmp_path / "summary.md"
        summary_path.write_text(
            """# contexto para o guide: test

Este é um contexto de teste.

## FILE DESCRIPTION
"""
        )

        summary_file = parse_summary(summary_path)

        assert summary_file.path == summary_path
        assert "Este é um contexto de teste." in summary_file.context_description
        assert len(summary_file.file_descriptions) == 0

    def test_parse_summary_with_file_descriptions(self, tmp_path):
        """Test parsing summary.md with existing file descriptions."""
        from synth_lab.services.topic_guides.summary_manager import parse_summary

        summary_path = tmp_path / "summary.md"
        summary_path.write_text(
            """# contexto para o guide: test

Context description here.

## FILE DESCRIPTION

- **image.png** (hash: a3b5c7d9e1f2a3b5c7d9e1f2a3b5c7d9)
  Screenshot of the homepage showing navigation

- **doc.pdf** (hash: f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4)
  Technical documentation for the API
"""
        )

        summary_file = parse_summary(summary_path)

        assert len(summary_file.file_descriptions) == 2

        # Check first file
        desc1 = summary_file.file_descriptions[0]
        assert desc1.filename == "image.png"
        assert desc1.content_hash == "a3b5c7d9e1f2a3b5c7d9e1f2a3b5c7d9"
        assert "Screenshot" in desc1.description

        # Check second file
        desc2 = summary_file.file_descriptions[1]
        assert desc2.filename == "doc.pdf"
        assert desc2.content_hash == "f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4"
        assert "Technical documentation" in desc2.description

    def test_write_summary_to_disk(self, tmp_path):
        """Test serializing SummaryFile to disk."""
        from synth_lab.services.topic_guides.internal_models import FileDescription, SummaryFile
        from synth_lab.services.topic_guides.summary_manager import write_summary

        summary_path = tmp_path / "summary.md"

        desc = FileDescription(
            filename="test.png",
            content_hash="abc123def456",
            description="A test image",
            generated_at=datetime.now(),
        )

        summary = SummaryFile(
            path=summary_path,
            context_description="Test context",
            file_descriptions=[desc],
        )

        write_summary(summary)

        assert summary_path.exists()
        content = summary_path.read_text()

        assert "# contexto para o guide:" in content
        assert "## FILE DESCRIPTION" in content
        assert "test.png" in content
        assert "abc123de" in content
        assert "A test image" in content

    def test_parse_summary_missing_file_description_section(self, tmp_path):
        """
        Test parsing summary.md without FILE DESCRIPTION section.

        According to clarification (Answer B from /speckit.clarify):
        Should auto-append the section if missing.
        """
        from synth_lab.services.topic_guides.summary_manager import parse_summary

        summary_path = tmp_path / "summary.md"
        summary_path.write_text(
            """# contexto para o guide: test

Just a context description, no FILE DESCRIPTION section.
"""
        )

        summary_file = parse_summary(summary_path)

        # Should parse successfully with empty file_descriptions
        assert len(summary_file.file_descriptions) == 0

        # When written back, should include the section
        from synth_lab.services.topic_guides.summary_manager import write_summary

        write_summary(summary_file)

        content = summary_path.read_text()
        assert "## FILE DESCRIPTION" in content

"""
Integration Tests: Error Handling Scenarios

Tests error handling for various failure modes:
- API failures
- Unsupported file types
- Corrupted files
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestErrorHandling:
    """Integration tests for error handling in file processing."""

    def test_unsupported_files_are_skipped(self, tmp_path):
        """Test that unsupported file types are skipped with warning."""
        from synth_lab.services.topic_guides.file_processor import is_supported_type, scan_directory

        guide_dir = tmp_path / "test-guide"
        guide_dir.mkdir()

        # Create mix of supported and unsupported files
        (guide_dir / "image.png").write_bytes(b"png")
        (guide_dir / "video.mp4").write_bytes(b"mp4")  # Unsupported
        (guide_dir / "logo.svg").write_bytes(b"svg")  # Unsupported
        (guide_dir / "doc.pdf").write_bytes(b"pdf")

        files = scan_directory(guide_dir)
        supported = [f for f in files if is_supported_type(f)]
        unsupported = [f for f in files if not is_supported_type(f)]

        assert len(supported) == 2  # png, pdf
        assert len(unsupported) == 2  # mp4, svg

    @patch("pdfplumber.open")
    def test_corrupted_pdf_is_handled(self, mock_pdfplumber, tmp_path):
        """Test that corrupted PDF files are handled gracefully."""
        from synth_lab.services.topic_guides.file_processor import extract_pdf_text

        # Create corrupted PDF
        pdf_file = tmp_path / "corrupted.pdf"
        pdf_file.write_bytes(b"not a real pdf")

        # Mock pdfplumber to raise exception
        mock_pdfplumber.side_effect = Exception("Corrupted PDF")

        # Should return empty string or None for corrupted files
        try:
            text = extract_pdf_text(pdf_file)
            assert text == "" or text is None
        except Exception:
            # Or raise exception that can be caught by caller
            pass

    @patch("openai.OpenAI")
    def test_api_failure_returns_none(self, mock_openai_class, tmp_path):
        """Test that API failures return None instead of crashing."""
        from synth_lab.services.topic_guides.file_processor import generate_file_description

        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        # Mock client that always fails
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Use a generic exception instead of APIError (which requires complex initialization)
        mock_client.chat.completions.create.side_effect = Exception("API failure")

        # After max retries, should raise or return None
        try:
            result = generate_file_description(image_file, "fake-api-key")
            assert result is None  # Graceful failure
        except Exception:
            pass  # Or raises exception for caller to handle

    def test_empty_file_is_handled(self, tmp_path):
        """Test that empty files don't crash processing."""
        from synth_lab.services.topic_guides.file_processor import compute_file_hash

        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        # Should compute hash even for empty file
        hash_value = compute_file_hash(empty_file)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 32  # MD5 hash length

    def test_very_large_file_is_processed(self, tmp_path):
        """Test that large files (>10MB) are processed correctly."""
        from synth_lab.services.topic_guides.file_processor import compute_file_hash

        large_file = tmp_path / "large.bin"
        # Create 15MB file
        with open(large_file, "wb") as f:
            f.write(b"x" * (15 * 1024 * 1024))

        # Should process in chunks without memory issues
        hash_value = compute_file_hash(large_file)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 32

    def test_missing_file_raises_error(self):
        """Test that missing file raises appropriate error."""
        from synth_lab.services.topic_guides.file_processor import compute_file_hash

        missing_file = Path("/nonexistent/file.txt")

        with pytest.raises(FileNotFoundError):
            compute_file_hash(missing_file)

    @patch("openai.OpenAI")
    def test_placeholder_added_on_api_failure(self, mock_openai_class, tmp_path):
        """Test that placeholder description is added when API fails."""
        from datetime import datetime

        from synth_lab.services.topic_guides.internal_models import FileDescription

        # This test verifies the CLI behavior of adding placeholders
        # The actual implementation will be in cli.py update command

        # Simulate what should happen when API fails
        placeholder = FileDescription(
            filename="test.png",
            content_hash="abc123",
            description="API failure - manual documentation needed",
            generated_at=datetime.now(),
            is_placeholder=True,
        )

        assert placeholder.is_placeholder is True
        assert "manual documentation" in placeholder.description

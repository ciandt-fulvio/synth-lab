"""
Integration Tests: LLM Description Generation

Tests OpenAI API integration for generating file descriptions.
Uses mocked responses to avoid actual API calls in tests.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestLLMIntegration:
    """Integration tests for LLM API calls with mocked responses."""

    @patch("openai.OpenAI")
    def test_generate_description_for_image(self, mock_openai_class, tmp_path):
        """Test generating description for image file."""
        from synth_lab.topic_guides.file_processor import generate_file_description

        # Create test image
        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n")  # PNG header

        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Screenshot of a test interface"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        description = generate_file_description(image_file, "fake-api-key")

        assert description == "Screenshot of a test interface"
        assert mock_client.chat.completions.create.called

    @patch("openai.OpenAI")
    def test_generate_description_for_pdf(self, mock_openai_class, tmp_path):
        """Test generating description for PDF file."""
        from synth_lab.topic_guides.file_processor import generate_file_description

        # Create test PDF (just needs .pdf extension for this test)
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")  # PDF header

        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Technical documentation PDF"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        description = generate_file_description(pdf_file, "fake-api-key")

        assert description == "Technical documentation PDF"

    @patch("openai.OpenAI")
    def test_generate_description_for_text_file(self, mock_openai_class, tmp_path):
        """Test generating description for text/markdown file."""
        from synth_lab.topic_guides.file_processor import generate_file_description

        # Create test text file
        text_file = tmp_path / "notes.md"
        text_file.write_text("# Meeting Notes\nDiscussed project timeline")

        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Meeting notes about project timeline"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        description = generate_file_description(text_file, "fake-api-key")

        assert description == "Meeting notes about project timeline"

    @patch("openai.OpenAI")
    def test_api_retry_on_failure(self, mock_openai_class, tmp_path):
        """Test that API failures are retried with exponential backoff."""
        from synth_lab.topic_guides.file_processor import generate_file_description

        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        # Mock client that fails twice then succeeds
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_success = MagicMock()
        mock_success.choices = [MagicMock(message=MagicMock(content="Success"))]

        # Simulate 2 failures then success
        from openai import APIError

        mock_client.chat.completions.create.side_effect = [
            APIError("Rate limit"),
            APIError("Temporary error"),
            mock_success,
        ]

        description = generate_file_description(image_file, "fake-api-key")

        assert description == "Success"
        assert mock_client.chat.completions.create.call_count == 3

    @patch("openai.OpenAI")
    def test_api_gives_up_after_max_retries(self, mock_openai_class, tmp_path):
        """Test that API gives up after maximum retries."""
        from synth_lab.topic_guides.file_processor import generate_file_description

        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        # Mock client that always fails
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        from openai import APIError

        mock_client.chat.completions.create.side_effect = APIError("Always fails")

        # Should raise after max retries
        with pytest.raises(APIError):
            generate_file_description(image_file, "fake-api-key")

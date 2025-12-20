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
        from synth_lab.services.topic_guides.file_processor import generate_file_description

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

    @patch("synth_lab.services.topic_guides.file_processor.extract_pdf_text")
    @patch("openai.OpenAI")
    def test_generate_description_for_pdf(self, mock_openai_class, mock_extract_pdf, tmp_path):
        """Test generating description for PDF file."""
        from synth_lab.services.topic_guides.file_processor import generate_file_description

        # Create test PDF (just needs .pdf extension for this test)
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")  # PDF header

        # Mock PDF text extraction
        mock_extract_pdf.return_value = "This is extracted PDF text content"

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
        from synth_lab.services.topic_guides.file_processor import generate_file_description

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
        from synth_lab.services.topic_guides.file_processor import generate_file_description

        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        # Mock client that fails twice then succeeds
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_success = MagicMock()
        mock_success.choices = [MagicMock(message=MagicMock(content="Success"))]

        # Simulate 2 failures then success using generic Exception
        mock_client.chat.completions.create.side_effect = [
            Exception("Rate limit"),
            Exception("Temporary error"),
            mock_success,
        ]

        description = generate_file_description(image_file, "fake-api-key")

        assert description == "Success"
        assert mock_client.chat.completions.create.call_count == 3

    @patch("openai.OpenAI")
    def test_api_gives_up_after_max_retries(self, mock_openai_class, tmp_path):
        """Test that API gives up after maximum retries and returns None."""
        from synth_lab.services.topic_guides.file_processor import generate_file_description

        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        # Mock client that always fails
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_client.chat.completions.create.side_effect = Exception("Always fails")

        # Should return None after max retries (exceptions are caught)
        description = generate_file_description(image_file, "fake-api-key")
        assert description is None

    @patch("openai.OpenAI")
    def test_generate_context_overview_from_descriptions(self, mock_openai_class):
        """Test generating contextual overview from file descriptions."""
        from synth_lab.services.topic_guides.file_processor import generate_context_overview

        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="This topic guide covers e-commerce workflows with screenshots and documentation."
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        descriptions = [
            "Screenshot of shopping cart page",
            "PDF user manual for checkout process",
            "Wireframe mockup of payment flow",
        ]

        overview = generate_context_overview(descriptions, "fake-api-key")

        assert overview == "This topic guide covers e-commerce workflows with screenshots and documentation."
        assert mock_client.chat.completions.create.called

    @patch("openai.OpenAI")
    def test_generate_context_overview_empty_list(self, mock_openai_class):
        """Test that empty description list returns empty string."""
        from synth_lab.services.topic_guides.file_processor import generate_context_overview

        overview = generate_context_overview([], "fake-api-key")

        assert overview == ""

    @patch("openai.OpenAI")
    def test_generate_context_overview_api_failure(self, mock_openai_class):
        """Test that API failure returns None."""
        from synth_lab.services.topic_guides.file_processor import generate_context_overview

        # Mock client that fails
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_client.chat.completions.create.side_effect = Exception("API failure")

        descriptions = ["Screenshot of homepage", "PDF documentation"]

        overview = generate_context_overview(descriptions, "fake-api-key")

        assert overview is None

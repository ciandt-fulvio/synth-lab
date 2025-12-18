"""
Test function calling integration for image loading.

This module tests:
- load_image_for_analysis() function
- Base64 encoding
- File not found handling
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
import base64
import pytest


class TestImageLoading:
    """Unit tests for image loading functionality."""

    def test_load_image_for_analysis_success(self, tmp_path):
        """Test successful image loading and base64 encoding."""
        from synth_lab.research.interview import load_image_for_analysis

        # Create a test topic guide directory with an image
        topic_guide_dir = tmp_path / "test-guide"
        topic_guide_dir.mkdir()

        # Create a simple test image (1x1 pixel PNG)
        test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        image_path = topic_guide_dir / "test.png"
        image_path.write_bytes(test_image_data)

        # Mock environment variable
        with patch.dict("os.environ", {"TOPIC_GUIDES_DIR": str(tmp_path)}):
            result = load_image_for_analysis("test.png", "test-guide")

        # Verify result is base64 encoded
        assert result is not None
        assert isinstance(result, str)

        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert decoded == test_image_data

    def test_load_image_for_analysis_file_not_found(self, tmp_path):
        """Test error handling when image file doesn't exist."""
        from synth_lab.research.interview import load_image_for_analysis

        # Create a test topic guide directory without the image
        topic_guide_dir = tmp_path / "test-guide"
        topic_guide_dir.mkdir()

        # Mock environment variable
        with patch.dict("os.environ", {"TOPIC_GUIDES_DIR": str(tmp_path)}):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_image_for_analysis("nonexistent.png", "test-guide")

        assert "nonexistent.png" in str(exc_info.value)
        assert "test-guide" in str(exc_info.value)

    def test_load_image_for_analysis_real_image(self):
        """Test loading a real image from compra-amazon topic guide."""
        from synth_lab.research.interview import load_image_for_analysis

        # This test uses the actual compra-amazon topic guide
        topic_guide_path = Path("data/topic_guides/compra-amazon")

        if not topic_guide_path.exists():
            pytest.skip("compra-amazon topic guide not found")

        # Test loading one of the images
        image_file = "01_amazon_homepage.PNG"
        image_path = topic_guide_path / image_file

        if not image_path.exists():
            pytest.skip(f"{image_file} not found in topic guide")

        result = load_image_for_analysis(image_file, "compra-amazon")

        # Verify result is base64 encoded
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 100  # Should be a substantial image

        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert len(decoded) > 0


class TestConversationTurnWithTools:
    """Unit tests for conversation_turn with function calling."""

    @patch("synth_lab.research.interview.OpenAI")
    def test_conversation_turn_no_tool_calls(self, mock_openai_class):
        """Test conversation_turn without tool calls (normal flow)."""
        from synth_lab.research.interview import conversation_turn, InterviewResponse

        # Setup mock
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_message = MagicMock()

        # Mock the response
        mock_response = InterviewResponse(
            message="Hello, how are you?",
            internal_notes="Test notes",
            should_end=False
        )
        mock_message.parsed = mock_response
        mock_message.tool_calls = None  # No tool calls
        mock_completion.choices = [MagicMock(message=mock_message)]
        mock_client.beta.chat.completions.parse.return_value = mock_completion

        # Call function
        result = conversation_turn(
            client=mock_client,
            messages=[],
            system_prompt="You are a helpful assistant.",
            model="gpt-5-mini"
        )

        # Verify
        assert result.message == "Hello, how are you?"
        assert result.should_end is False
        mock_client.beta.chat.completions.parse.assert_called_once()

    @patch("synth_lab.research.interview.load_image_for_analysis")
    @patch("synth_lab.research.interview.OpenAI")
    def test_conversation_turn_with_tool_call(self, mock_openai_class, mock_load_image):
        """Test conversation_turn with tool call for loading image."""
        from synth_lab.research.interview import conversation_turn, InterviewResponse

        # Setup mocks
        mock_client = MagicMock()
        mock_load_image.return_value = "base64encodedimagedata"

        # First completion - with tool call
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "load_image_for_analysis"
        mock_tool_call.function.arguments = '{"filename": "test.png"}'

        mock_message1 = MagicMock()
        mock_message1.content = "Let me load that image for you."
        mock_message1.tool_calls = [mock_tool_call]
        mock_message1.parsed = None

        mock_completion1 = MagicMock()
        mock_completion1.choices = [MagicMock(message=mock_message1)]

        # Second completion - final response after tool execution
        mock_response = InterviewResponse(
            message="I can see the image now.",
            internal_notes="Image loaded successfully",
            should_end=False
        )
        mock_message2 = MagicMock()
        mock_message2.parsed = mock_response
        mock_completion2 = MagicMock()
        mock_completion2.choices = [MagicMock(message=mock_message2)]

        # Configure mock to return different values on consecutive calls
        mock_client.beta.chat.completions.parse.side_effect = [
            mock_completion1,
            mock_completion2
        ]

        # Define tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "load_image_for_analysis",
                    "description": "Load an image file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"}
                        },
                        "required": ["filename"]
                    }
                }
            }
        ]

        # Call function
        messages = []
        result = conversation_turn(
            client=mock_client,
            messages=messages,
            system_prompt="You are a helpful assistant.",
            model="gpt-5-mini",
            tools=tools,
            topic_guide_name="test-guide"
        )

        # Verify
        assert result.message == "I can see the image now."
        assert mock_load_image.called
        mock_load_image.assert_called_once_with(
            filename="test.png",
            topic_guide_name="test-guide"
        )
        # Should call parse twice - once for initial, once after tool execution
        assert mock_client.beta.chat.completions.parse.call_count == 2


if __name__ == "__main__":
    """Validation with real data."""
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Load real image from compra-amazon
    total_tests += 1
    try:
        from synth_lab.research.interview import load_image_for_analysis

        topic_guide_path = Path("data/topic_guides/compra-amazon")
        if not topic_guide_path.exists():
            all_validation_failures.append(
                "compra-amazon topic guide not found")
        else:
            image_file = "01_amazon_homepage.PNG"
            image_path = topic_guide_path / image_file

            if not image_path.exists():
                all_validation_failures.append(f"{image_file} not found")
            else:
                result = load_image_for_analysis(image_file, "compra-amazon")

                if not isinstance(result, str):
                    all_validation_failures.append(
                        f"Expected str, got {type(result)}")
                elif len(result) < 100:
                    all_validation_failures.append(
                        f"Base64 result too short: {len(result)}")
                else:
                    # Verify it's valid base64
                    try:
                        decoded = base64.b64decode(result)
                        if len(decoded) == 0:
                            all_validation_failures.append(
                                "Decoded image is empty")
                    except Exception as e:
                        all_validation_failures.append(
                            f"Base64 decode failed: {e}")

    except Exception as e:
        all_validation_failures.append(f"Image loading test: {e}")

    # Test 2: Verify FileNotFoundError for missing image
    total_tests += 1
    try:
        from synth_lab.research.interview import load_image_for_analysis

        try:
            load_image_for_analysis("nonexistent.png", "compra-amazon")
            all_validation_failures.append(
                "Expected FileNotFoundError but no exception was raised")
        except FileNotFoundError:
            # Expected - test passes
            pass
        except Exception as e:
            all_validation_failures.append(
                f"Expected FileNotFoundError but got {type(e).__name__}")

    except Exception as e:
        all_validation_failures.append(f"FileNotFoundError test: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function calling integration is validated and ready for use")
        sys.exit(0)

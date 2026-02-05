"""
Centralized fixtures for mocking LLM clients.

Provides reusable mocks for OpenAI and other LLM services to enable
fast, deterministic testing without real API calls.

Usage:
    def test_my_service(mock_llm_client):
        service = MyService(llm_client=mock_llm_client)
        result = service.generate()
        assert result is not None
        mock_llm_client.complete.assert_called_once()
"""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_llm_client():
    """
    Mock LLM client for text completion (sync and async).

    Mocks common methods:
    - complete(prompt) -> str
    - complete_json(prompt) -> str (JSON string)
    - acomplete(prompt) -> str (async)

    Returns:
        MagicMock: Configured mock LLM client
    """
    mock = MagicMock()

    # Mock synchronous text completion
    mock.complete.return_value = "Mocked LLM response text"

    # Mock JSON completion (returns JSON string)
    mock.complete_json.return_value = '{"key": "value", "message": "mocked response"}'

    # Mock async methods
    mock.acomplete = AsyncMock(return_value="Async mocked response")

    return mock


@pytest.fixture
def mock_openai_client():
    """
    Mock OpenAI client for text completions.

    Mocks the OpenAI Python SDK structure:
    - client.chat.completions.create(...)

    Returns:
        MagicMock: Configured mock OpenAI client
    """
    mock = MagicMock()

    # Mock chat completion response structure
    mock_message = MagicMock()
    mock_message.content = "Mocked OpenAI response"
    mock_message.role = "assistant"

    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "stop"
    mock_choice.index = 0

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.id = "chatcmpl-mock123"
    mock_response.model = "gpt-4o-mini"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30

    # Configure mock to return this structure
    mock.chat.completions.create.return_value = mock_response

    return mock


@pytest.fixture
def mock_openai_image():
    """
    Mock OpenAI DALL-E image generation client.

    Mocks the OpenAI Python SDK structure for images:
    - client.images.generate(...)

    Returns:
        MagicMock: Configured mock OpenAI image client
    """
    mock = MagicMock()

    # Mock image data structure
    mock_image_data = MagicMock()
    mock_image_data.url = "https://mocked-image.com/test.png"
    mock_image_data.b64_json = None
    mock_image_data.revised_prompt = "Mocked revised prompt"

    # Mock response structure
    mock_response = MagicMock()
    mock_response.data = [mock_image_data]
    mock_response.created = 1234567890

    # Configure mock to return this structure
    mock.images.generate.return_value = mock_response

    return mock


@pytest.fixture
def mock_openai_image_bytes():
    """
    Mock OpenAI image generation that returns image bytes.

    Useful for testing avatar generation that downloads and processes images.

    Returns:
        tuple: (mock_client, mock_image_bytes)
    """
    from PIL import Image

    # Create a simple 200x200 white PNG image in memory
    img = Image.new("RGB", (200, 200), color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    mock_image_bytes = img_bytes.getvalue()

    # Mock OpenAI client
    mock = MagicMock()
    mock_image_data = MagicMock()
    mock_image_data.url = "https://mocked-image.com/test.png"
    mock_image_data.b64_json = None

    mock_response = MagicMock()
    mock_response.data = [mock_image_data]

    mock.images.generate.return_value = mock_response

    return mock, mock_image_bytes


@pytest.fixture
def mock_s3_storage():
    """
    Mock S3 storage operations (upload, download, check existence).

    Mocks common S3 operations:
    - upload_file(...)
    - download_file(...)
    - check_object_exists(...) -> bool
    - get_object_bytes(...) -> bytes

    Returns:
        MagicMock: Configured mock S3 storage client
    """
    mock = MagicMock()

    # Mock successful upload (returns S3 key)
    mock.upload_file.return_value = "avatars/test_synth_001.png"

    # Mock download (returns success)
    mock.download_file.return_value = True

    # Mock existence check (returns True by default)
    mock.check_object_exists.return_value = True

    # Mock get bytes (returns fake PNG bytes)
    from PIL import Image

    img = Image.new("RGB", (200, 200), color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    mock.get_object_bytes.return_value = img_bytes.getvalue()

    return mock


@pytest.fixture
def mock_http_image_download(monkeypatch):
    """
    Mock HTTP image download for avatar generation.

    Patches requests.get to return a fake PNG image.

    Returns:
        MagicMock: Mock response object
    """
    from PIL import Image

    # Create fake image bytes
    img = Image.new("RGB", (1024, 1024), color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = img_bytes.getvalue()
    mock_response.headers = {"Content-Type": "image/png"}

    def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr("requests.get", mock_get)

    return mock_response


# Convenience fixture combining multiple mocks for avatar generation
@pytest.fixture
def mock_avatar_generation_stack(mock_openai_image_bytes, mock_s3_storage, mock_http_image_download):
    """
    Complete mock stack for avatar generation testing.

    Combines:
    - OpenAI image generation (with bytes)
    - S3 storage operations
    - HTTP image download

    Returns:
        dict: Dictionary with all mocks
    """
    mock_openai, mock_image_bytes = mock_openai_image_bytes

    return {
        "openai_client": mock_openai,
        "image_bytes": mock_image_bytes,
        "s3_storage": mock_s3_storage,
        "http_response": mock_http_image_download,
    }

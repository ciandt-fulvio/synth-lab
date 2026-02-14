"""
Integration tests for materials tool with S3.

Tests the materials tool with mocked S3 operations to verify
the complete flow from material request to presigned URL response.

References:
    - contracts/materials_tool.yaml: Tool contract
"""

from unittest.mock import Mock, patch

import pytest

from synth_lab.services.research_agentic.tools import _load_material_content


@pytest.fixture
def mock_material_repository():
    """Create mock material repository with sample data."""
    repo = Mock()

    # Sample material
    material = Mock()
    material.id = "mat_test123"
    material.experiment_id = "exp_123"
    material.file_url = "https://s3.amazonaws.com/test-bucket/materials/exp_123/mat_test123.png"
    material.mime_type = "image/png"
    material.file_name = "test-wireframe.png"
    material.file_size = 1_500_000
    material.description = "Test wireframe screenshot"

    repo.get_by_id.return_value = material
    return repo


@pytest.fixture
def mock_s3_client():
    """Create mock S3 client (kept for backward compatibility)."""
    client = Mock()
    return client


class TestMaterialsToolIntegration:
    """Integration tests for materials tool."""

    @patch('synth_lab.services.research_agentic.tools.generate_view_url')
    def test_load_image_material(self, mock_generate_url, mock_material_repository, mock_s3_client):
        """Test loading an image material returns presigned URL."""
        # Mock presigned URL generation
        mock_generate_url.return_value = "https://s3.amazonaws.com/bucket/materials/exp_123/mat_test123.png?X-Amz-Expires=3600"

        result = _load_material_content(
            material_id="mat_test123",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            storage_client=mock_s3_client
        )

        # Should be a presigned URL
        assert result.startswith("https://")
        assert "X-Amz-Expires" in result

        # Should have called generate_view_url with correct object_key
        mock_generate_url.assert_called_once()
        call_args = mock_generate_url.call_args[0]
        assert "materials/exp_123/mat_test123.png" in call_args[0]

    @patch('synth_lab.services.research_agentic.tools.generate_view_url')
    def test_load_pdf_material(self, mock_generate_url, mock_material_repository, mock_s3_client):
        """Test loading a PDF material returns presigned URL."""
        # Setup PDF material
        pdf_material = Mock()
        pdf_material.id = "mat_pdf456"
        pdf_material.experiment_id = "exp_123"
        pdf_material.file_url = "https://s3.amazonaws.com/test-bucket/materials/exp_123/mat_pdf456.pdf"
        pdf_material.mime_type = "application/pdf"
        pdf_material.file_name = "spec.pdf"
        pdf_material.file_size = 500_000
        pdf_material.description = "Product specification"

        mock_material_repository.get_by_id.return_value = pdf_material
        mock_generate_url.return_value = "https://s3.amazonaws.com/bucket/materials/exp_123/mat_pdf456.pdf?X-Amz-Expires=3600"

        result = _load_material_content(
            material_id="mat_pdf456",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            storage_client=mock_s3_client
        )

        # Should be a presigned URL
        assert result.startswith("https://")
        assert "X-Amz-Expires" in result

    @patch('synth_lab.services.research_agentic.tools.generate_view_url')
    def test_load_video_material(self, mock_generate_url, mock_material_repository, mock_s3_client):
        """Test loading a video material returns presigned URL."""
        # Setup video material
        video_material = Mock()
        video_material.id = "mat_video789"
        video_material.experiment_id = "exp_123"
        video_material.file_url = "https://s3.amazonaws.com/test-bucket/materials/exp_123/mat_video789.mp4"
        video_material.mime_type = "video/mp4"
        video_material.file_name = "demo.mp4"
        video_material.file_size = 10_000_000
        video_material.description = "Product demo video"

        mock_material_repository.get_by_id.return_value = video_material
        mock_generate_url.return_value = "https://s3.amazonaws.com/bucket/materials/exp_123/mat_video789.mp4?X-Amz-Expires=3600"

        result = _load_material_content(
            material_id="mat_video789",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            storage_client=mock_s3_client
        )

        # Should be a presigned URL
        assert result.startswith("https://")
        assert "X-Amz-Expires" in result

    def test_load_nonexistent_material_returns_error(
        self, mock_material_repository, mock_s3_client
    ):
        """Test loading non-existent material returns error message."""
        mock_material_repository.get_by_id.return_value = None

        result = _load_material_content(
            material_id="mat_nonexistent",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            storage_client=mock_s3_client
        )

        # Should return error message (string)
        assert isinstance(result, str)
        assert "não encontrado" in result.lower()

    @patch('synth_lab.services.research_agentic.tools.generate_view_url')
    def test_load_deleted_s3_file_returns_error(
        self, mock_generate_url, mock_material_repository, mock_s3_client
    ):
        """Test loading material with deleted S3 file returns error."""
        # Mock S3 error when generating URL
        mock_generate_url.side_effect = Exception("NoSuchKey: The specified key does not exist")

        result = _load_material_content(
            material_id="mat_test123",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            storage_client=mock_s3_client
        )

        # Should return error message about missing/removed file
        assert isinstance(result, str)
        assert "erro" in result.lower() or "error" in result.lower()

    @patch('synth_lab.services.research_agentic.tools.generate_view_url')
    def test_load_timeout_returns_error(
        self, mock_generate_url, mock_material_repository, mock_s3_client
    ):
        """Test timeout during URL generation returns error."""
        # Simulate timeout
        mock_generate_url.side_effect = TimeoutError("Request timeout")

        result = _load_material_content(
            material_id="mat_test123",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            storage_client=mock_s3_client
        )

        # Should return timeout error
        assert isinstance(result, str)
        assert "erro" in result.lower()

    def test_load_large_file_returns_size_error(
        self, mock_material_repository, mock_s3_client
    ):
        """Test loading file >50MB returns size error."""
        # Setup large file
        large_material = Mock()
        large_material.id = "mat_large"
        large_material.experiment_id = "exp_123"
        large_material.file_url = "https://s3.amazonaws.com/test-bucket/materials/exp_123/large.mp4"
        large_material.mime_type = "video/mp4"
        large_material.file_name = "large-video.mp4"
        large_material.file_size = 60_000_000  # 60 MB
        large_material.description = "Large product demo video"

        mock_material_repository.get_by_id.return_value = large_material

        result = _load_material_content(
            material_id="mat_large",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            storage_client=mock_s3_client
        )

        # Should return size error
        assert isinstance(result, str)
        assert "grande" in result.lower() or "50mb" in result.lower()

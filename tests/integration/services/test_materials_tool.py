"""
Integration tests for materials tool with S3.

Tests the materials tool with mocked S3 operations to verify
the complete flow from material request to data URI response.

References:
    - contracts/materials_tool.yaml: Tool contract
"""

import pytest
import base64
from unittest.mock import Mock, patch
from synth_lab.services.research_agentic.tools import create_materials_tool, _load_material_content


@pytest.fixture
def mock_material_repository():
    """Create mock material repository with sample data."""
    repo = Mock()

    # Sample material
    material = Mock()
    material.id = "mat_test123"
    material.experiment_id = "exp_123"
    material.file_url = "s3://test-bucket/materials/mat_test123.png"
    material.mime_type = "image/png"
    material.file_name = "test-wireframe.png"
    material.file_size = 1_500_000

    repo.get_by_id.return_value = material
    return repo


@pytest.fixture
def mock_s3_client():
    """Create mock S3 client."""
    client = Mock()
    # Return fake image data
    client.download_from_s3.return_value = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    return client


class TestMaterialsToolIntegration:
    """Integration tests for materials tool."""

    def test_load_image_material(self, mock_material_repository, mock_s3_client):
        """Test loading an image material returns valid data URI."""
        result = _load_material_content(
            material_id="mat_test123",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            s3_client=mock_s3_client
        )

        # Should be a data URI
        assert result.startswith("data:image/png;base64,")

        # Should contain valid base64
        data_part = result.split("base64,")[1]
        decoded = base64.b64decode(data_part)
        assert decoded == b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

    def test_load_pdf_material(self, mock_material_repository, mock_s3_client):
        """Test loading a PDF material returns valid data URI."""
        # Setup PDF material
        pdf_material = Mock()
        pdf_material.id = "mat_pdf456"
        pdf_material.experiment_id = "exp_123"
        pdf_material.file_url = "s3://test-bucket/materials/mat_pdf456.pdf"
        pdf_material.mime_type = "application/pdf"
        pdf_material.file_name = "spec.pdf"
        pdf_material.file_size = 500_000

        mock_material_repository.get_by_id.return_value = pdf_material
        mock_s3_client.download_from_s3.return_value = b"%PDF-1.4"

        result = _load_material_content(
            material_id="mat_pdf456",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            s3_client=mock_s3_client
        )

        # Should be PDF data URI
        assert result.startswith("data:application/pdf;base64,")

    def test_load_video_material(self, mock_material_repository, mock_s3_client):
        """Test loading a video material returns valid data URI."""
        # Setup video material
        video_material = Mock()
        video_material.id = "mat_video789"
        video_material.experiment_id = "exp_123"
        video_material.file_url = "s3://test-bucket/materials/mat_video789.mp4"
        video_material.mime_type = "video/mp4"
        video_material.file_name = "demo.mp4"
        video_material.file_size = 10_000_000

        mock_material_repository.get_by_id.return_value = video_material
        mock_s3_client.download_from_s3.return_value = b"\x00\x00\x00\x20ftyp"

        result = _load_material_content(
            material_id="mat_video789",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            s3_client=mock_s3_client
        )

        # Should be video data URI
        assert result.startswith("data:video/mp4;base64,")

    def test_load_nonexistent_material_returns_error(
        self, mock_material_repository, mock_s3_client
    ):
        """Test loading non-existent material returns error message."""
        mock_material_repository.get_by_id.return_value = None

        result = _load_material_content(
            material_id="mat_nonexistent",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            s3_client=mock_s3_client
        )

        # Should return error message (string)
        assert isinstance(result, str)
        assert "não encontrado" in result.lower() or "not found" in result.lower()

    def test_load_deleted_s3_file_returns_error(
        self, mock_material_repository, mock_s3_client
    ):
        """Test loading material with deleted S3 file returns error."""
        mock_s3_client.download_from_s3.side_effect = Exception("NoSuchKey")

        result = _load_material_content(
            material_id="mat_test123",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            s3_client=mock_s3_client
        )

        # Should return error message about missing/removed file
        assert isinstance(result, str)
        assert ("não encontrado" in result.lower() or "removido" in result.lower() or
                "error" in result.lower())

    @patch('synth_lab.services.research_agentic.tools.logger')
    def test_load_timeout_returns_error(
        self, mock_logger, mock_material_repository, mock_s3_client
    ):
        """Test timeout during S3 download returns error."""
        # Simulate timeout
        mock_s3_client.download_from_s3.side_effect = TimeoutError("Request timeout")

        result = _load_material_content(
            material_id="mat_test123",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            s3_client=mock_s3_client
        )

        # Should return timeout error
        assert isinstance(result, str)
        assert "timeout" in result.lower() or "erro" in result.lower()

    def test_load_large_file_returns_size_error(
        self, mock_material_repository, mock_s3_client
    ):
        """Test loading file >50MB returns size error."""
        # Setup large file
        large_material = Mock()
        large_material.id = "mat_large"
        large_material.experiment_id = "exp_123"
        large_material.file_url = "s3://test-bucket/materials/large.mp4"
        large_material.mime_type = "video/mp4"
        large_material.file_name = "large-video.mp4"
        large_material.file_size = 60_000_000  # 60 MB

        mock_material_repository.get_by_id.return_value = large_material

        result = _load_material_content(
            material_id="mat_large",
            experiment_id="exp_123",
            material_repository=mock_material_repository,
            s3_client=mock_s3_client
        )

        # Should return size error
        assert isinstance(result, str)
        assert "grande" in result.lower() or "size" in result.lower() or "50mb" in result.lower()


# This module needs implementation
if __name__ == "__main__":
    import sys

    print("❌ EXPECTED TO FAIL - materials tool not yet implemented")
    print("Run pytest to see actual integration test failures")
    sys.exit(1)

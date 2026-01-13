"""
Unit tests for materials retrieval tool.

Tests the creation and functionality of the materials tool that allows
LLMs to load experiment materials on demand during interviews.

References:
    - contracts/materials_tool.yaml: API contract
    - research.md: Tool design decisions
"""

import pytest
from unittest.mock import Mock, patch
from synth_lab.services.research_agentic.tools import (
    create_materials_tool,
    MaterialToolResponse,
    _load_material_content
)


class TestMaterialToolResponse:
    """Test MaterialToolResponse model."""

    def test_success_response(self):
        """Test creating a success response."""
        response = MaterialToolResponse.success(
            material_id="mat_abc123",
            data_uri="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==",
            mime_type="image/png",
            file_name="test.png"
        )

        assert response.status == "success"
        assert response.material_id == "mat_abc123"
        assert response.data_uri == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="
        assert response.error_message is None
        assert response.mime_type == "image/png"
        assert response.file_name == "test.png"

    def test_error_response(self):
        """Test creating an error response."""
        response = MaterialToolResponse.error(
            material_id="mat_invalid",
            error_message="Material não encontrado"
        )

        assert response.status == "error"
        assert response.material_id == "mat_invalid"
        assert response.data_uri is None
        assert response.error_message == "Material não encontrado"
        assert response.mime_type is None
        assert response.file_name is None


class TestCreateMaterialsTool:
    """Test materials tool creation and behavior."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock material repository."""
        repo = Mock()
        return repo

    @pytest.fixture
    def sample_material(self):
        """Create sample material."""
        material = Mock()
        material.id = "mat_abc123"
        material.experiment_id = "exp_123"
        material.file_url = "https://endpoint/bucket/materials/exp_123/mat_abc123.png"
        material.mime_type = "image/png"
        material.file_name = "wireframe.png"
        material.file_size = 2_300_000
        return material

    def test_create_tool_with_valid_params(self, mock_repository):
        """Test tool is created successfully with valid parameters."""
        tool = create_materials_tool(
            experiment_id="exp_123",
            material_repository=mock_repository,
        )

        # Tool should be a FunctionTool
        assert tool is not None
        assert hasattr(tool, 'name')
        # Tool name should be ver_material
        assert tool.name == "ver_material"

    def test_tool_validates_material_id_format(self, mock_repository):
        """Test tool validates material ID follows mat_XXXXXX format."""
        tool = create_materials_tool(
            experiment_id="exp_123",
            material_repository=mock_repository,
        )

        # Invalid ID should be rejected
        # (This will be tested when the tool function is called)
        assert tool is not None

    def test_tool_validates_experiment_ownership(
        self, mock_repository, sample_material
    ):
        """Test tool rejects materials from other experiments."""
        # Setup: Material belongs to different experiment
        mock_repository.get_by_id.return_value = sample_material
        sample_material.experiment_id = "exp_other"

        tool = create_materials_tool(
            experiment_id="exp_123",  # Different from material's experiment
            material_repository=mock_repository,
        )

        # When tool function is called, it should validate ownership
        # This will be tested in integration tests
        assert tool is not None


class TestMaterialToolFunction:
    """Test the actual tool function behavior."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock material repository."""
        repo = Mock()
        return repo

    @pytest.fixture
    def sample_material(self):
        """Create sample material."""
        material = Mock()
        material.id = "mat_abc123"
        material.experiment_id = "exp_123"
        material.file_url = "https://endpoint/bucket/materials/exp_123/mat_abc123.png"
        material.mime_type = "image/png"
        material.file_name = "wireframe.png"
        material.file_size = 2_300_000
        return material

    @patch("synth_lab.services.research_agentic.tools.generate_view_url")
    def test_function_returns_view_url_on_success(
        self, mock_generate_url, mock_repository, sample_material
    ):
        """Test function returns presigned view URL on successful load."""
        # Setup
        mock_repository.get_by_id.return_value = sample_material
        mock_generate_url.return_value = "https://presigned-url.example.com/mat_abc123.png?sig=abc123"

        # Call the core function directly
        result = _load_material_content(
            material_id="mat_abc123",
            experiment_id="exp_123",
            material_repository=mock_repository,
        )

        # Should return presigned URL
        assert result.startswith("https://")
        assert "presigned-url" in result

    def test_function_returns_error_for_nonexistent_material(
        self, mock_repository
    ):
        """Test function returns error when material doesn't exist."""
        # Setup: Repository returns None
        mock_repository.get_by_id.return_value = None

        # Call with invalid ID
        result = _load_material_content(
            material_id="mat_invalid",
            experiment_id="exp_123",
            material_repository=mock_repository,
        )

        # Should return error message
        assert "não encontrado" in result.lower()

    def test_function_validates_experiment_ownership(
        self, mock_repository, sample_material
    ):
        """Test function rejects materials from other experiments."""
        # Setup: Material from different experiment
        sample_material.experiment_id = "exp_other"
        mock_repository.get_by_id.return_value = sample_material

        # Call function
        result = _load_material_content(
            material_id="mat_abc123",
            experiment_id="exp_123",
            material_repository=mock_repository,
        )

        # Should return error
        assert "não encontrado" in result.lower()

    @patch("synth_lab.services.research_agentic.tools.generate_view_url")
    def test_function_handles_s3_url_generation_failure(
        self, mock_generate_url, mock_repository, sample_material
    ):
        """Test function handles URL generation errors gracefully."""
        # Setup: URL generation fails
        mock_repository.get_by_id.return_value = sample_material
        mock_generate_url.side_effect = Exception("S3 error")

        # Call function
        result = _load_material_content(
            material_id="mat_abc123",
            experiment_id="exp_123",
            material_repository=mock_repository,
        )

        # Should return error message
        assert isinstance(result, str)
        assert "erro" in result.lower()


# This module needs to be implemented for tests to pass
if __name__ == "__main__":
    import sys

    print("Running materials tool unit tests...")
    print("Use pytest to run all tests")
    sys.exit(0)

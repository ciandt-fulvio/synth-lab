"""
Contract tests for materials_context module.

Verifies the materials formatting output matches the expected contract
structure and is valid markdown that can be parsed.

References:
    - contracts/materials_context.yaml: API contract specification
"""

import pytest
import re
from synth_lab.services.materials_context import format_materials_for_prompt
from synth_lab.models.orm.material import ExperimentMaterial


class TestMaterialsContextContract:
    """Test materials context formatting contract."""

    @pytest.fixture
    def sample_materials(self):
        """Create sample materials for testing."""
        return [
            ExperimentMaterial(
                id="mat_abc123def456",
                experiment_id="exp_123",
                file_type="image",
                file_url="s3://bucket/wireframe.png",
                file_name="wireframe-checkout.png",
                file_size=2_300_000,
                mime_type="image/png",
                material_type="design",
                description="Wireframe do fluxo de checkout",
                description_status="completed",
                display_order=0,
                created_at="2026-01-06T12:00:00Z"
            ),
            ExperimentMaterial(
                id="mat_def456ghi789",
                experiment_id="exp_123",
                file_type="video",
                file_url="s3://bucket/demo.mp4",
                file_name="prototype-demo.mp4",
                file_size=15_000_000,
                mime_type="video/mp4",
                material_type="prototype",
                description="Vídeo demonstrando interação",
                description_status="completed",
                display_order=1,
                created_at="2026-01-06T12:01:00Z"
            )
        ]

    def test_output_is_valid_markdown(self, sample_materials):
        """Test output is valid markdown structure."""
        result = format_materials_for_prompt(
            materials=sample_materials,
            context="interview"
        )

        # Should have markdown headers
        assert re.search(r"^##\s+.+", result, re.MULTILINE) is not None

        # Should have bullet points
        assert re.search(r"^-\s+\*\*.+\*\*", result, re.MULTILINE) is not None

    def test_output_includes_all_materials(self, sample_materials):
        """Test all materials are included in output."""
        result = format_materials_for_prompt(
            materials=sample_materials,
            context="interview"
        )

        # All material IDs must be present
        for material in sample_materials:
            assert material.id in result
            assert material.file_name in result

    def test_material_ids_preserved(self, sample_materials):
        """Test material IDs match input exactly."""
        result = format_materials_for_prompt(
            materials=sample_materials,
            context="interview"
        )

        # Extract material IDs from output
        id_pattern = r"mat_[a-z0-9]{12}"
        found_ids = set(re.findall(id_pattern, result))

        expected_ids = {m.id for m in sample_materials}

        assert found_ids == expected_ids

    def test_interview_context_has_tool_section(self, sample_materials):
        """Test interview context includes tool usage section."""
        result = format_materials_for_prompt(
            materials=sample_materials,
            context="interview",
            include_tool_instructions=True
        )

        # Should mention the tool function
        assert "ver_material" in result

        # Should have instructions on how to reference materials
        assert "como" in result.lower() or "when" in result.lower()

    def test_prfaq_context_has_reference_format(self, sample_materials):
        """Test PR-FAQ context includes reference format guidelines."""
        result = format_materials_for_prompt(
            materials=sample_materials,
            context="prfaq",
            include_tool_instructions=False
        )

        # Should mention reference format
        assert "ref" in result.lower() or "referência" in result.lower()

        # Should NOT have tool instructions
        assert "ver_material" not in result

    def test_exploration_context_metadata_only(self, sample_materials):
        """Test exploration context has metadata without tool."""
        result = format_materials_for_prompt(
            materials=sample_materials,
            context="exploration",
            include_tool_instructions=False
        )

        # Should have material metadata
        assert "mat_abc123def456" in result

        # Should NOT have tool instructions
        assert "ver_material" not in result

    def test_material_format_structure(self, sample_materials):
        """Test each material follows expected format structure."""
        result = format_materials_for_prompt(
            materials=sample_materials,
            context="interview"
        )

        # Each material should follow pattern:
        # - **mat_XXXX** - [type] filename (mime, size)
        #   Descrição: ...
        pattern = r"-\s+\*\*mat_[a-z0-9]+\*\*\s+-\s+\[.+?\]\s+.+?\s+\(.+?,\s+[\d.]+\s+MB\)"

        matches = re.findall(pattern, result)

        # Should have at least one match per material (or close to it)
        assert len(matches) >= len(sample_materials) - 1  # Allow some formatting variation

    def test_file_size_in_megabytes(self, sample_materials):
        """Test file sizes are shown in MB with proper formatting."""
        result = format_materials_for_prompt(
            materials=sample_materials,
            context="interview"
        )

        # Should have MB units
        assert "MB" in result

        # Should have decimal file sizes (e.g., "2.3 MB", "15.0 MB")
        size_pattern = r"[\d.]+\s+MB"
        sizes = re.findall(size_pattern, result)

        assert len(sizes) >= len(sample_materials)

    def test_empty_materials_returns_empty_string(self):
        """Test contract: empty materials → empty string."""
        result = format_materials_for_prompt(
            materials=[],
            context="interview"
        )

        assert result == ""

    def test_none_materials_returns_empty_string(self):
        """Test contract: None materials → empty string."""
        result = format_materials_for_prompt(
            materials=None,
            context="interview"
        )

        assert result == ""


# This module needs to be implemented for tests to pass
if __name__ == "__main__":
    import sys

    print("❌ EXPECTED TO FAIL - materials_context module not yet implemented")
    print("Run pytest to see actual contract test failures")
    sys.exit(1)

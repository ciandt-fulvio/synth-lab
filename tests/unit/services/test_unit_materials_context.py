"""
Unit tests for materials_context module.

Tests the formatting of experiment materials for LLM prompts across
different contexts (interview, prfaq, exploration).

References:
    - data-model.md: MaterialContext, MaterialReference definitions
    - contracts/materials_context.yaml: API contracts
"""

import pytest
from synth_lab.services.materials_context import (
    MaterialContext,
    format_materials_for_prompt,
    to_material_context,
    validate_token_budget,
)
from synth_lab.models.orm.material import ExperimentMaterial


class TestToMaterialContext:
    """Test ORM to MaterialContext transformation."""

    def test_transform_with_all_fields(self):
        """Test transformation with all fields populated."""
        material = ExperimentMaterial(
            id="mat_abc123def456",
            experiment_id="exp_123",
            file_type="image",
            file_url="s3://bucket/mat_abc123def456.png",
            thumbnail_url="s3://bucket/thumb_abc123.png",
            file_name="wireframe-checkout.png",
            file_size=2_300_000,  # 2.3 MB
            mime_type="image/png",
            material_type="design",
            description="Wireframe do fluxo de checkout com 8 campos",
            description_status="completed",
            display_order=0,
            created_at="2026-01-06T12:00:00Z"
        )

        context = to_material_context(material)

        assert context.material_id == "mat_abc123def456"
        assert context.material_type == "design"
        assert context.file_name == "wireframe-checkout.png"
        assert context.mime_type == "image/png"
        assert context.description == "Wireframe do fluxo de checkout com 8 campos"
        assert context.file_size_mb == 2.3  # Rounded to 2 decimals

    def test_transform_with_none_description(self):
        """Test transformation when description is None."""
        material = ExperimentMaterial(
            id="mat_test123",
            experiment_id="exp_123",
            file_type="video",
            file_url="s3://bucket/video.mp4",
            file_name="demo.mp4",
            file_size=15_000_000,  # 15 MB
            mime_type="video/mp4",
            material_type="prototype",
            description=None,  # No description
            description_status="pending",
            display_order=1,
            created_at="2026-01-06T12:00:00Z"
        )

        context = to_material_context(material)

        assert context.description is None
        assert context.file_size_mb == 15.0

    def test_file_size_rounding(self):
        """Test file size is rounded to 2 decimal places."""
        material = ExperimentMaterial(
            id="mat_test",
            experiment_id="exp_123",
            file_type="document",
            file_url="s3://bucket/doc.pdf",
            file_name="spec.pdf",
            file_size=1_234_567,  # 1.234567 MB
            mime_type="application/pdf",
            material_type="spec",
            description="Specification",
            description_status="completed",
            display_order=0,
            created_at="2026-01-06T12:00:00Z"
        )

        context = to_material_context(material)

        assert context.file_size_mb == 1.23  # Rounded


class TestFormatMaterialsForPrompt:
    """Test formatting materials for different LLM contexts."""

    def test_format_empty_materials_list(self):
        """Test with empty materials list returns empty string."""
        result = format_materials_for_prompt(
            materials=[],
            context="interview"
        )

        assert result == ""

    def test_format_single_material_interview_context(self):
        """Test formatting single material for interview context."""
        materials = [
            ExperimentMaterial(
                id="mat_abc123",
                experiment_id="exp_123",
                file_type="image",
                file_url="s3://bucket/wireframe.png",
                file_name="wireframe-checkout.png",
                file_size=2_300_000,
                mime_type="image/png",
                material_type="design",
                description="Wireframe do checkout",
                description_status="completed",
                display_order=0,
                created_at="2026-01-06T12:00:00Z"
            )
        ]

        result = format_materials_for_prompt(
            materials=materials,
            context="interview",
            include_tool_instructions=True
        )

        # Verify structure
        assert "## Materiais Anexados" in result
        assert "mat_abc123" in result
        assert "wireframe-checkout.png" in result
        assert "image/png" in result
        assert "2.3 MB" in result
        assert "Wireframe do checkout" in result
        assert "ver_material" in result  # Tool instructions included

    def test_format_multiple_materials(self):
        """Test formatting multiple materials preserves order."""
        materials = [
            ExperimentMaterial(
                id="mat_001",
                experiment_id="exp_123",
                file_type="image",
                file_url="s3://bucket/img1.png",
                file_name="first.png",
                file_size=1_000_000,
                mime_type="image/png",
                material_type="design",
                description="First material",
                description_status="completed",
                display_order=0,
                created_at="2026-01-06T12:00:00Z"
            ),
            ExperimentMaterial(
                id="mat_002",
                experiment_id="exp_123",
                file_type="video",
                file_url="s3://bucket/video.mp4",
                file_name="second.mp4",
                file_size=10_000_000,
                mime_type="video/mp4",
                material_type="prototype",
                description="Second material",
                description_status="completed",
                display_order=1,
                created_at="2026-01-06T12:01:00Z"
            )
        ]

        result = format_materials_for_prompt(
            materials=materials,
            context="interview"
        )

        # Verify both materials appear
        assert "mat_001" in result
        assert "mat_002" in result
        assert "first.png" in result
        assert "second.mp4" in result

        # Verify order (mat_001 should appear before mat_002)
        pos_001 = result.index("mat_001")
        pos_002 = result.index("mat_002")
        assert pos_001 < pos_002

    def test_format_prfaq_context(self):
        """Test formatting for PR-FAQ context (no tool instructions)."""
        materials = [
            ExperimentMaterial(
                id="mat_test",
                experiment_id="exp_123",
                file_type="image",
                file_url="s3://bucket/img.png",
                file_name="test.png",
                file_size=1_000_000,
                mime_type="image/png",
                material_type="design",
                description="Test image",
                description_status="completed",
                display_order=0,
                created_at="2026-01-06T12:00:00Z"
            )
        ]

        result = format_materials_for_prompt(
            materials=materials,
            context="prfaq",
            include_tool_instructions=False
        )

        assert "Materiais de Referência" in result
        assert "mat_test" in result
        # Should have reference format instructions, not tool instructions
        assert "ref:" in result or "observação" in result
        assert "ver_material" not in result  # No tool in PR-FAQ

    def test_format_exploration_context(self):
        """Test formatting for exploration context (metadata only)."""
        materials = [
            ExperimentMaterial(
                id="mat_explore",
                experiment_id="exp_123",
                file_type="document",
                file_url="s3://bucket/doc.pdf",
                file_name="spec.pdf",
                file_size=500_000,
                mime_type="application/pdf",
                material_type="spec",
                description="Specification document",
                description_status="completed",
                display_order=0,
                created_at="2026-01-06T12:00:00Z"
            )
        ]

        result = format_materials_for_prompt(
            materials=materials,
            context="exploration",
            include_tool_instructions=False
        )

        assert "mat_explore" in result
        assert "spec.pdf" in result
        assert "ver_material" not in result  # No tool in exploration

    def test_format_missing_description(self):
        """Test formatting handles None description gracefully."""
        materials = [
            ExperimentMaterial(
                id="mat_nodesc",
                experiment_id="exp_123",
                file_type="image",
                file_url="s3://bucket/img.png",
                file_name="no-desc.png",
                file_size=1_000_000,
                mime_type="image/png",
                material_type="other",
                description=None,  # Missing description
                description_status="pending",
                display_order=0,
                created_at="2026-01-06T12:00:00Z"
            )
        ]

        result = format_materials_for_prompt(
            materials=materials,
            context="interview"
        )

        assert "mat_nodesc" in result
        assert "no-desc.png" in result
        # Should not crash, should handle None gracefully


class TestValidateTokenBudget:
    """Test token budget validation."""

    def test_validate_small_section_passes(self):
        """Test small materials section passes budget."""
        short_section = "## Materiais\n\n- mat_123 - test.png (image/png, 1.0 MB)"

        result = validate_token_budget(short_section)

        assert result["is_valid"] is True
        assert result["budget"] == 2000
        assert result["estimated_tokens"] < 2000
        assert result["exceeded_by"] is None

    def test_validate_large_section_fails(self):
        """Test very large section exceeds budget."""
        # Create a section with many materials (>2000 tokens)
        large_section = "## Materiais\n\n" + "\n".join([
            f"- mat_{i:03d} - material-{i}.png (image/png, 1.0 MB)\n  Descrição: Este é um material de teste com uma descrição relativamente longa para consumir tokens"
            for i in range(100)  # 100 materials with long descriptions
        ])

        result = validate_token_budget(large_section)

        # Should exceed budget
        assert result["is_valid"] is False
        assert result["estimated_tokens"] > 2000
        assert result["exceeded_by"] > 0


# This module needs to be implemented for tests to pass
if __name__ == "__main__":
    import sys

    # This test file verifies the tests FAIL before implementation
    print("❌ EXPECTED TO FAIL - materials_context module not yet implemented")
    print("Run pytest to see actual failures")
    sys.exit(1)

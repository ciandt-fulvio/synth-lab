"""
Unit tests for PR-FAQ prompts with materials.

Tests that the PR-FAQ system prompt correctly includes materials sections
when materials are provided.

References:
    - contracts/materials_context.yaml: Material formatting contract
    - src/synth_lab/services/research_prfaq/prompts.py: Prompt generation
"""

import pytest
from unittest.mock import Mock


class TestPRFAQPromptWithMaterials:
    """Test PR-FAQ prompt formatting with materials."""

    @pytest.fixture
    def sample_materials(self):
        """Create sample materials for testing."""
        materials = []

        # Material 1: Design wireframe
        mat1 = Mock()
        mat1.id = "mat_abc123"
        mat1.experiment_id = "exp_123"
        mat1.file_type = "image"
        mat1.file_url = "s3://bucket/wireframe.png"
        mat1.file_name = "checkout-wireframe.png"
        mat1.file_size = 2_300_000
        mat1.mime_type = "image/png"
        mat1.material_type = "design"
        mat1.description = "Wireframe do fluxo de checkout"
        mat1.display_order = 0

        # Material 2: Product spec PDF
        mat2 = Mock()
        mat2.id = "mat_def456"
        mat2.experiment_id = "exp_123"
        mat2.file_type = "document"
        mat2.file_url = "s3://bucket/spec.pdf"
        mat2.file_name = "product-spec.pdf"
        mat2.file_size = 500_000
        mat2.mime_type = "application/pdf"
        mat2.material_type = "specification"
        mat2.description = "Especificação técnica do produto"
        mat2.display_order = 1

        materials.extend([mat1, mat2])
        return materials

    def test_prompt_with_materials_includes_section(self, sample_materials):
        """Test that system prompt includes materials section when provided."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=sample_materials)

        # Should include materials header
        assert "Materiais Anexados" in result or "Materiais" in result

        # Should include material IDs
        assert "mat_abc123" in result
        assert "mat_def456" in result

        # Should include file names
        assert "checkout-wireframe.png" in result
        assert "product-spec.pdf" in result

    def test_prompt_with_materials_includes_reference_instructions(self, sample_materials):
        """Test that prompt includes instructions for referencing materials in PR-FAQ."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=sample_materials)

        # Should mention how to reference materials
        # Note: Portuguese plural is "materiais" not "materials"
        assert "materiais" in result.lower() or "anexado" in result.lower()

        # Should explain citation format
        assert "referência" in result.lower() or "cit" in result.lower()

    def test_prompt_without_materials_has_no_section(self):
        """Test that system prompt without materials has no materials section."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=None)

        # Should NOT include materials section
        assert "Materiais Anexados" not in result
        assert "mat_" not in result

    def test_prompt_preserves_existing_structure(self, sample_materials):
        """Test that materials section doesn't break existing prompt structure."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=sample_materials)

        # Should still have all required sections from original prompt
        assert "Working Backwards" in result
        assert "Amazon" in result
        assert "Press Release" in result or "PRESS RELEASE" in result
        assert "FAQ" in result
        assert "Markdown" in result

    def test_prompt_with_empty_materials_list(self):
        """Test that empty materials list is handled gracefully."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=[])

        # Empty list should be treated as no materials
        assert "Materiais Anexados" not in result
        assert "mat_" not in result


# This module needs implementation
if __name__ == "__main__":
    import sys

    print("❌ EXPECTED TO FAIL - get_system_prompt() not yet updated for materials")
    print("Run pytest to see actual test failures")
    sys.exit(1)

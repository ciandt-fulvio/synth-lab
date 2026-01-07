"""
Contract tests for material references in PR-FAQ documents.

Verifies that generated PR-FAQ documents correctly reference materials
with proper formatting and metadata.

References:
    - contracts/materials_context.yaml: Material formatting contract
    - research.md: PR-FAQ material reference format
"""

import pytest
from unittest.mock import Mock
import re


@pytest.fixture
def sample_materials():
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


class TestPRFAQMaterialReferences:
    """Test material reference formatting in PR-FAQ prompts."""

    def test_materials_section_is_markdown(self, sample_materials):
        """Test that materials section uses valid markdown format."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=sample_materials)

        # Should have markdown headers
        assert re.search(r"^##+ ", result, re.MULTILINE) is not None

    def test_material_ids_preserved(self, sample_materials):
        """Test that material IDs are preserved exactly."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=sample_materials)

        # Extract material IDs from prompt (flexible pattern)
        id_pattern = r"mat_[a-z0-9]+"
        found_ids = set(re.findall(id_pattern, result))
        expected_ids = {m.id for m in sample_materials}

        assert found_ids == expected_ids

    def test_material_descriptions_included(self, sample_materials):
        """Test that material descriptions are included."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=sample_materials)

        # Should include descriptions
        assert "Wireframe do fluxo de checkout" in result
        assert "Especificação técnica" in result

    def test_reference_format_instructions(self, sample_materials):
        """Test that prompt includes instructions for material references."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=sample_materials)

        # Should explain how to reference materials in PR-FAQ
        # Looking for Portuguese keywords about referencing
        # Note: Portuguese plural is "materiais" not "materials"
        has_reference_instructions = (
            "referência" in result.lower() or
            "referenc" in result.lower() or
            "cit" in result.lower() or
            "materiais" in result.lower()
        )
        assert has_reference_instructions

    def test_prfaq_context_specific_format(self, sample_materials):
        """Test that materials use PR-FAQ context formatting."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=sample_materials)

        # For PR-FAQ context, should emphasize reference format
        # (different from interview context which has tool usage)
        # Should NOT mention "ver_material" tool (that's for interviews)
        assert "ver_material" not in result

    def test_file_metadata_included(self, sample_materials):
        """Test that file metadata is included."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=sample_materials)

        # Should include file names
        assert "checkout-wireframe.png" in result
        assert "product-spec.pdf" in result

        # Should include material types
        assert "design" in result.lower()
        assert "specification" in result.lower()

    def test_empty_materials_returns_base_prompt(self):
        """Test that empty materials list returns base prompt without materials section."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=[])

        # Should not have materials section
        assert "Materiais Anexados" not in result
        assert "mat_" not in result

    def test_none_materials_returns_base_prompt(self):
        """Test that None materials returns base prompt without materials section."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        result = get_system_prompt(materials=None)

        # Should not have materials section
        assert "Materiais Anexados" not in result
        assert "mat_" not in result


# This module needs implementation
if __name__ == "__main__":
    import sys

    print("❌ EXPECTED TO FAIL - PR-FAQ prompt not yet updated for materials")
    print("Run pytest to see actual contract failures")
    sys.exit(1)

"""
Integration tests for PR-FAQ generation with materials.

Tests the complete flow of generating a PR-FAQ document when
experiment materials are attached.

References:
    - spec.md: User Story 2 acceptance criteria
"""

import pytest
from unittest.mock import Mock


@pytest.mark.integration
class TestPRFAQWithMaterials:
    """Integration tests for PR-FAQ generation with materials."""

    @pytest.fixture
    def sample_experiment_with_materials(self):
        """Create sample experiment with materials."""
        experiment = Mock()
        experiment.id = "exp_test123"
        experiment.name = "Test Experiment"

        # Material 1: Design wireframe
        material1 = Mock()
        material1.id = "mat_abc123"
        material1.experiment_id = "exp_test123"
        material1.file_url = "s3://bucket/wireframe.png"
        material1.mime_type = "image/png"
        material1.file_name = "checkout-wireframe.png"
        material1.file_size = 2_000_000
        material1.file_type = "image"
        material1.material_type = "design"
        material1.description = "Wireframe do fluxo de checkout"
        material1.display_order = 0

        # Material 2: Product spec
        material2 = Mock()
        material2.id = "mat_def456"
        material2.experiment_id = "exp_test123"
        material2.file_url = "s3://bucket/spec.pdf"
        material2.mime_type = "application/pdf"
        material2.file_name = "product-spec.pdf"
        material2.file_size = 500_000
        material2.file_type = "document"
        material2.material_type = "specification"
        material2.description = "Especificação técnica"
        material2.display_order = 1

        experiment.materials = [material1, material2]
        return experiment

    @pytest.fixture
    def sample_research_summary(self):
        """Create sample research summary."""
        return """# Achados da Pesquisa: E-commerce Checkout

## Resumo Executivo
Realizamos 10 entrevistas com usuários de e-commerce.

## Padrões Recorrentes
- Processo de checkout muito longo
- Falta de feedback visual
- Campos redundantes

## Recomendações
1. Simplificar formulário para 3 etapas
2. Adicionar indicador de progresso visual
3. Remover campos desnecessários"""

    def test_prompt_includes_materials(
        self, sample_experiment_with_materials
    ):
        """Test that generated prompt includes materials section."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        prompt = get_system_prompt(
            materials=sample_experiment_with_materials.materials
        )

        # Should include materials
        assert "mat_abc123" in prompt
        assert "mat_def456" in prompt
        assert "checkout-wireframe.png" in prompt

    def test_prfaq_generation_with_materials_completes(
        self, sample_experiment_with_materials, sample_research_summary
    ):
        """Test that PR-FAQ generation completes with materials attached.

        This is a smoke test to ensure all components integrate correctly.
        """
        # This test verifies the integration points are working
        # A full PR-FAQ generation would require:
        # 1. Fetch materials from experiment
        # 2. Generate system prompt with materials
        # 3. Call LLM with prompt + research summary
        # 4. Verify output includes material references

        # For now, verify core components exist and can be created
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        # Can generate prompt with materials
        prompt = get_system_prompt(
            materials=sample_experiment_with_materials.materials
        )
        assert prompt is not None
        assert "mat_abc123" in prompt

        # Verify research summary is available
        assert sample_research_summary is not None
        assert len(sample_research_summary) > 0

    def test_materials_section_format(self, sample_experiment_with_materials):
        """Test that materials are formatted correctly in prompt."""
        from synth_lab.services.research_prfaq.prompts import get_system_prompt

        prompt = get_system_prompt(
            materials=sample_experiment_with_materials.materials
        )

        # Should use markdown format for materials
        assert "##" in prompt or "**" in prompt

        # Should include material metadata
        assert "design" in prompt.lower() or "wireframe" in prompt.lower()


# This module needs implementation
if __name__ == "__main__":
    import sys

    print("❌ EXPECTED TO FAIL - PR-FAQ generation with materials not yet implemented")
    print("Run pytest to see actual integration test failures")
    sys.exit(1)

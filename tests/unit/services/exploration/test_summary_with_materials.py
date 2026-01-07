"""
Unit tests for exploration summary generation with materials.

Tests that summary prompts correctly include materials sections
when materials are provided.

References:
    - spec.md: User Story 4 acceptance criteria
    - services/materials_context.py: Material formatting module
"""

import pytest
from unittest.mock import Mock


class TestSummaryWithMaterials:
    """Test summary prompt formatting with materials."""

    @pytest.fixture
    def sample_materials(self):
        """Create sample materials for testing."""
        materials = []

        # Material 1: Design wireframe
        mat1 = Mock()
        mat1.id = "mat_abc123"
        mat1.experiment_id = "exp_abcd1234"
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
        mat2.experiment_id = "exp_abcd1234"
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

    @pytest.fixture
    def sample_exploration(self):
        """Create sample exploration."""
        from synth_lab.domain.entities.exploration import (
            Exploration,
            ExplorationStatus,
            Goal,
        )

        return Exploration(
            experiment_id="exp_abcd1234",
            baseline_analysis_id="ana_abcd1234",
            status=ExplorationStatus.GOAL_ACHIEVED,
            goal=Goal(value=0.70),
            total_nodes=5,
        )

    @pytest.fixture
    def sample_winning_path(self):
        """Create sample winning path."""
        from synth_lab.domain.entities.scenario_node import (
            ScenarioNode,
            ScorecardParams,
            SimulationResults,
        )

        # Root node
        root = ScenarioNode(
            exploration_id="expl_abcd1234",
            depth=0,
            scorecard_params=ScorecardParams(
                complexity=0.45,
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.40,
            ),
            simulation_results=SimulationResults(
                success_rate=0.50, fail_rate=0.30, did_not_try_rate=0.20
            ),
        )

        # Final node
        final = ScenarioNode(
            exploration_id="expl_abcd1234",
            depth=1,
            parent_id=root.id,
            action_applied="Simplificar formulário",
            action_category="ux_interface",
            rationale="Reduz complexidade",
            scorecard_params=ScorecardParams(
                complexity=0.40,
                initial_effort=0.30,
                perceived_risk=0.20,
                time_to_value=0.35,
            ),
            simulation_results=SimulationResults(
                success_rate=0.72, fail_rate=0.18, did_not_try_rate=0.10
            ),
        )

        return [root, final]

    def test_prompt_with_materials_includes_section(
        self, sample_exploration, sample_winning_path, sample_materials
    ):
        """Test that prompt includes materials section when provided."""
        from synth_lab.services.exploration_summary_generator_service import (
            ExplorationSummaryGeneratorService,
        )

        service = ExplorationSummaryGeneratorService()
        prompt = service._build_prompt(
            sample_exploration,
            sample_winning_path,
            "Test Experiment",
            materials=sample_materials,
        )

        # Should include materials header
        assert "Materiais" in prompt or "materiais" in prompt

        # Should include material IDs
        assert "mat_abc123" in prompt
        assert "mat_def456" in prompt

        # Should include file names
        assert "checkout-wireframe.png" in prompt
        assert "product-spec.pdf" in prompt

    def test_prompt_without_materials_has_no_section(
        self, sample_exploration, sample_winning_path
    ):
        """Test that prompt without materials has no materials section."""
        from synth_lab.services.exploration_summary_generator_service import (
            ExplorationSummaryGeneratorService,
        )

        service = ExplorationSummaryGeneratorService()
        prompt = service._build_prompt(
            sample_exploration, sample_winning_path, "Test Experiment", materials=None
        )

        # Should NOT include materials section
        assert "## Materiais" not in prompt
        assert "mat_" not in prompt

    def test_prompt_with_empty_materials_list(
        self, sample_exploration, sample_winning_path
    ):
        """Test that empty materials list is handled gracefully."""
        from synth_lab.services.exploration_summary_generator_service import (
            ExplorationSummaryGeneratorService,
        )

        service = ExplorationSummaryGeneratorService()
        prompt = service._build_prompt(
            sample_exploration, sample_winning_path, "Test Experiment", materials=[]
        )

        # Empty list should be treated as no materials
        assert "## Materiais" not in prompt
        assert "mat_" not in prompt

    def test_prompt_preserves_existing_structure(
        self, sample_exploration, sample_winning_path, sample_materials
    ):
        """Test that materials section doesn't break existing prompt structure."""
        from synth_lab.services.exploration_summary_generator_service import (
            ExplorationSummaryGeneratorService,
        )

        service = ExplorationSummaryGeneratorService()
        prompt = service._build_prompt(
            sample_exploration,
            sample_winning_path,
            "Test Experiment",
            materials=sample_materials,
        )

        # Should still have all required sections
        assert "## CONTEXTO DA EXPLORAÇÃO" in prompt or "CONTEXTO DA EXPLORAÇÃO" in prompt
        assert "## COMPARAÇÃO DE SCORECARD" in prompt or "COMPARAÇÃO DE SCORECARD" in prompt
        assert "## MELHORIAS APLICADAS" in prompt or "MELHORIAS APLICADAS" in prompt
        assert "## TAREFA" in prompt or "TAREFA" in prompt

    def test_materials_section_format(
        self, sample_exploration, sample_winning_path, sample_materials
    ):
        """Test that materials are formatted correctly in prompt."""
        from synth_lab.services.exploration_summary_generator_service import (
            ExplorationSummaryGeneratorService,
        )

        service = ExplorationSummaryGeneratorService()
        prompt = service._build_prompt(
            sample_exploration,
            sample_winning_path,
            "Test Experiment",
            materials=sample_materials,
        )

        # Should use markdown format for materials
        assert "##" in prompt or "**" in prompt

        # Should include material metadata
        assert "design" in prompt.lower() or "wireframe" in prompt.lower()


# This module needs implementation
if __name__ == "__main__":
    import sys

    print("❌ EXPECTED TO FAIL - Summary generator not yet updated for materials")
    print("Run pytest to see actual test failures")
    sys.exit(1)

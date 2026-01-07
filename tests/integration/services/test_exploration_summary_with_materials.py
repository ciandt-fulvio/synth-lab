"""
Integration tests for exploration summary generation with materials.

Tests the complete flow of generating exploration summaries when
experiment materials are attached.

References:
    - spec.md: User Story 4 acceptance criteria
"""

import pytest
from unittest.mock import Mock


@pytest.mark.integration
class TestExplorationSummaryWithMaterials:
    """Integration tests for exploration summary with materials."""

    @pytest.fixture
    def sample_exploration(self):
        """Create sample exploration."""
        from synth_lab.domain.entities.exploration import (
            Exploration,
            ExplorationStatus,
            Goal,
        )

        return Exploration(
            id="expl_abcd1234",
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

    @pytest.fixture
    def sample_materials(self):
        """Create sample materials."""
        materials = []

        # Material 1: Design wireframe
        mat1 = Mock()
        mat1.id = "mat_abc123"
        mat1.experiment_id = "exp_abcd1234"
        mat1.file_url = "s3://bucket/wireframe.png"
        mat1.mime_type = "image/png"
        mat1.file_name = "checkout-wireframe.png"
        mat1.file_size = 2_000_000
        mat1.file_type = "image"
        mat1.material_type = "design"
        mat1.description = "Wireframe do fluxo de checkout"
        mat1.display_order = 0

        # Material 2: Product spec
        mat2 = Mock()
        mat2.id = "mat_def456"
        mat2.experiment_id = "exp_abcd1234"
        mat2.file_url = "s3://bucket/spec.pdf"
        mat2.mime_type = "application/pdf"
        mat2.file_name = "product-spec.pdf"
        mat2.file_size = 500_000
        mat2.file_type = "document"
        mat2.material_type = "specification"
        mat2.description = "Especificação técnica"
        mat2.display_order = 1

        materials.extend([mat1, mat2])
        return materials

    def test_prompt_includes_materials(
        self, sample_exploration, sample_winning_path, sample_materials
    ):
        """Test that generated prompt includes materials section."""
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

        # Should include materials
        assert "mat_abc123" in prompt
        assert "mat_def456" in prompt
        assert "checkout-wireframe.png" in prompt

    def test_summary_generation_with_materials_completes(
        self, sample_exploration, sample_winning_path, sample_materials
    ):
        """Test that summary generation completes with materials attached.

        This is a smoke test to ensure all components integrate correctly.
        """
        # This test verifies the integration points are working
        # A full generation would require:
        # 1. Fetch materials from experiment
        # 2. Generate prompt with materials
        # 3. Call LLM with prompt
        # 4. Verify output includes material-informed summaries

        # For now, verify core components exist and can be created
        from synth_lab.services.exploration_summary_generator_service import (
            ExplorationSummaryGeneratorService,
        )

        service = ExplorationSummaryGeneratorService()

        # Can generate prompt with materials
        prompt = service._build_prompt(
            sample_exploration,
            sample_winning_path,
            "Test Experiment",
            materials=sample_materials,
        )
        assert prompt is not None
        assert "mat_abc123" in prompt

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

    print(
        "❌ EXPECTED TO FAIL - summary generation with materials not yet implemented"
    )
    print("Run pytest to see actual integration test failures")
    sys.exit(1)

"""
Integration tests for exploration with materials.

Tests the complete flow of generating action proposals when
experiment materials are attached.

References:
    - spec.md: User Story 3 acceptance criteria
"""

import pytest
from unittest.mock import Mock


@pytest.mark.integration
class TestExplorationWithMaterials:
    """Integration tests for exploration with materials."""

    @pytest.fixture
    def sample_experiment_with_materials(self):
        """Create sample experiment with materials."""
        from synth_lab.domain.entities.experiment import (
            Experiment,
            ScorecardData,
            ScorecardDimension,
        )

        experiment = Mock()
        experiment.id = "exp_test123"
        experiment.name = "Test Experiment"
        experiment.hypothesis = "Test hypothesis"
        experiment.scorecard_data = ScorecardData(
            feature_name="Test Feature",
            description_text="Test description",
            complexity=ScorecardDimension(score=0.45),
            initial_effort=ScorecardDimension(score=0.30),
            perceived_risk=ScorecardDimension(score=0.25),
            time_to_value=ScorecardDimension(score=0.40),
        )

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
    def sample_node(self):
        """Create sample scenario node."""
        from synth_lab.domain.entities.scenario_node import (
            ScenarioNode,
            ScorecardParams,
            SimulationResults,
        )

        # Root node with valid ID pattern (expl_[8 hex chars])
        return ScenarioNode(
            exploration_id="expl_abcd1234",
            depth=0,
            scorecard_params=ScorecardParams(
                complexity=0.45,
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.40,
            ),
            simulation_results=SimulationResults(
                success_rate=0.25, fail_rate=0.45, did_not_try_rate=0.30
            ),
        )

    def test_prompt_includes_materials(
        self, sample_experiment_with_materials, sample_node
    ):
        """Test that generated prompt includes materials section."""
        from unittest.mock import MagicMock

        from synth_lab.services.exploration.action_proposal_service import (
            ActionProposalService,
        )

        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get_path_to_node.return_value = [sample_node]

        service = ActionProposalService(repository=mock_repo)
        prompt = service._build_prompt(
            sample_node,
            sample_experiment_with_materials,
            4,
            materials=sample_experiment_with_materials.materials,
        )

        # Should include materials
        assert "mat_abc123" in prompt
        assert "mat_def456" in prompt
        assert "checkout-wireframe.png" in prompt

    def test_action_proposal_generation_with_materials_completes(
        self, sample_experiment_with_materials, sample_node
    ):
        """Test that action proposal generation completes with materials attached.

        This is a smoke test to ensure all components integrate correctly.
        """
        # This test verifies the integration points are working
        # A full generation would require:
        # 1. Fetch materials from experiment
        # 2. Generate prompt with materials
        # 3. Call LLM with prompt
        # 4. Verify output includes material-informed proposals

        # For now, verify core components exist and can be created
        from unittest.mock import MagicMock

        from synth_lab.services.exploration.action_proposal_service import (
            ActionProposalService,
        )

        mock_repo = MagicMock()
        mock_repo.get_path_to_node.return_value = [sample_node]

        service = ActionProposalService(repository=mock_repo)

        # Can generate prompt with materials
        prompt = service._build_prompt(
            sample_node,
            sample_experiment_with_materials,
            4,
            materials=sample_experiment_with_materials.materials,
        )
        assert prompt is not None
        assert "mat_abc123" in prompt

    def test_materials_section_format(
        self, sample_experiment_with_materials, sample_node
    ):
        """Test that materials are formatted correctly in prompt."""
        from unittest.mock import MagicMock

        from synth_lab.services.exploration.action_proposal_service import (
            ActionProposalService,
        )

        mock_repo = MagicMock()
        mock_repo.get_path_to_node.return_value = [sample_node]

        service = ActionProposalService(repository=mock_repo)
        prompt = service._build_prompt(
            sample_node,
            sample_experiment_with_materials,
            4,
            materials=sample_experiment_with_materials.materials,
        )

        # Should use markdown format for materials
        assert "##" in prompt or "**" in prompt

        # Should include material metadata
        assert "design" in prompt.lower() or "wireframe" in prompt.lower()


# This module needs implementation
if __name__ == "__main__":
    import sys

    print(
        "❌ EXPECTED TO FAIL - exploration generation with materials not yet implemented"
    )
    print("Run pytest to see actual integration test failures")
    sys.exit(1)

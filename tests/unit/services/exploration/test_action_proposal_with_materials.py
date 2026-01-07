"""
Unit tests for action proposal generation with materials.

Tests that action proposal prompts correctly include materials sections
when materials are provided.

References:
    - spec.md: User Story 3 acceptance criteria
    - services/materials_context.py: Material formatting module
"""

import pytest
from unittest.mock import Mock


class TestActionProposalWithMaterials:
    """Test action proposal prompt formatting with materials."""

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

    @pytest.fixture
    def sample_node(self):
        """Create sample scenario node."""
        from synth_lab.domain.entities.scenario_node import (
            ScenarioNode,
            ScorecardParams,
            SimulationResults,
        )

        # Root node (depth=0) doesn't require parent_id
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

    @pytest.fixture
    def sample_experiment(self):
        """Create sample experiment."""
        from synth_lab.domain.entities.experiment import (
            Experiment,
            ScorecardData,
            ScorecardDimension,
        )

        return Experiment(
            id="exp_123",
            name="Test Experiment",
            hypothesis="Test hypothesis",
            scorecard_data=ScorecardData(
                feature_name="Test Feature",
                description_text="Test description",
                complexity=ScorecardDimension(score=0.45),
                initial_effort=ScorecardDimension(score=0.30),
                perceived_risk=ScorecardDimension(score=0.25),
                time_to_value=ScorecardDimension(score=0.40),
            ),
        )

    def test_prompt_with_materials_includes_section(
        self, sample_node, sample_experiment, sample_materials
    ):
        """Test that prompt includes materials section when provided."""
        from unittest.mock import MagicMock

        from synth_lab.services.exploration.action_proposal_service import (
            ActionProposalService,
        )

        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get_path_to_node.return_value = [sample_node]

        service = ActionProposalService(repository=mock_repo)
        prompt = service._build_prompt(
            sample_node, sample_experiment, 4, materials=sample_materials
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
        self, sample_node, sample_experiment
    ):
        """Test that prompt without materials has no materials section."""
        from unittest.mock import MagicMock

        from synth_lab.services.exploration.action_proposal_service import (
            ActionProposalService,
        )

        mock_repo = MagicMock()
        mock_repo.get_path_to_node.return_value = [sample_node]

        service = ActionProposalService(repository=mock_repo)
        prompt = service._build_prompt(sample_node, sample_experiment, 4, materials=None)

        # Should NOT include materials section
        # (unless accidentally in experiment name or description)
        # Look for the specific header format
        assert "## Materiais" not in prompt
        assert "mat_" not in prompt

    def test_prompt_with_empty_materials_list(
        self, sample_node, sample_experiment
    ):
        """Test that empty materials list is handled gracefully."""
        from unittest.mock import MagicMock

        from synth_lab.services.exploration.action_proposal_service import (
            ActionProposalService,
        )

        mock_repo = MagicMock()
        mock_repo.get_path_to_node.return_value = [sample_node]

        service = ActionProposalService(repository=mock_repo)
        prompt = service._build_prompt(sample_node, sample_experiment, 4, materials=[])

        # Empty list should be treated as no materials
        assert "## Materiais" not in prompt
        assert "mat_" not in prompt

    def test_prompt_preserves_existing_structure(
        self, sample_node, sample_experiment, sample_materials
    ):
        """Test that materials section doesn't break existing prompt structure."""
        from unittest.mock import MagicMock

        from synth_lab.services.exploration.action_proposal_service import (
            ActionProposalService,
        )

        mock_repo = MagicMock()
        mock_repo.get_path_to_node.return_value = [sample_node]

        service = ActionProposalService(repository=mock_repo)
        prompt = service._build_prompt(
            sample_node, sample_experiment, 4, materials=sample_materials
        )

        # Should still have all required sections
        assert "## Contexto do Experimento" in prompt
        assert "## Parametros Atuais do Scorecard" in prompt
        assert "## Resultados Observados" in prompt
        assert "## Instrucoes" in prompt
        assert "Catalogo de Acoes" in prompt

    def test_materials_section_format(
        self, sample_node, sample_experiment, sample_materials
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
            sample_node, sample_experiment, 4, materials=sample_materials
        )

        # Should use markdown format for materials
        assert "##" in prompt or "**" in prompt

        # Should include material metadata
        assert "design" in prompt.lower() or "wireframe" in prompt.lower()


# This module needs implementation
if __name__ == "__main__":
    import sys

    print("❌ EXPECTED TO FAIL - ActionProposalService not yet updated for materials")
    print("Run pytest to see actual test failures")
    sys.exit(1)

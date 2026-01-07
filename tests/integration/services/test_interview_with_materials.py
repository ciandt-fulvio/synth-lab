"""
End-to-end integration test for interviews with materials.

Tests the complete flow of conducting an interview where the interviewee
agent can load and reference experiment materials.

References:
    - spec.md: User Story 1 acceptance criteria
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


@pytest.mark.integration
class TestInterviewWithMaterials:
    """End-to-end tests for interview with materials."""

    @pytest.fixture
    def sample_experiment_with_materials(self):
        """Create sample experiment with materials."""
        experiment = Mock()
        experiment.id = "exp_test123"
        experiment.name = "Test Experiment"

        # Materials
        material1 = Mock()
        material1.id = "mat_abc123"
        material1.experiment_id = "exp_test123"
        material1.file_url = "s3://bucket/wireframe.png"
        material1.mime_type = "image/png"
        material1.file_name = "wireframe.png"
        material1.file_size = 2_000_000
        material1.file_type = "image"
        material1.material_type = "design"
        material1.description = "Wireframe do checkout"
        material1.display_order = 0

        experiment.materials = [material1]
        return experiment

    def test_interviewer_agent_has_materials_in_prompt(
        self, sample_experiment_with_materials
    ):
        """Test interviewer agent instructions include materials."""
        from synth_lab.services.research_agentic.instructions import (
            format_interviewer_instructions
        )

        instructions = format_interviewer_instructions(
            topic_guide="Test research topic",
            materials=sample_experiment_with_materials.materials,
            max_turns=5,
            conversation_history="",
            additional_context=""
        )

        # Should include materials section
        assert "mat_abc123" in instructions
        assert "wireframe.png" in instructions
        assert "ver_material" in instructions

    def test_interviewee_agent_has_materials_in_prompt(
        self, sample_experiment_with_materials
    ):
        """Test interviewee agent instructions include materials."""
        from synth_lab.services.research_agentic.instructions import (
            format_interviewee_instructions
        )

        synth = {
            "nome": "Test User",
            "demografia": {
                "idade": 30,
                "identidade_genero": "Masculino",
                "ocupacao": "Developer",
                "escolaridade": "Superior",
                "localizacao": {"cidade": "São Paulo", "estado": "SP"}
            },
            "descricao": "Tech-savvy person",
            "psicografia": {
                "interesses": ["Technology"],
                "contrato_cognitivo": {
                    "tipo": "Direct responses",
                    "perfil_cognitivo": "Direct",
                    "regras": [],
                    "efeito_esperado": ""
                }
            }
        }
        instructions = format_interviewee_instructions(
            synth=synth,
            conversation_history="",
            initial_context="",
            materials=sample_experiment_with_materials.materials
        )

        # Should include materials
        assert "mat_abc123" in instructions
        assert "wireframe.png" in instructions

    def test_interviewee_agent_can_call_materials_tool(
        self, sample_experiment_with_materials
    ):
        """Test interviewee agent can successfully call ver_material tool."""
        from synth_lab.services.research_agentic.tools import _load_material_content

        # Mock dependencies
        mock_repo = Mock()
        mock_repo.get_by_id.return_value = sample_experiment_with_materials.materials[0]

        mock_s3 = Mock()
        mock_s3.download_from_s3.return_value = b"fake_image_data"

        # Call the core function directly
        result = _load_material_content(
            material_id="mat_abc123",
            experiment_id="exp_test123",
            material_repository=mock_repo,
            s3_client=mock_s3
        )

        # Should return data URI
        assert result.startswith("data:image/png;base64,")
        assert mock_repo.get_by_id.called
        assert mock_s3.download_from_s3.called

    def test_interview_with_materials_completes_successfully(
        self, sample_experiment_with_materials
    ):
        """Test complete interview flow with materials.

        This is a smoke test to ensure all components integrate correctly.
        """
        # This test verifies the integration points are working
        # A full interview simulation would require:
        # 1. Create interviewer with materials tool
        # 2. Create interviewee with materials tool
        # 3. Run interview turns
        # 4. Verify materials are referenced in responses

        # For now, verify core components exist and can be created
        from synth_lab.services.research_agentic.tools import create_materials_tool
        from synth_lab.services.research_agentic.instructions import (
            format_interviewer_instructions,
            format_interviewee_instructions,
        )

        # Can create tool
        mock_repo = Mock()
        mock_s3 = Mock()
        tool = create_materials_tool(
            experiment_id="exp_test123",
            material_repository=mock_repo,
            s3_client=mock_s3
        )
        assert tool is not None

        # Can format instructions with materials
        interviewer_instructions = format_interviewer_instructions(
            topic_guide="Test",
            materials=sample_experiment_with_materials.materials,
            max_turns=5,
            conversation_history="",
            additional_context=""
        )
        assert "mat_abc123" in interviewer_instructions

        synth = {
            "nome": "Test",
            "demografia": {
                "idade": 30,
                "identidade_genero": "M",
                "ocupacao": "Dev",
                "escolaridade": "Superior",
                "localizacao": {"cidade": "SP", "estado": "SP"}
            },
            "descricao": "Test",
            "psicografia": {
                "interesses": ["Tech"],
                "contrato_cognitivo": {
                    "tipo": "Direct",
                    "perfil_cognitivo": "Direct",
                    "regras": [],
                    "efeito_esperado": ""
                }
            }
        }
        interviewee_instructions = format_interviewee_instructions(
            synth=synth,
            conversation_history="",
            initial_context="",
            materials=sample_experiment_with_materials.materials
        )
        assert "mat_abc123" in interviewee_instructions


# This module needs full implementation
if __name__ == "__main__":
    import sys

    print("❌ EXPECTED TO FAIL - interview materials integration not yet implemented")
    print("Run pytest to see actual E2E test failures")
    sys.exit(1)

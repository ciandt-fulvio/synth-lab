"""
Contract tests for interview prompts with materials.

Verifies that interview prompts (interviewer and interviewee) correctly
include materials sections when materials are provided.

References:
    - contracts/materials_tool.yaml: Tool contract
    - contracts/materials_context.yaml: Prompt formatting contract
"""

import pytest
from unittest.mock import Mock
from synth_lab.services.research_agentic.instructions import (
    format_interviewer_instructions,
    format_interviewee_instructions,
)


@pytest.fixture
def sample_materials():
    """Create sample materials for testing."""
    materials = []

    # Material 1: Image
    mat1 = Mock()
    mat1.id = "mat_abc123"
    mat1.experiment_id = "exp_123"
    mat1.file_type = "image"
    mat1.file_url = "s3://bucket/wireframe.png"
    mat1.file_name = "wireframe-checkout.png"
    mat1.file_size = 2_300_000
    mat1.mime_type = "image/png"
    mat1.material_type = "design"
    mat1.description = "Wireframe do fluxo de checkout"
    mat1.display_order = 0

    # Material 2: Video
    mat2 = Mock()
    mat2.id = "mat_def456"
    mat2.experiment_id = "exp_123"
    mat2.file_type = "video"
    mat2.file_url = "s3://bucket/demo.mp4"
    mat2.file_name = "prototype-demo.mp4"
    mat2.file_size = 15_000_000
    mat2.mime_type = "video/mp4"
    mat2.material_type = "prototype"
    mat2.description = "Vídeo demonstrando interação"
    mat2.display_order = 1

    materials.extend([mat1, mat2])
    return materials


class TestInterviewerPromptWithMaterials:
    """Test interviewer prompt formatting with materials."""

    def test_interviewer_prompt_includes_materials_section(self, sample_materials):
        """Test interviewer prompt includes materials section when materials provided."""
        result = format_interviewer_instructions(
            topic_guide="Test topic guide",
            materials=sample_materials,
            max_turns=10,
            conversation_history="",
            additional_context=""
        )

        # Should include materials header
        assert "Materiais Anexados" in result or "Materiais" in result

        # Should include material IDs
        assert "mat_abc123" in result
        assert "mat_def456" in result

        # Should include file names
        assert "wireframe-checkout.png" in result
        assert "prototype-demo.mp4" in result

    def test_interviewer_prompt_includes_tool_instructions(self, sample_materials):
        """Test interviewer prompt includes ver_material tool usage instructions."""
        result = format_interviewer_instructions(
            topic_guide="Test topic guide",
            materials=sample_materials,
            max_turns=10,
            conversation_history="",
            additional_context=""
        )

        # Should mention the tool
        assert "ver_material" in result

        # Should have usage instructions
        assert "como" in result.lower() or "when" in result.lower()

    def test_interviewer_prompt_without_materials_has_no_section(self):
        """Test interviewer prompt without materials has no materials section."""
        result = format_interviewer_instructions(
            topic_guide="Test topic guide",
            materials=None,  # No materials
            max_turns=10,
            conversation_history="",
            additional_context=""
        )

        # Should NOT include materials section
        assert "Materiais Anexados" not in result
        assert "ver_material" not in result

    def test_interviewer_prompt_preserves_existing_structure(self, sample_materials):
        """Test materials section doesn't break existing prompt structure."""
        result = format_interviewer_instructions(
            topic_guide="Test topic guide",
            materials=sample_materials,
            max_turns=10,
            conversation_history="Previous conversation",
            additional_context="Additional context"
        )

        # Should still have all required sections
        assert "Roteiro da Pesquisa" in result
        assert "Test topic guide" in result
        assert "Histórico da Conversa" in result
        assert "Previous conversation" in result
        assert "FORMATO DE RESPOSTA" in result


class TestIntervieweePromptWithMaterials:
    """Test interviewee prompt formatting with materials."""

    def test_interviewee_prompt_includes_materials_section(self, sample_materials):
        """Test interviewee prompt includes materials section when materials provided."""
        synth = {
            "nome": "João Silva",
            "demografia": {
                "idade": 35,
                "identidade_genero": "Masculino",
                "ocupacao": "Desenvolvedor",
                "escolaridade": "Superior completo",
                "localizacao": {"cidade": "São Paulo", "estado": "SP"}
            },
            "descricao": "Pessoa técnica",
            "psicografia": {
                "interesses": ["Tecnologia"],
                "contrato_cognitivo": {
                    "tipo": "Responde de forma direta",
                    "perfil_cognitivo": "Direto",
                    "regras": [],
                    "efeito_esperado": ""
                }
            }
        }
        result = format_interviewee_instructions(
            synth=synth,
            conversation_history="",
            initial_context="",
            materials=sample_materials
        )

        # Should include materials
        assert "mat_abc123" in result
        assert "mat_def456" in result

    def test_interviewee_prompt_includes_tool_access(self, sample_materials):
        """Test interviewee can access ver_material tool."""
        synth = {
            "nome": "João Silva",
            "demografia": {
                "idade": 35,
                "identidade_genero": "Masculino",
                "ocupacao": "Desenvolvedor",
                "escolaridade": "Superior completo",
                "localizacao": {"cidade": "São Paulo", "estado": "SP"}
            },
            "descricao": "Pessoa técnica",
            "psicografia": {
                "interesses": ["Tecnologia"],
                "contrato_cognitivo": {
                    "tipo": "Responde de forma direta",
                    "perfil_cognitivo": "Direto",
                    "regras": [],
                    "efeito_esperado": ""
                }
            }
        }
        result = format_interviewee_instructions(
            synth=synth,
            conversation_history="",
            initial_context="",
            materials=sample_materials
        )

        # Should mention tool availability
        assert "ver_material" in result

    def test_interviewee_prompt_without_materials_has_no_section(self):
        """Test interviewee prompt without materials has no materials section."""
        synth = {
            "nome": "João Silva",
            "demografia": {
                "idade": 35,
                "identidade_genero": "Masculino",
                "ocupacao": "Desenvolvedor",
                "escolaridade": "Superior completo",
                "localizacao": {"cidade": "São Paulo", "estado": "SP"}
            },
            "descricao": "Pessoa técnica",
            "psicografia": {
                "interesses": ["Tecnologia"],
                "contrato_cognitivo": {
                    "tipo": "Responde de forma direta",
                    "perfil_cognitivo": "Direto",
                    "regras": [],
                    "efeito_esperado": ""
                }
            }
        }
        result = format_interviewee_instructions(
            synth=synth,
            conversation_history="",
            initial_context="",
            materials=None
        )

        # Should NOT include materials
        assert "mat_" not in result
        assert "ver_material" not in result

    def test_interviewee_prompt_preserves_persona(self, sample_materials):
        """Test materials don't interfere with persona definition."""
        synth = {
            "nome": "João Silva",
            "demografia": {
                "idade": 35,
                "identidade_genero": "Masculino",
                "ocupacao": "Desenvolvedor",
                "escolaridade": "Superior completo",
                "localizacao": {"cidade": "São Paulo", "estado": "SP"}
            },
            "descricao": "Pessoa técnica",
            "psicografia": {
                "interesses": ["Tecnologia"],
                "contrato_cognitivo": {
                    "tipo": "Responde de forma direta",
                    "perfil_cognitivo": "Direto",
                    "regras": [],
                    "efeito_esperado": ""
                }
            }
        }
        result = format_interviewee_instructions(
            synth=synth,
            conversation_history="",
            initial_context="",
            materials=sample_materials
        )

        # Should still have persona info
        assert "João Silva" in result
        assert "35 anos" in result
        assert "Desenvolvedor" in result


# This module needs implementation
if __name__ == "__main__":
    import sys

    print("❌ EXPECTED TO FAIL - prompt formatting functions not yet updated for materials")
    print("Run pytest to see actual contract failures")
    sys.exit(1)

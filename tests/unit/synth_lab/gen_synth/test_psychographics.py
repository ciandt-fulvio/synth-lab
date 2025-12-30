"""Tests for psychographics module (v2.3.0 - big_five removed)."""

from synth_lab.gen_synth import psychographics


def test_generate_psychographics_structure(config_data):
    """Test that psychographics have correct structure."""
    psycho = psychographics.generate_psychographics(config_data)

    # v2.3.0: only interesses and contrato_cognitivo
    required_fields = [
        "interesses",
        "contrato_cognitivo",
    ]

    for field in required_fields:
        assert field in psycho

    # Verify removed fields are NOT present (v2.3.0)
    removed_fields = [
        "personalidade_big_five",
        "valores",
        "hobbies",
        "estilo_vida",
        "inclinacao_politica",
        "inclinacao_religiosa",
    ]
    for field in removed_fields:
        assert field not in psycho, f"Field {field} should not be in schema"


def test_generate_psychographics_interesses(config_data):
    """Test interesses generation."""
    psycho = psychographics.generate_psychographics(config_data)

    assert isinstance(psycho["interesses"], list)
    assert 1 <= len(psycho["interesses"]) <= 4  # 1-4 items
    # Should be unique
    assert len(psycho["interesses"]) == len(set(psycho["interesses"]))


def test_generate_psychographics_contrato_cognitivo(config_data):
    """Test contrato cognitivo generation."""
    psycho = psychographics.generate_psychographics(config_data)

    assert isinstance(psycho["contrato_cognitivo"], dict)
    assert "tipo" in psycho["contrato_cognitivo"]
    assert "perfil_cognitivo" in psycho["contrato_cognitivo"]
    assert "regras" in psycho["contrato_cognitivo"]
    assert "efeito_esperado" in psycho["contrato_cognitivo"]


def test_generate_psychographics_contrato_types(config_data):
    """Test contrato cognitivo type values."""
    valid_types = [
        "factual",
        "narrador",
        "desconfiado",
        "racionalizador",
        "impaciente",
        "esforçado_confuso",
    ]

    # Generate multiple to check variety
    for _ in range(10):
        psycho = psychographics.generate_psychographics(config_data)
        assert psycho["contrato_cognitivo"]["tipo"] in valid_types

"""Tests for synth_builder module."""

import pytest
from synth_lab.gen_synth import synth_builder


def test_assemble_synth_structure(config_data):
    """Test that assemble_synth returns complete structure."""
    synth = synth_builder.assemble_synth(config_data)

    # Check top-level fields
    required_fields = [
        "id",
        "nome",
        "arquetipo",
        "descricao",
        "link_photo",
        "created_at",
        "version",
        "demografia",
        "psicografia",
        "comportamento",
        "deficiencias",
        "capacidades_tecnologicas",
        "vieses",
    ]

    for field in required_fields:
        assert field in synth, f"Missing required field: {field}"


def test_assemble_synth_demographics(config_data):
    """Test demographics section is complete."""
    synth = synth_builder.assemble_synth(config_data)

    demo = synth["demografia"]
    required_demo_fields = [
        "idade",
        "genero_biologico",
        "identidade_genero",
        "raca_etnia",
        "localizacao",
        "escolaridade",
        "renda_mensal",
        "ocupacao",
        "estado_civil",
        "composicao_familiar",
    ]

    for field in required_demo_fields:
        assert field in demo


def test_assemble_synth_psychographics(config_data):
    """Test psychographics section is complete (v2.0.0)."""
    synth = synth_builder.assemble_synth(config_data)

    psycho = synth["psicografia"]
    required_psycho_fields = [
        "personalidade_big_five",
        "interesses",
        "inclinacao_politica",
        "inclinacao_religiosa",
    ]

    for field in required_psycho_fields:
        assert field in psycho

    # Verify removed fields are NOT present in v2.0.0
    removed_fields = ["valores", "hobbies", "estilo_vida"]
    for field in removed_fields:
        assert field not in psycho, f"Field {field} should not be in v2.0.0 schema"


def test_assemble_synth_behavior(config_data):
    """Test behavior section is complete (v2.0.0)."""
    synth = synth_builder.assemble_synth(config_data)

    behavior = synth["comportamento"]
    required_behavior_fields = [
        "habitos_consumo",
        "padroes_midia",
        "fonte_noticias",
        "lealdade_marca",
        "engajamento_redes_sociais",
    ]

    for field in required_behavior_fields:
        assert field in behavior

    # Verify removed fields are NOT present in v2.0.0
    removed_fields = ["uso_tecnologia", "comportamento_compra"]
    for field in removed_fields:
        assert field not in behavior, f"Field {field} should not be in v2.0.0 schema"


def test_assemble_synth_disabilities(config_data):
    """Test disabilities section is complete."""
    synth = synth_builder.assemble_synth(config_data)

    disabilities = synth["deficiencias"]
    required_disability_fields = ["visual", "auditiva", "motora", "cognitiva"]

    for field in required_disability_fields:
        assert field in disabilities
        assert "tipo" in disabilities[field]


def test_assemble_synth_tech_capabilities(config_data):
    """Test tech capabilities section is complete."""
    synth = synth_builder.assemble_synth(config_data)

    tech = synth["capacidades_tecnologicas"]
    required_tech_fields = [
        "alfabetizacao_digital",
        "dispositivos",
        "preferencias_acessibilidade",
        "velocidade_digitacao",
        "frequencia_internet",
        "familiaridade_plataformas",
    ]

    for field in required_tech_fields:
        assert field in tech


def test_assemble_synth_biases(config_data):
    """Test biases section is complete."""
    synth = synth_builder.assemble_synth(config_data)

    biases = synth["vieses"]
    required_bias_fields = [
        "aversao_perda",
        "desconto_hiperbolico",
        "suscetibilidade_chamariz",
        "ancoragem",
        "vies_confirmacao",
        "vies_status_quo",
        "sobrecarga_informacao",
    ]

    for field in required_bias_fields:
        assert field in biases
        assert isinstance(biases[field], int)
        assert 0 <= biases[field] <= 100


def test_assemble_synth_id_unique(config_data):
    """Test that each synth gets a unique ID."""
    synth1 = synth_builder.assemble_synth(config_data)
    synth2 = synth_builder.assemble_synth(config_data)

    assert synth1["id"] != synth2["id"]


def test_assemble_synth_timestamps(config_data):
    """Test that timestamp is valid ISO format."""
    synth = synth_builder.assemble_synth(config_data)

    # Check created_at is valid ISO timestamp
    from datetime import datetime

    try:
        datetime.fromisoformat(synth["created_at"].replace("Z", "+00:00"))
    except ValueError:
        pytest.fail("created_at is not valid ISO timestamp")


def test_assemble_synth_version(config_data):
    """Test that version is set correctly to v2.0.0."""
    synth = synth_builder.assemble_synth(config_data)

    assert "version" in synth
    assert isinstance(synth["version"], str)
    # Version should be v2.0.0 for simplified schema
    assert synth["version"] == "2.0.0", f"Expected version 2.0.0, got {synth['version']}"


def test_assemble_synth_link_photo(config_data):
    """Test that photo link is generated."""
    synth = synth_builder.assemble_synth(config_data)

    assert "link_photo" in synth
    assert isinstance(synth["link_photo"], str)
    assert synth["link_photo"].startswith("http")


def test_assemble_synth_arquetipo(config_data):
    """Test that arquetipo is generated and non-empty."""
    synth = synth_builder.assemble_synth(config_data)

    assert "arquetipo" in synth
    assert isinstance(synth["arquetipo"], str)
    assert len(synth["arquetipo"]) > 0


def test_assemble_synth_descricao(config_data):
    """Test that descricao is generated and non-empty."""
    synth = synth_builder.assemble_synth(config_data)

    assert "descricao" in synth
    assert isinstance(synth["descricao"], str)
    assert len(synth["descricao"]) > 0


def test_assemble_synth_validates(config_data):
    """Test that assembled synth passes validation."""
    from synth_lab.gen_synth import validation

    synth = synth_builder.assemble_synth(config_data)
    is_valid, errors = validation.validate_synth(synth)

    assert is_valid is True, f"Synth validation failed: {errors}"
    assert len(errors) == 0


def test_assemble_synth_multiple_valid(config_data):
    """Test that multiple generated synths are all valid."""
    from synth_lab.gen_synth import validation

    for _ in range(5):
        synth = synth_builder.assemble_synth(config_data)
        is_valid, errors = validation.validate_synth(synth)
        assert is_valid is True, f"Synth validation failed: {errors}"

"""Tests for synth_builder module (v2.3.0)."""

import pytest

from synth_lab.gen_synth import synth_builder


def test_assemble_synth_structure(config_data):
    """Test that assemble_synth returns complete structure."""
    synth = synth_builder.assemble_synth(config_data)

    # Check top-level fields (v2.3.0 - capacidades_tecnologicas removed, observables added)
    required_fields = [
        "id",
        "nome",
        "descricao",
        "link_photo",
        "created_at",
        "version",
        "demografia",
        "psicografia",
        "deficiencias",
        "observables",
    ]

    for field in required_fields:
        assert field in synth, f"Missing required field: {field}"

    # Ensure removed fields are not present
    assert "capacidades_tecnologicas" not in synth


def test_assemble_synth_demographics(config_data):
    """Test demographics section is complete (v2.3.0 - identidade_genero removed)."""
    synth = synth_builder.assemble_synth(config_data)

    demo = synth["demografia"]
    required_demo_fields = [
        "idade",
        "genero_biologico",
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

    # Ensure identidade_genero is removed in v2.3.0
    assert "identidade_genero" not in demo


def test_assemble_synth_psychographics(config_data):
    """Test psychographics section (v2.3.0 - big_five removed)."""
    synth = synth_builder.assemble_synth(config_data)

    psycho = synth["psicografia"]
    required_psycho_fields = [
        "interesses",
        "contrato_cognitivo",
    ]

    for field in required_psycho_fields:
        assert field in psycho

    # Verify big_five is removed in v2.3.0
    assert "personalidade_big_five" not in psycho


def test_assemble_synth_disabilities(config_data):
    """Test disabilities section is complete."""
    synth = synth_builder.assemble_synth(config_data)

    disabilities = synth["deficiencias"]
    required_disability_fields = ["visual", "auditiva", "motora", "cognitiva"]

    for field in required_disability_fields:
        assert field in disabilities
        assert "tipo" in disabilities[field]


def test_assemble_synth_observables(config_data):
    """Test observables section has all 5 attributes (v2.3.0)."""
    synth = synth_builder.assemble_synth(config_data)

    obs = synth["observables"]
    required_obs_fields = [
        "digital_literacy",
        "similar_tool_experience",
        "motor_ability",
        "time_availability",
        "domain_expertise",
    ]

    for field in required_obs_fields:
        assert field in obs
        assert isinstance(obs[field], float)
        assert 0.0 <= obs[field] <= 1.0


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
    """Test that version is set correctly to v2.3.0."""
    synth = synth_builder.assemble_synth(config_data)

    assert "version" in synth
    assert isinstance(synth["version"], str)
    # Version should be v2.3.0 for schema with observables
    assert synth["version"] == "2.3.0", f"Expected version 2.3.0, got {synth['version']}"


def test_assemble_synth_link_photo(config_data):
    """Test that photo link is generated."""
    synth = synth_builder.assemble_synth(config_data)

    assert "link_photo" in synth
    assert isinstance(synth["link_photo"], str)
    assert synth["link_photo"].startswith("http")


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

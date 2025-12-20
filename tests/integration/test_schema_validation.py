"""
Integration tests for synth generation with current schema.

Tests verify that synths generated match the expected schema structure.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from synth_lab.gen_synth import synth_builder
from synth_lab.gen_synth.config import load_config_data


def test_generated_synth_no_removed_fields():
    """Test that newly generated synths do not contain removed fields."""
    # Load config and generate a synth
    config = load_config_data()
    synth = synth_builder.assemble_synth(config)

    # Verify removed fields are not present in psicografia
    assert "psicografia" in synth
    psico = synth["psicografia"]

    removed_fields_psico = [
        "valores",
        "hobbies",
        "estilo_vida",
        "inclinacao_politica",
        "inclinacao_religiosa",
    ]
    for field in removed_fields_psico:
        assert field not in psico, f"Generated synth should not have {field} field"


def test_generated_synth_has_retained_fields():
    """Test that generated synths have all essential fields."""
    config = load_config_data()
    synth = synth_builder.assemble_synth(config)

    # Verify essential psicografia fields
    psico = synth["psicografia"]
    assert "personalidade_big_five" in psico
    assert "interesses" in psico
    assert "contrato_cognitivo" in psico

    # Verify contrato_cognitivo structure
    contrato = psico["contrato_cognitivo"]
    assert "tipo" in contrato
    assert "perfil_cognitivo" in contrato
    assert "regras" in contrato
    assert "efeito_esperado" in contrato


def test_generated_synth_version_2_0_0():
    """Test that generated synths have version 2.0.0."""
    config = load_config_data()
    synth = synth_builder.assemble_synth(config)

    assert "version" in synth
    assert synth["version"] == "2.0.0", f"Generated synth should be v2.0.0, got {synth['version']}"


def test_multiple_synths_no_removed_fields():
    """Test that multiple generated synths are consistent (no removed fields)."""
    config = load_config_data()
    synths = [synth_builder.assemble_synth(config) for _ in range(5)]

    removed_fields_psico = [
        "valores",
        "hobbies",
        "estilo_vida",
        "inclinacao_politica",
        "inclinacao_religiosa",
    ]

    for i, synth in enumerate(synths):
        # Check psicografia
        for field in removed_fields_psico:
            assert field not in synth["psicografia"], \
                f"Synth {i+1} should not have psicografia.{field}"


def test_generated_synth_passes_schema_validation():
    """Test that generated synths pass schema validation."""
    from synth_lab.gen_synth.validation import validate_synth

    config = load_config_data()
    synth = synth_builder.assemble_synth(config)

    is_valid, errors = validate_synth(synth)

    assert is_valid is True, (
        f"Generated synth should pass schema validation. Errors: {errors}"
    )


def test_batch_generated_synths_all_pass_validation():
    """Test that a batch of generated synths all pass schema validation."""
    from synth_lab.gen_synth.validation import validate_synth

    config = load_config_data()
    synths = [synth_builder.assemble_synth(config) for _ in range(10)]

    failed_synths = []
    for i, synth in enumerate(synths):
        is_valid, errors = validate_synth(synth)
        if not is_valid:
            failed_synths.append((i, errors))

    assert len(failed_synths) == 0, (
        f"{len(failed_synths)} of 10 synths failed schema validation: {failed_synths}"
    )

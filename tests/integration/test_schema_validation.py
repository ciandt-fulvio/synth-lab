"""
Integration tests for synth generation with schema v2.0.0.

Tests verify that synths generated with v2.0.0 do not contain removed fields
and pass schema validation.
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

    assert "valores" not in psico, "Generated synth should not have valores field"
    assert "hobbies" not in psico, "Generated synth should not have hobbies field"
    assert "estilo_vida" not in psico, "Generated synth should not have estilo_vida field"

    # Verify removed fields are not present in comportamento
    assert "comportamento" in synth
    comp = synth["comportamento"]

    assert "uso_tecnologia" not in comp, "Generated synth should not have uso_tecnologia field"
    assert "comportamento_compra" not in comp, "Generated synth should not have comportamento_compra field"


def test_generated_synth_has_retained_fields():
    """Test that generated synths have all retained essential fields."""
    config = load_config_data()
    synth = synth_builder.assemble_synth(config)

    # Verify retained psicografia fields
    psico = synth["psicografia"]
    assert "personalidade_big_five" in psico
    assert "interesses" in psico
    assert "inclinacao_politica" in psico
    assert "inclinacao_religiosa" in psico

    # Verify retained comportamento fields
    comp = synth["comportamento"]
    assert "habitos_consumo" in comp
    assert "padroes_midia" in comp
    assert "lealdade_marca" in comp


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

    removed_fields_psico = ["valores", "hobbies", "estilo_vida"]
    removed_fields_comp = ["uso_tecnologia", "comportamento_compra"]

    for i, synth in enumerate(synths):
        # Check psicografia
        for field in removed_fields_psico:
            assert field not in synth["psicografia"], \
                f"Synth {i+1} should not have psicografia.{field}"

        # Check comportamento
        for field in removed_fields_comp:
            assert field not in synth["comportamento"], \
                f"Synth {i+1} should not have comportamento.{field}"


def test_generated_synth_passes_coherence_validation():
    """
    Integration test for end-to-end coherence validation (User Story 3).

    Tests that newly generated synths pass coherence validation,
    ensuring personality-bias consistency is maintained.
    """
    from synth_lab.gen_synth.validation import validate_synth_full

    config = load_config_data()
    synth = synth_builder.assemble_synth(config)

    # Validate with full validation (schema + coherence)
    is_valid, errors = validate_synth_full(synth, strict=False)

    assert is_valid is True, (
        f"Generated synth should pass coherence validation. Errors: {errors}"
    )


def test_manually_created_incoherent_synth_fails_validation():
    """
    Test that manually created synths with coherence violations fail validation.

    This verifies that the validation system can detect and report
    personality-bias inconsistencies.
    """
    from synth_lab.gen_synth.validation import validate_coherence

    # Create a synth with deliberate coherence violation
    incoherent_synth = {
        "psicografia": {
            "personalidade_big_five": {
                "abertura": 90,  # Very high openness
                "conscienciosidade": 50,
                "extroversao": 50,
                "amabilidade": 50,
                "neuroticismo": 50,
            }
        },
        "vieses": {
            "aversao_perda": 50,
            "desconto_hiperbolico": 50,
            "suscetibilidade_chamariz": 50,
            "ancoragem": 50,
            "vies_confirmacao": 85,  # HIGH - incoherent with high openness
            "vies_status_quo": 50,
            "sobrecarga_informacao": 50,
        },
    }

    is_valid, errors = validate_coherence(incoherent_synth, strict=False)

    assert is_valid is False, "Incoherent synth should fail validation"
    assert len(errors) > 0, "Should have error messages describing violations"
    # Error should mention the violation
    assert any("confirmacao" in err.lower() or "abertura" in err.lower()
               for err in errors), f"Error should describe violation: {errors}"


def test_batch_generated_synths_all_pass_coherence():
    """
    Test that a batch of generated synths all pass coherence validation.

    This ensures the generation system consistently produces
    psychologically coherent synths.
    """
    from synth_lab.gen_synth.validation import validate_coherence

    config = load_config_data()
    synths = [synth_builder.assemble_synth(config) for _ in range(10)]

    failed_synths = []
    for i, synth in enumerate(synths):
        is_valid, errors = validate_coherence(synth, strict=False)
        if not is_valid:
            failed_synths.append((i, errors))

    assert len(failed_synths) == 0, (
        f"{len(failed_synths)} of 10 synths failed coherence validation: {failed_synths}"
    )

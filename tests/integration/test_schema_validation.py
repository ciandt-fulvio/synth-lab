"""
Integration tests for synth generation with schema v2.0.0.

Tests verify that synths generated with v2.0.0 do not contain removed fields
and pass schema validation.
"""

import json
from pathlib import Path
import sys

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

"""
Unit tests for schema v2.0.0 field removal.

Tests verify that the following fields have been removed from the schema:
- psicografia.valores
- psicografia.hobbies
- psicografia.estilo_vida
- comportamento.uso_tecnologia
- comportamento.comportamento_compra
"""

import json
from pathlib import Path


def test_schema_v2_removed_fields():
    """Test that removed fields are not present in schema v2.0.0."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    # Verify schema is v2.0.0
    assert "$id" in schema
    assert "v2.0.0" in schema["$id"], "Schema should be v2.0.0"

    # Check psicografia properties
    psico_props = schema["properties"]["psicografia"]["properties"]

    assert "valores" not in psico_props, "valores should be removed from psicografia"
    assert "hobbies" not in psico_props, "hobbies should be removed from psicografia"
    assert "estilo_vida" not in psico_props, "estilo_vida should be removed from psicografia"

    # Check comportamento properties
    comp_props = schema["properties"]["comportamento"]["properties"]

    assert "uso_tecnologia" not in comp_props, "uso_tecnologia should be removed from comportamento"
    assert "comportamento_compra" not in comp_props, "comportamento_compra should be removed from comportamento"


def test_schema_v2_retained_fields():
    """Test that important fields are retained in schema v2.0.0."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    # Check retained psicografia fields
    psico_props = schema["properties"]["psicografia"]["properties"]

    assert "personalidade_big_five" in psico_props, "personalidade_big_five should be retained"
    assert "interesses" in psico_props, "interesses should be retained"
    assert "inclinacao_politica" in psico_props, "inclinacao_politica should be retained"
    assert "inclinacao_religiosa" in psico_props, "inclinacao_religiosa should be retained"

    # Check retained comportamento fields
    comp_props = schema["properties"]["comportamento"]["properties"]

    assert "habitos_consumo" in comp_props, "habitos_consumo should be retained"
    assert "padroes_midia" in comp_props, "padroes_midia should be retained"
    assert "lealdade_marca" in comp_props, "lealdade_marca should be retained"


def test_schema_v2_additional_properties_false():
    """Test that additionalProperties is set to false on modified objects."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    # Check psicografia has additionalProperties: false
    psico = schema["properties"]["psicografia"]
    assert "additionalProperties" in psico, "psicografia should have additionalProperties"
    assert psico["additionalProperties"] is False, "psicografia additionalProperties should be false"

    # Check comportamento has additionalProperties: false
    comp = schema["properties"]["comportamento"]
    assert "additionalProperties" in comp, "comportamento should have additionalProperties"
    assert comp["additionalProperties"] is False, "comportamento additionalProperties should be false"


def test_schema_v2_file_size():
    """Test that schema file size is ≤15KB."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    file_size_bytes = schema_path.stat().st_size
    file_size_kb = file_size_bytes / 1024

    assert file_size_kb <= 15, f"Schema file should be ≤15KB, got {file_size_kb:.2f}KB"

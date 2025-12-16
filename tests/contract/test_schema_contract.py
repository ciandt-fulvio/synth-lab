"""
Contract tests for schema v2.0.0 structure.

Tests verify that the schema conforms to the contract defined in
specs/004-simplify-synth-schema/contracts/schema-evolution.md
"""

import json
from pathlib import Path


def test_schema_is_valid_json_schema():
    """Test that schema is valid JSON Schema Draft 2020-12."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    # Must have $schema property
    assert "$schema" in schema
    assert "2020-12" in schema["$schema"], "Should use JSON Schema Draft 2020-12"

    # Must have required properties
    assert "$id" in schema
    assert "title" in schema
    assert "type" in schema
    assert schema["type"] == "object"
    assert "properties" in schema


def test_schema_contract_field_count():
    """Test that schema has approximately 40 fields (down from 45)."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    # Count top-level properties
    top_level_count = len(schema["properties"])

    # Schema should have core sections
    assert "psicografia" in schema["properties"]
    assert "comportamento" in schema["properties"]
    assert "vieses" in schema["properties"]
    assert "demografia" in schema["properties"]

    # Verify reduction in fields
    psico_count = len(schema["properties"]["psicografia"]["properties"])
    comp_count = len(schema["properties"]["comportamento"]["properties"])

    # Psicografia should have ~5 fields (down from ~8)
    assert psico_count <= 6, f"Psicografia should have ≤6 fields, got {psico_count}"

    # Comportamento should have ~4-5 fields (down from ~6)
    assert comp_count <= 6, f"Comportamento should have ≤6 fields, got {comp_count}"


def test_schema_contract_breaking_changes():
    """Test that breaking changes from v1 to v2 are implemented."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    # Breaking change: version bumped to 2.0.0
    assert "v2.0.0" in schema["$id"]

    # Breaking change: removed fields not present
    removed_fields = {
        "psicografia": ["valores", "hobbies", "estilo_vida"],
        "comportamento": ["uso_tecnologia", "comportamento_compra"]
    }

    for section, fields in removed_fields.items():
        section_props = schema["properties"][section]["properties"]
        for field in fields:
            assert field not in section_props, \
                f"Removed field '{section}.{field}' should not be present"


def test_schema_contract_retained_fields():
    """Test that essential fields are retained per contract."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    # Essential fields that must be retained
    essential_fields = {
        "psicografia": ["personalidade_big_five", "interesses"],
        "comportamento": ["habitos_consumo", "padroes_midia"],
        "vieses": [
            "aversao_perda",
            "desconto_hiperbolico",
            "suscetibilidade_chamariz",
            "ancoragem",
            "vies_confirmacao",
            "vies_status_quo",
            "sobrecarga_informacao"
        ]
    }

    for section, fields in essential_fields.items():
        section_props = schema["properties"][section]["properties"]
        for field in fields:
            assert field in section_props, \
                f"Essential field '{section}.{field}' must be retained"


def test_schema_contract_size_reduction():
    """Test that schema file size is reduced per contract (≤15KB target)."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    file_size_bytes = schema_path.stat().st_size
    file_size_kb = file_size_bytes / 1024

    # Contract specifies ≤15KB (from ~18KB = 17% reduction)
    assert file_size_kb <= 15, \
        f"Schema should be ≤15KB per contract, got {file_size_kb:.2f}KB"

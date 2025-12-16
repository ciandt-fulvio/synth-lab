"""
Unit tests for schema version validation.

Tests verify that schema version is correctly set to 2.0.0 and that
version validation works properly.
"""

import json
from pathlib import Path


def test_schema_version_is_2_0_0():
    """Test that schema version is 2.0.0."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    # Check $id contains v2.0.0
    assert "$id" in schema
    assert "v2.0.0" in schema["$id"], f"Schema $id should contain v2.0.0, got: {schema['$id']}"

    # Check version property pattern
    version_prop = schema["properties"]["version"]
    assert "pattern" in version_prop
    expected_pattern = "^2\\.0\\.0$"
    assert version_prop["pattern"] == expected_pattern, \
        f"Version pattern should be {expected_pattern}, got: {version_prop['pattern']}"


def test_schema_id_format():
    """Test that schema $id follows correct format."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    schema_id = schema["$id"]

    # Should follow format: https://synthlab.com/schemas/synth/v2.0.0
    assert schema_id.startswith("https://synthlab.com/schemas/synth/")
    assert schema_id.endswith("/v2.0.0")


def test_schema_description_mentions_simplification():
    """Test that schema description mentions simplification or v2."""
    schema_path = Path("data/schemas/synth-schema-cleaned.json")

    with open(schema_path) as f:
        schema = json.load(f)

    description = schema.get("description", "").lower()

    # Description should mention v2 or simplification
    assert "v2" in description or "2.0.0" in description or "simplificad" in description, \
        "Schema description should mention v2 or simplification"

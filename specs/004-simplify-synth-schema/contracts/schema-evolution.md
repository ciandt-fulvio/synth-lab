# Contract: Schema Evolution (v1.0.0 → v2.0.0)

**Feature**: 004-simplify-synth-schema
**Version**: 1.0.0
**Date**: 2025-12-16

## Purpose

This contract defines the schema changes from v1.0.0 to v2.0.0 and guarantees for schema validation behavior.

## Schema Versions

### Version 1.0.0 (Current/Legacy)

**Identifier**: `https://synthlab.com/schemas/synth/v1.0.0`
**File**: `data/schemas/synth-schema-v1.json` (archived)
**Status**: Deprecated, read-only support

**Field Count**:
- Total: ~45 fields
- Psychographic: 8 fields
- Behavioral: 6 fields

### Version 2.0.0 (New/Simplified)

**Identifier**: `https://synthlab.com/schemas/synth/v2.0.0`
**File**: `data/schemas/synth-schema-cleaned.json`
**Status**: Active, write-enabled

**Field Count**:
- Total: ~40 fields (-5 from v1)
- Psychographic: 5 fields (-3 from v1)
- Behavioral: 4 fields (-2 from v1)

## Breaking Changes (v1 → v2)

### Removed Fields

| Field Path | v1 Type | v2 Status | Reason for Removal |
|------------|---------|-----------|-------------------|
| `psicografia.valores` | `array[string]` | ❌ REMOVED | Redundant with personality_big_five traits |
| `psicografia.hobbies` | `array[string]` | ❌ REMOVED | Interests field provides sufficient detail |
| `psicografia.estilo_vida` | `string` | ❌ REMOVED | Derived from personality, not atomic data |
| `comportamento.uso_tecnologia` | `object` | ❌ REMOVED | Redundant with capacidades_tecnologicas |
| `comportamento.comportamento_compra` | `object` | ❌ REMOVED | Habitos_consumo provides sufficient detail |

### Modified Fields

| Field Path | v1 Value | v2 Value | Change Type |
|------------|----------|----------|-------------|
| `version` | Pattern: `^1\\.0\\.0$` | Pattern: `^2\\.0\\.0$` | Version bump |
| `$id` | `v1.0.0` | `v2.0.0` | Version bump |

### Unchanged Fields (Retained)

All other fields remain unchanged:
- `id`, `nome`, `arquetipo`, `descricao`, `link_photo`, `created_at`
- `demografia.*` (all demographic fields)
- `psicografia.personalidade_big_five.*` (all 5 traits)
- `psicografia.interesses` ✅
- `psicografia.inclinacao_politica`, `psicografia.inclinacao_religiosa`
- `comportamento.habitos_consumo` ✅
- `comportamento.padroes_midia`, `comportamento.fonte_noticias`, `comportamento.lealdade_marca`, `comportamento.engajamento_redes_sociais`
- `vieses.*` (all 7 cognitive biases)
- `deficiencias.*`
- `capacidades_tecnologicas.*`

## Validation Behavior Guarantees

### Schema Validation Contract

```python
def validate_synth_v2(synth: dict) -> None:
    """
    Validate synth against v2.0.0 schema.

    Args:
        synth: Synth data dictionary

    Raises:
        ValidationError: If synth doesn't conform to v2 schema

    Guarantees:
        - MUST reject synths containing removed fields
        - MUST accept synths with all v2 required fields
        - MUST validate field types per v2 schema
        - MUST complete in <50ms per synth
    """
```

### Validation Test Cases

| Synth Content | v1 Validator | v2 Validator | Expected Behavior |
|---------------|--------------|--------------|-------------------|
| All v1 fields present | ✅ PASS | ❌ FAIL | v2 rejects removed fields |
| All v2 fields only | ❌ FAIL | ✅ PASS | v1 rejects missing required fields |
| Removed fields absent | ✅ PASS | ✅ PASS | Both accept minimal valid set |
| Malformed data | ❌ FAIL | ❌ FAIL | Both reject invalid data |

### Backward Compatibility Guarantees

```python
def load_synth(synth_file: str, strict: bool = False) -> dict:
    """
    Load synth from file with version detection.

    Args:
        synth_file: Path to synth JSON file
        strict: If True, enforce v2 schema strictly

    Returns:
        Synth dictionary (normalized to v2 format)

    Guarantees:
        - MUST read v1 synths successfully (strip removed fields)
        - MUST read v2 synths successfully (pass-through)
        - IF strict=False: WARN about removed fields but continue
        - IF strict=True: RAISE error on removed fields
        - MUST preserve all v2-compatible fields from v1 synths
    """
```

**Behavior Matrix**:

| Input Version | strict=False | strict=True | Output |
|---------------|--------------|-------------|--------|
| v1 synth | ✅ Load + warn | ❌ Error | v2 format (fields stripped) |
| v2 synth | ✅ Load | ✅ Load | v2 format (unchanged) |
| Invalid synth | ❌ Error | ❌ Error | N/A |

## Schema File Format

### v2.0.0 Schema Structure

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://synthlab.com/schemas/synth/v2.0.0",
  "title": "Synth (Synthetic Persona)",
  "description": "Schema simplificado para persona sintética brasileira (v2.0.0)",
  "type": "object",
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^2\\.0\\.0$",
      "description": "Schema version (semantic versioning)"
    },
    "psicografia": {
      "type": "object",
      "properties": {
        "personalidade_big_five": { "..." },
        "interesses": { "..." },
        "inclinacao_politica": { "..." },
        "inclinacao_religiosa": { "..." }
      },
      "required": ["personalidade_big_five"],
      "additionalProperties": false
    },
    "comportamento": {
      "type": "object",
      "properties": {
        "habitos_consumo": { "..." },
        "padroes_midia": { "..." },
        "fonte_noticias": { "..." },
        "lealdade_marca": { "..." },
        "engajamento_redes_sociais": { "..." }
      },
      "additionalProperties": false
    },
    "...": "..."
  },
  "required": [
    "id", "nome", "version", "demografia", "psicografia",
    "comportamento", "vieses", "capacidades_tecnologicas"
  ]
}
```

**Key Changes**:
- `additionalProperties: false` on `psicografia` and `comportamento` - strictly reject removed fields
- `version` pattern updated to require "2.0.0"
- `description` updated to indicate simplified schema

## Validation Error Messages

### Error Message Contract

All validation errors MUST provide:
1. **Field path**: Dot-notation path to invalid field
2. **Error type**: Schema violation type (missing, type mismatch, additional property, etc.)
3. **Expected value**: What the schema requires
4. **Actual value**: What was provided

**Example**:

```python
# Error: Removed field present
{
    "error": "ValidationError",
    "message": "Additional property 'hobbies' not allowed in 'psicografia'",
    "field": "psicografia.hobbies",
    "schema_version": "2.0.0",
    "suggestion": "This field was removed in v2.0.0. Use 'psicografia.interesses' instead."
}

# Error: Missing required field
{
    "error": "ValidationError",
    "message": "Missing required property 'personalidade_big_five' in 'psicografia'",
    "field": "psicografia.personalidade_big_five",
    "schema_version": "2.0.0",
    "suggestion": "All synths must include Big Five personality traits."
}

# Error: Wrong version
{
    "error": "ValidationError",
    "message": "Property 'version' does not match pattern '^2\\.0\\.0$'",
    "field": "version",
    "expected": "2.0.0",
    "actual": "1.0.0",
    "schema_version": "2.0.0",
    "suggestion": "This synth uses an old schema version. Consider migrating to v2.0.0."
}
```

## Performance Guarantees

| Operation | v1 Schema | v2 Schema | Improvement |
|-----------|-----------|-----------|-------------|
| Schema validation | ~30ms | <30ms | Maintained |
| Schema file size | ~18KB | ≤15KB | -17% |
| Schema load time | ~5ms | ~4ms | -20% |
| Memory usage | ~8MB | ~7MB | -12.5% |

**Rationale**: Fewer fields → less validation work, smaller file, faster loading.

## Migration Path (Informational)

**Note**: Migration is OUT OF SCOPE for this feature but documented for reference.

### Automated Migration Script (Future Work)

```python
def migrate_synth_v1_to_v2(synth_v1: dict) -> dict:
    """
    Migrate a v1 synth to v2 format.

    This is INFORMATIONAL ONLY - not implemented in this feature.
    """
    synth_v2 = synth_v1.copy()

    # Remove deprecated fields
    if "psicografia" in synth_v2:
        synth_v2["psicografia"].pop("valores", None)
        synth_v2["psicografia"].pop("hobbies", None)
        synth_v2["psicografia"].pop("estilo_vida", None)

    if "comportamento" in synth_v2:
        synth_v2["comportamento"].pop("uso_tecnologia", None)
        synth_v2["comportamento"].pop("comportamento_compra", None)

    # Update version
    synth_v2["version"] = "2.0.0"

    # Validate migrated synth
    validate_synth_v2(synth_v2)

    return synth_v2
```

## Testing Requirements

### Schema Validation Tests

1. **Field Removal**: Verify v2 schema rejects synths with removed fields
2. **Field Retention**: Verify v2 schema accepts synths with all v2 fields
3. **Version Validation**: Verify version field pattern matching
4. **Error Messages**: Verify all error messages match contract format
5. **Performance**: Verify validation completes in <50ms

### Backward Compatibility Tests

1. **v1 Reading**: Verify v1 synths can be loaded successfully
2. **Field Stripping**: Verify removed fields are stripped on load
3. **Warning Generation**: Verify warnings issued for removed fields (strict=False)
4. **Strict Mode**: Verify errors raised for removed fields (strict=True)
5. **Data Preservation**: Verify all v2-compatible fields preserved from v1

### Schema File Tests

1. **File Size**: Verify v2 schema file ≤15KB
2. **Valid JSON Schema**: Verify v2 schema is valid JSON Schema Draft 2020-12
3. **Required Fields**: Verify all required fields documented in schema
4. **Additional Properties**: Verify `additionalProperties: false` on modified objects

## Versioning Rules

### When to Bump Version

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Remove field | MAJOR | v1.0.0 → v2.0.0 ✅ |
| Add required field | MAJOR | v2.0.0 → v3.0.0 |
| Add optional field | MINOR | v2.0.0 → v2.1.0 |
| Change field type | MAJOR | v2.0.0 → v3.0.0 |
| Expand enum values | MINOR | v2.0.0 → v2.1.0 |
| Tighten validation | MAJOR | v2.0.0 → v3.0.0 |
| Fix documentation | PATCH | v2.0.0 → v2.0.1 |

### Version Identifier Format

```
$id: https://synthlab.com/schemas/synth/v{MAJOR}.{MINOR}.{PATCH}
version.pattern: "^{MAJOR}\\.{MINOR}\\.{PATCH}$"
```

**Example**:
```json
{
  "$id": "https://synthlab.com/schemas/synth/v2.0.0",
  "version": {
    "pattern": "^2\\.0\\.0$"
  }
}
```

## Related Contracts

- [coherence-rules.md](./coherence-rules.md) - Personality-bias coherence validation
- [backward-compatibility.md](./backward-compatibility.md) - Version migration guarantees

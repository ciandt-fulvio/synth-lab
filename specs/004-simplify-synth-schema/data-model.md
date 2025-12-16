# Data Model: Simplify Synth Schema

**Feature**: 004-simplify-synth-schema
**Date**: 2025-12-16
**Purpose**: Define simplified synth schema structure, coherence rule data model, and validation architecture

## Schema Evolution

### Version Comparison

| Aspect | v1.0.0 (Current) | v2.0.0 (Simplified) | Change |
|--------|------------------|---------------------|--------|
| Total fields | ~45 fields | ~40 fields | -5 fields |
| Psychographic fields | 8 fields | 5 fields | -3 fields |
| Behavioral fields | 6 fields | 4 fields | -2 fields |
| Coherence rules | None | 10 mappings | +10 rules |
| Schema file size | ~18 KB | ≤15 KB | -17% |
| Version identifier | 1.0.0 | 2.0.0 | MAJOR bump |

### Removed Fields

```json
{
  "psicografia": {
    "valores": "[REMOVED]",           // Removed: redundant with personality traits
    "hobbies": "[REMOVED]",           // Removed: interests field is sufficient
    "estilo_vida": "[REMOVED]"        // Removed: derived from personality, not atomic data
  },
  "comportamento": {
    "uso_tecnologia": "[REMOVED]",    // Removed: redundant with capacidades_tecnologicas
    "comportamento_compra": "[REMOVED]" // Removed: habitos_consumo is sufficient
  }
}
```

### Retained Fields (Simplified View)

```json
{
  "id": "string (6 chars)",
  "nome": "string",
  "arquetipo": "string",
  "descricao": "string",
  "link_photo": "uri",
  "created_at": "datetime",
  "version": "2.0.0",

  "demografia": {
    "idade": "integer",
    "genero_biologico": "enum",
    "identidade_genero": "enum",
    "raca_etnia": "enum",
    "localizacao": { ... },
    "escolaridade": "enum",
    "renda_mensal": "number",
    "ocupacao": "string",
    "estado_civil": "enum",
    "composicao_familiar": { ... }
  },

  "psicografia": {
    "personalidade_big_five": {
      "abertura": "0-100",
      "conscienciosidade": "0-100",
      "extroversao": "0-100",
      "amabilidade": "0-100",
      "neuroticismo": "0-100"
    },
    "interesses": ["string"],
    "inclinacao_politica": "-100 to 100",
    "inclinacao_religiosa": "enum"
  },

  "comportamento": {
    "habitos_consumo": { ... },
    "padroes_midia": { ... },
    "fonte_noticias": ["string"],
    "lealdade_marca": "0-100",
    "engajamento_redes_sociais": { ... }
  },

  "deficiencias": { ... },

  "capacidades_tecnologicas": { ... },

  "vieses": {
    "aversao_perda": "0-100",
    "desconto_hiperbolico": "0-100",
    "suscetibilidade_chamariz": "0-100",
    "ancoragem": "0-100",
    "vies_confirmacao": "0-100",
    "vies_status_quo": "0-100",
    "sobrecarga_informacao": "0-100"
  }
}
```

## Coherence Rule Data Model

### Rule Configuration Structure

```python
# Type definitions for coherence rules
from typing import Tuple, Dict, Literal

PersonalityTrait = Literal[
    "abertura",
    "conscienciosidade",
    "extroversao",
    "amabilidade",
    "neuroticismo"
]

CognitiveBias = Literal[
    "aversao_perda",
    "desconto_hiperbolico",
    "suscetibilidade_chamariz",
    "ancoragem",
    "vies_confirmacao",
    "vies_status_quo",
    "sobrecarga_informacao"
]

TraitLevel = Literal["high", "low"]  # high: 70-100, low: 0-30

BiasRange = Tuple[int, int]  # (min, max) both 0-100


# Coherence rule: (trait, trait_level) -> (bias, bias_range)
CoherenceRule = Dict[
    Tuple[PersonalityTrait, TraitLevel],
    Dict[CognitiveBias, BiasRange]
]
```

### Coherence Rules Table

```python
COHERENCE_RULES: CoherenceRule = {
    # High Conscientiousness: organized, disciplined, prefers stability
    ("conscienciosidade", "high"): {
        "vies_status_quo": (70, 90),       # Strong preference for current state
        "desconto_hiperbolico": (10, 30),  # Weak preference for immediate rewards
    },

    # Low Conscientiousness: impulsive, disorganized
    ("conscienciosidade", "low"): {
        "vies_status_quo": (10, 35),       # Weak preference for current state
        "desconto_hiperbolico": (60, 85),  # Strong preference for immediate rewards
    },

    # High Neuroticism: anxious, emotionally unstable
    ("neuroticismo", "high"): {
        "aversao_perda": (70, 95),         # Strong fear of losses
        "sobrecarga_informacao": (60, 85), # Easily overwhelmed by information
    },

    # Low Neuroticism: emotionally stable, calm
    ("neuroticismo", "low"): {
        "aversao_perda": (10, 35),         # Weak fear of losses
        "sobrecarga_informacao": (15, 40), # Handles information well
    },

    # High Openness: curious, creative, embraces new ideas
    ("abertura", "high"): {
        "vies_confirmacao": (10, 35),      # Weak confirmation bias
        "sobrecarga_informacao": (15, 40), # Enjoys complexity
    },

    # Low Openness: traditional, prefers familiar
    ("abertura", "low"): {
        "vies_confirmacao": (60, 85),      # Strong confirmation bias
        "vies_status_quo": (60, 85),       # Strong resistance to change
    },

    # High Agreeableness: cooperative, empathetic
    ("amabilidade", "high"): {
        "vies_confirmacao": (15, 40),      # Considers diverse viewpoints
        "ancoragem": (40, 60),             # Moderate anchoring
    },

    # Low Agreeableness: competitive, self-focused
    ("amabilidade", "low"): {
        "vies_confirmacao": (65, 90),      # Strong confirmation bias
        "ancoragem": (60, 85),             # Strong anchoring on own values
    },

    # High Extraversion: outgoing, energetic, seeks stimulation
    ("extroversao", "high"): {
        "desconto_hiperbolico": (50, 80),  # Moderate-high immediate reward preference
        "sobrecarga_informacao": (20, 45), # Social processing helps with overload
    },

    # Low Extraversion (Introversion): reserved, prefers calm
    ("extroversao", "low"): {
        "desconto_hiperbolico": (20, 50),  # Moderate-low immediate reward preference
        "sobrecarga_informacao": (45, 70), # More affected by stimulation
    },
}
```

### Rule Application Logic

```python
def get_coherence_expectations(synth: dict) -> Dict[CognitiveBias, BiasRange]:
    """
    Calculate expected bias ranges based on personality traits.

    Returns a dictionary mapping each bias to its expected range
    based on all applicable coherence rules. When multiple rules
    apply to the same bias, union the ranges (take min of mins, max of maxes).
    """
    personality = synth["psicografia"]["personalidade_big_five"]
    expectations = {}

    for trait_name, trait_value in personality.items():
        # Determine trait level
        if trait_value >= 70:
            level = "high"
        elif trait_value <= 30:
            level = "low"
        else:
            # Moderate values (31-69) - no strict rules
            continue

        # Get applicable rules
        rule_key = (trait_name, level)
        if rule_key in COHERENCE_RULES:
            for bias_name, (min_val, max_val) in COHERENCE_RULES[rule_key].items():
                if bias_name in expectations:
                    # Multiple rules affect this bias - expand range
                    existing_min, existing_max = expectations[bias_name]
                    expectations[bias_name] = (
                        min(existing_min, min_val),
                        max(existing_max, max_val)
                    )
                else:
                    expectations[bias_name] = (min_val, max_val)

    return expectations
```

## Validation Architecture

### Validation Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     Synth Validation Pipeline                    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                   ┌───────────────────────┐
                   │ 1. Schema Validation  │
                   │   (jsonschema v2.0.0) │
                   │   - Field presence    │
                   │   - Type checking     │
                   │   - Range validation  │
                   └───────────┬───────────┘
                               │
                         ✅ Valid │ ❌ Invalid
                               │       └──> ValidationError
                               ▼
                   ┌───────────────────────┐
                   │ 2. Coherence Check    │
                   │   (personality-bias)  │
                   │   - Get expectations  │
                   │   - Compare actual    │
                   │   - Raise on conflict │
                   └───────────┬───────────┘
                               │
                         ✅ Valid │ ❌ Invalid
                               │       └──> CoherenceError
                               ▼
                   ┌───────────────────────┐
                   │ 3. Backward Compat    │
                   │   Check (optional)    │
                   │   - Warn on removed   │
                   │   - fields if present │
                   └───────────┬───────────┘
                               │
                               ▼
                        ✅ Fully Valid
```

### Validation Functions

```python
from jsonschema import Draft202012Validator, ValidationError
from typing import Dict, List

class CoherenceError(Exception):
    """Raised when personality-bias coherence rules are violated."""
    pass


def validate_synth_schema(synth: dict) -> None:
    """
    Validate synth against JSON Schema v2.0.0 (strict).

    Raises:
        ValidationError: If synth doesn't conform to schema
    """
    validator = Draft202012Validator(SCHEMA_V2)
    validator.validate(synth)


def validate_coherence(synth: dict) -> None:
    """
    Validate personality-bias coherence rules.

    Raises:
        CoherenceError: If bias values violate personality expectations
    """
    expectations = get_coherence_expectations(synth)
    biases = synth["vieses"]
    violations = []

    for bias_name, (min_expected, max_expected) in expectations.items():
        actual_value = biases[bias_name]

        if not (min_expected <= actual_value <= max_expected):
            violations.append({
                "bias": bias_name,
                "expected_range": (min_expected, max_expected),
                "actual_value": actual_value,
                "personality": {
                    k: v for k, v in synth["psicografia"]["personalidade_big_five"].items()
                    if v >= 70 or v <= 30  # Only report extreme traits
                }
            })

    if violations:
        raise CoherenceError(
            f"Personality-bias coherence violations detected: {violations}"
        )


def validate_synth_full(synth: dict, strict: bool = True) -> Dict[str, List[str]]:
    """
    Full validation: schema + coherence + backward compatibility.

    Args:
        synth: Synth data to validate
        strict: If False, only warn about removed fields instead of error

    Returns:
        Dictionary with 'errors' and 'warnings' keys
    """
    result = {"errors": [], "warnings": []}

    # Schema validation
    try:
        validate_synth_schema(synth)
    except ValidationError as e:
        result["errors"].append(f"Schema validation failed: {e.message}")

    # Coherence validation
    try:
        validate_coherence(synth)
    except CoherenceError as e:
        result["errors"].append(f"Coherence validation failed: {str(e)}")

    # Backward compatibility check
    removed_fields = [
        "psicografia.valores",
        "psicografia.hobbies",
        "psicografia.estilo_vida",
        "comportamento.uso_tecnologia",
        "comportamento.comportamento_compra"
    ]

    for field_path in removed_fields:
        parts = field_path.split(".")
        if len(parts) == 2 and parts[0] in synth:
            if parts[1] in synth[parts[0]]:
                msg = f"Removed field '{field_path}' present (use v2.0.0 schema)"
                if strict:
                    result["errors"].append(msg)
                else:
                    result["warnings"].append(msg)

    return result
```

## Data Transformation

### Synth Generation Flow (Modified)

```
┌─────────────────────────────────────────────────────────────────┐
│                  Synth Generation (v2.0.0)                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────┐
        │ 1. Generate Demographics             │
        │    (age, gender, location, etc.)     │
        └─────────────────┬────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────┐
        │ 2. Generate Personality (Big Five)   │
        │    - Random with distribution        │
        │    *** IDENTIFIES TRAIT LEVELS ***   │
        └─────────────────┬────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────┐
        │ 3. Generate Psychographics           │
        │    - interesses (KEEP)               │
        │    - ❌ NO hobbies                   │
        │    - ❌ NO valores                   │
        │    - ❌ NO estilo_vida               │
        │    - inclinacao_politica             │
        │    - inclinacao_religiosa            │
        └─────────────────┬────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────┐
        │ 4. Generate Behavioral Traits        │
        │    - habitos_consumo (KEEP)          │
        │    - ❌ NO uso_tecnologia            │
        │    - ❌ NO comportamento_compra      │
        │    - padroes_midia                   │
        │    - fonte_noticias                  │
        │    - lealdade_marca                  │
        │    - engajamento_redes_sociais       │
        └─────────────────┬────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────┐
        │ 5. Generate Cognitive Biases         │
        │    *** APPLY COHERENCE RULES ***     │
        │    - Calculate expected ranges       │
        │    - Generate within ranges          │
        └─────────────────┬────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────┐
        │ 6. Generate Tech Capabilities        │
        │    (separate from behavior)          │
        └─────────────────┬────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────┐
        │ 7. Generate Disabilities             │
        └─────────────────┬────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────────┐
        │ 8. Validate Full Synth               │
        │    - Schema validation               │
        │    - Coherence validation            │
        └─────────────────┬────────────────────┘
                          │
                          ▼
                   ✅ Valid Synth
```

### Bias Generation with Coherence

```python
def generate_biases_with_coherence(personality: Dict[str, int]) -> Dict[str, int]:
    """
    Generate cognitive biases that cohere with personality traits.

    Args:
        personality: Big Five personality trait values (0-100)

    Returns:
        Dictionary of bias names to values (0-100)
    """
    import random

    # Get coherence expectations based on personality
    synth_partial = {"psicografia": {"personalidade_big_five": personality}}
    expectations = get_coherence_expectations(synth_partial)

    # Generate bias values
    biases = {}
    all_bias_names = [
        "aversao_perda",
        "desconto_hiperbolico",
        "suscetibilidade_chamariz",
        "ancoragem",
        "vies_confirmacao",
        "vies_status_quo",
        "sobrecarga_informacao"
    ]

    for bias_name in all_bias_names:
        if bias_name in expectations:
            # Constrained by coherence rule
            min_val, max_val = expectations[bias_name]
            biases[bias_name] = random.randint(min_val, max_val)
        else:
            # No constraint - moderate personality trait
            # Use wider range with normal distribution around 50
            biases[bias_name] = max(0, min(100, int(random.gauss(50, 20))))

    return biases
```

## Storage Format

### File Structure (Unchanged)

```
data/
├── schemas/
│   ├── synth-schema-cleaned.json     # v2.0.0 (simplified)
│   └── synth-schema-v1.json          # v1.0.0 (archived for reference)
├── synths/
│   └── synths.json                   # Generated synths (v2.0.0 format)
└── synths.duckdb                     # DuckDB database (v2.0.0 schema)
```

### Schema File Changes

```diff
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
- "$id": "https://synthlab.com/schemas/synth/v1.0.0",
+ "$id": "https://synthlab.com/schemas/synth/v2.0.0",
  "title": "Synth (Synthetic Persona)",
- "description": "Schema completo para persona sintética brasileira...",
+ "description": "Schema simplificado para persona sintética brasileira (v2.0.0)...",
  "version": {
    "type": "string",
-   "pattern": "^1\\.0\\.0$"
+   "pattern": "^2\\.0\\.0$"
  },
  "properties": {
    "psicografia": {
      "properties": {
        "personalidade_big_five": { ... },
        "interesses": { ... },
-       "hobbies": { ... },
-       "valores": { ... },
-       "estilo_vida": { ... },
        "inclinacao_politica": { ... },
        "inclinacao_religiosa": { ... }
      }
    },
    "comportamento": {
      "properties": {
        "habitos_consumo": { ... },
-       "uso_tecnologia": { ... },
-       "comportamento_compra": { ... },
        "padroes_midia": { ... },
        ...
      }
    }
  }
}
```

## Summary

This data model defines:

1. **Simplified Schema**: 5 fields removed, 17% size reduction
2. **Coherence Rules**: 10 personality-bias mappings with psychological basis
3. **Validation Pipeline**: 3-stage validation (schema → coherence → compat)
4. **Generation Flow**: Modified to apply coherence rules during bias generation
5. **Backward Compatibility**: Permissive reading, strict writing

All changes maintain the single project structure with localized modifications to existing modules.

# Contract: Personality-Bias Coherence Rules

**Feature**: 004-simplify-synth-schema
**Version**: 1.0.0
**Date**: 2025-12-16

## Purpose

This contract defines the interface and behavior guarantees for personality-bias coherence validation in synth generation.

## Data Structures

### Input: Personality Traits

```python
PersonalityTraits = {
    "abertura": int,          # 0-100: Openness to experience
    "conscienciosidade": int, # 0-100: Conscientiousness
    "extroversao": int,       # 0-100: Extraversion
    "amabilidade": int,       # 0-100: Agreeableness
    "neuroticismo": int       # 0-100: Neuroticism
}
```

**Constraints**:
- All values MUST be integers in range [0, 100]
- All 5 traits MUST be present

### Output: Bias Ranges

```python
BiasRanges = {
    "aversao_perda": (int, int),           # (min, max) both 0-100
    "desconto_hiperbolico": (int, int),
    "suscetibilidade_chamariz": (int, int),
    "ancoragem": (int, int),
    "vies_confirmacao": (int, int),
    "vies_status_quo": (int, int),
    "sobrecarga_informacao": (int, int)
}
```

**Constraints**:
- Each tuple represents (minimum, maximum) acceptable value for that bias
- min <= max for all tuples
- Both min and max are in range [0, 100]
- Missing bias keys indicate no constraint (personality is moderate on relevant traits)

## Functions

### `get_coherence_expectations(personality: PersonalityTraits) -> BiasRanges`

**Description**: Calculate expected bias ranges based on personality trait values.

**Contract**:

| Condition | Behavior |
|-----------|----------|
| All personality values in [31, 69] | Returns empty dict (no constraints) |
| One or more traits ≥70 or ≤30 | Returns bias ranges per coherence rules |
| Multiple rules affect same bias | Returns union (widest range) |
| Invalid personality input | Raises `ValueError` |

**Example**:

```python
# High conscientiousness (organized, disciplined)
personality = {
    "abertura": 50,
    "conscienciosidade": 85,  # High
    "extroversao": 60,
    "amabilidade": 55,
    "neuroticismo": 40
}

result = get_coherence_expectations(personality)
# Returns:
# {
#     "vies_status_quo": (70, 90),       # High conscientiousness → high status quo bias
#     "desconto_hiperbolico": (10, 30)   # High conscientiousness → low hyperbolic discounting
# }
```

### `validate_coherence(synth: dict) -> None`

**Description**: Validate that synth's bias values fall within expected ranges based on personality.

**Contract**:

| Condition | Behavior |
|-----------|----------|
| All bias values within expected ranges | Returns None (success) |
| One or more biases out of range | Raises `CoherenceError` with violation details |
| Synth missing required fields | Raises `KeyError` |
| Personality traits invalid | Raises `ValueError` |

**CoherenceError Format**:

```python
{
    "violations": [
        {
            "bias": "desconto_hiperbolico",
            "expected_range": (10, 30),
            "actual_value": 75,
            "conflicting_traits": {
                "conscienciosidade": 85  # High conscientiousness expects low hyperbolic discounting
            }
        }
    ]
}
```

**Example**:

```python
synth = {
    "psicografia": {
        "personalidade_big_five": {
            "abertura": 50,
            "conscienciosidade": 85,
            "extroversao": 60,
            "amabilidade": 55,
            "neuroticismo": 40
        }
    },
    "vieses": {
        "aversao_perda": 50,
        "desconto_hiperbolico": 75,  # ❌ Too high for high conscientiousness
        "suscetibilidade_chamariz": 60,
        "ancoragem": 55,
        "vies_confirmacao": 50,
        "vies_status_quo": 80,  # ✅ Within range (70-90)
        "sobrecarga_informacao": 45
    }
}

validate_coherence(synth)
# Raises CoherenceError: "desconto_hiperbolico value 75 outside expected range (10, 30)"
```

### `generate_biases_with_coherence(personality: PersonalityTraits) -> dict`

**Description**: Generate bias values that automatically cohere with personality traits.

**Contract**:

| Condition | Behavior |
|-----------|----------|
| Bias constrained by rule | Value randomly selected within rule range |
| Bias not constrained | Value randomly selected with wider distribution (gauss μ=50, σ=20) |
| Invalid personality input | Raises `ValueError` |
| Generated biases | MUST pass `validate_coherence()` when combined with input personality |

**Guarantees**:
- Generated bias values MUST be integers in [0, 100]
- Generated synth with returned biases MUST pass coherence validation
- Multiple calls with same personality MAY return different values (randomized)
- Values MUST be plausibly distributed (no edge-case artifacts)

**Example**:

```python
personality = {
    "abertura": 50,
    "conscienciosidade": 85,  # High
    "extroversao": 60,
    "amabilidade": 55,
    "neuroticismo": 40
}

biases = generate_biases_with_coherence(personality)
# Returns something like:
# {
#     "aversao_perda": 48,            # Unconstrained (moderate neuroticism)
#     "desconto_hiperbolico": 22,     # Constrained: within (10, 30)
#     "suscetibilidade_chamariz": 63, # Unconstrained
#     "ancoragem": 51,                # Unconstrained
#     "vies_confirmacao": 55,         # Unconstrained
#     "vies_status_quo": 78,          # Constrained: within (70, 90)
#     "sobrecarga_informacao": 44     # Unconstrained
# }

# Guarantee: This MUST be valid
synth = {
    "psicografia": {"personalidade_big_five": personality},
    "vieses": biases
}
validate_coherence(synth)  # MUST NOT raise CoherenceError
```

## Coherence Rule Mapping

### Complete Rule Set

| Personality Trait | Level | Cognitive Bias | Range | Psychological Basis |
|-------------------|-------|----------------|-------|---------------------|
| conscienciosidade | High (70-100) | vies_status_quo | (70, 90) | Organized individuals prefer stability |
| conscienciosidade | High (70-100) | desconto_hiperbolico | (10, 30) | Disciplined individuals plan ahead |
| conscienciosidade | Low (0-30) | vies_status_quo | (10, 35) | Disorganized individuals less attached to status quo |
| conscienciosidade | Low (0-30) | desconto_hiperbolico | (60, 85) | Impulsive individuals prefer immediate rewards |
| neuroticismo | High (70-100) | aversao_perda | (70, 95) | Anxious individuals fear losses |
| neuroticismo | High (70-100) | sobrecarga_informacao | (60, 85) | Anxious individuals overwhelmed by complexity |
| neuroticismo | Low (0-30) | aversao_perda | (10, 35) | Stable individuals tolerate risk |
| neuroticismo | Low (0-30) | sobrecarga_informacao | (15, 40) | Stable individuals handle information well |
| abertura | High (70-100) | vies_confirmacao | (10, 35) | Open individuals seek diverse views |
| abertura | High (70-100) | sobrecarga_informacao | (15, 40) | Open individuals enjoy complexity |
| abertura | Low (0-30) | vies_confirmacao | (60, 85) | Closed individuals prefer familiar ideas |
| abertura | Low (0-30) | vies_status_quo | (60, 85) | Traditional individuals resist change |
| amabilidade | High (70-100) | vies_confirmacao | (15, 40) | Agreeable individuals consider others |
| amabilidade | High (70-100) | ancoragem | (40, 60) | Cooperative individuals moderate anchoring |
| amabilidade | Low (0-30) | vies_confirmacao | (65, 90) | Disagreeable individuals dismiss contrary evidence |
| amabilidade | Low (0-30) | ancoragem | (60, 85) | Self-focused individuals anchor on own values |
| extroversao | High (70-100) | desconto_hiperbolico | (50, 80) | Extraverts seek immediate rewards |
| extroversao | High (70-100) | sobrecarga_informacao | (20, 45) | Social processing helps with overload |
| extroversao | Low (0-30) | desconto_hiperbolico | (20, 50) | Introverts more patient |
| extroversao | Low (0-30) | sobrecarga_informacao | (45, 70) | Introverts more affected by stimulation |

### Rule Application Algorithm

```
FOR each trait in personality:
    IF trait.value >= 70:
        level = "high"
    ELSE IF trait.value <= 30:
        level = "low"
    ELSE:
        CONTINUE  # Moderate trait, no constraint

    FOR each (bias, range) in RULES[(trait.name, level)]:
        IF bias already has expected range:
            # Multiple rules affect this bias - take union
            expected[bias] = (
                min(expected[bias].min, range.min),
                max(expected[bias].max, range.max)
            )
        ELSE:
            expected[bias] = range

RETURN expected
```

## Error Handling

### `ValueError`

**When**: Invalid input data (personality values out of range, missing required fields)

**Example**:
```python
personality = {"abertura": 150}  # Invalid: > 100
get_coherence_expectations(personality)
# Raises: ValueError("abertura value 150 outside valid range [0, 100]")
```

### `CoherenceError`

**When**: Bias values violate personality-based expectations

**Fields**:
- `violations`: List of violation details (bias, expected, actual, conflicting traits)
- `message`: Human-readable error description

**Example**:
```python
CoherenceError(
    "Personality-bias coherence violations: "
    "desconto_hiperbolico=75 outside expected (10, 30) for conscienciosidade=85"
)
```

### `KeyError`

**When**: Required fields missing from synth data structure

**Example**:
```python
synth = {"psicografia": {}}  # Missing personalidade_big_five
validate_coherence(synth)
# Raises: KeyError("personalidade_big_five")
```

## Performance Guarantees

| Operation | Max Time | Typical Time |
|-----------|----------|--------------|
| `get_coherence_expectations()` | 5ms | <1ms |
| `validate_coherence()` | 20ms | <5ms |
| `generate_biases_with_coherence()` | 10ms | <3ms |

**Scalability**:
- Time complexity: O(n) where n = number of personality traits (constant at 5)
- Space complexity: O(m) where m = number of biases (constant at 7)
- No external dependencies (database, network, filesystem)

## Testing Requirements

### Unit Tests

1. **Rule Coverage**: Test each of the 20 personality-bias rules individually
2. **Edge Cases**: Test boundary values (0, 30, 31, 69, 70, 100)
3. **Multiple Rules**: Test biases affected by multiple personality traits
4. **Error Handling**: Test all error conditions (ValueError, CoherenceError, KeyError)

### Integration Tests

1. **End-to-End Generation**: Generate 100 synths, verify all pass coherence validation
2. **Extreme Personalities**: Test synths with all traits at extremes (all 0-30 or all 70-100)
3. **Moderate Personalities**: Test synths with all traits moderate (40-60) have no constraints

### Contract Tests

1. **Function Signatures**: Verify all functions match documented signatures
2. **Return Types**: Verify all return values match documented types
3. **Exception Types**: Verify all exceptions match documented types
4. **Performance**: Verify all operations complete within guaranteed time limits

## Versioning

**Contract Version**: 1.0.0

**Breaking Changes** (require major version bump):
- Adding/removing personality traits
- Adding/removing cognitive biases
- Changing rule ranges by >20 points
- Changing function signatures

**Non-Breaking Changes** (allow minor/patch version bump):
- Adjusting rule ranges by ≤20 points
- Adding optional parameters
- Improving error messages
- Performance optimizations

## Related Contracts

- [schema-evolution.md](./schema-evolution.md) - JSON Schema v2.0.0 contract
- [backward-compatibility.md](./backward-compatibility.md) - Version migration contract

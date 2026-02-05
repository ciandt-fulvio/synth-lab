# Research: Mechanism-Based Simulation

**Feature**: 038-mechanism-based-simulation
**Date**: 2026-02-04

## Research Questions

### RQ-1: How should mechanism×sensitivity interactions modify simulation behavior?

**Decision**: Simple multiplicative interaction model with additive aggregation to emergent states.

**Rationale**:
- Simple multiplication (mechanism_intensity × user_sensitivity) produces values in [0,1] when both inputs are in [0,1]
- Emergent states aggregate multiple interactions to modify effective scorecard dimensions
- Preserves interpretability: "High perceived_risk emerged from irreversibility(0.9) × risk_aversion(0.73) = 0.66"

**Alternatives Considered**:
1. Non-linear interactions (sigmoid, quadratic): More expressive but harder to explain
2. Weighted averages: Loses the multiplicative sensitivity effect
3. Bayesian updating: Too complex for initial implementation

**Implementation Formula**:
```python
# Emergent states from interactions
perceived_risk_emergent = mechanisms.irreversibility * sensitivities.risk_aversion
social_barrier_emergent = mechanisms.network_effect * (1 - sensitivities.social_dependency)
trust_requirement_emergent = mechanisms.institutional_trust * (1 - sensitivities.institutional_trust_level)
habit_friction_emergent = mechanisms.habit_displacement * (1 - sensitivities.habit_plasticity)
learning_effort_emergent = mechanisms.learning_curve * (1 - sensitivities.learning_tolerance)
visibility_effect_emergent = mechanisms.social_visibility * sensitivities.social_influence

# Aggregate to modify scorecard dimensions
effective_perceived_risk = scorecard.perceived_risk + α * perceived_risk_emergent
effective_initial_effort = scorecard.initial_effort + β * (habit_friction_emergent + learning_effort_emergent)
# ... etc
```

### RQ-2: How should mechanisms be stored (new table vs JSONB extension)?

**Decision**: Extend existing `scorecard_data` JSONB column in `experiments` table.

**Rationale**:
- Scorecard and mechanisms are conceptually one unit (feature definition)
- No migration needed - JSONB schema evolves naturally
- Backward compatible - old experiments have no `mechanisms` key, treated as all zeros
- Follows existing pattern (scorecard_data already JSONB)

**Alternatives Considered**:
1. New `feature_mechanisms` table with FK to experiments: Over-normalized, adds JOIN complexity
2. Separate column: Would require migration and schema changes

**Storage Schema**:
```json
{
  "scorecard_data": {
    "complexity": {"score": 0.4, "rules_applied": [...]},
    "initial_effort": {"score": 0.3, ...},
    "perceived_risk": {"score": 0.2, ...},
    "time_to_value": {"score": 0.5, ...},
    "mechanisms": {
      "irreversibility": 0.9,
      "network_effect": 0.7,
      "institutional_trust": 0.8,
      "habit_displacement": 0.4,
      "learning_curve": 0.5,
      "social_visibility": 0.3
    },
    "feature_types": ["financial", "social"]
  }
}
```

### RQ-3: How should sensitivities be stored on synths?

**Decision**: Extend existing `simulation_attributes` structure within synth `data` JSONB.

**Rationale**:
- Sensitivities are synth-level attributes like latent_traits
- Follows existing pattern (simulation_attributes already has observables + latent_traits)
- Generation can happen during gensynth or as post-processing
- Backward compatible - missing sensitivities default to 0.5 (neutral)

**Storage Schema**:
```json
{
  "data": {
    "simulation_attributes": {
      "observables": {...},
      "latent_traits": {...},
      "sensitivities": {
        "risk_aversion": 0.73,
        "social_dependency": 0.45,
        "institutional_trust_level": 0.61,
        "habit_plasticity": 0.55,
        "learning_tolerance": 0.68,
        "social_influence": 0.40
      }
    }
  }
}
```

### RQ-4: How to ensure backward compatibility?

**Decision**: Default mechanisms to 0.0 and sensitivities to 0.5, which produces zero interaction effect.

**Rationale**:
- mechanism=0 means "this mechanism is not present in the feature"
- sensitivity=0.5 is the neutral point where interactions don't amplify or dampen
- When all mechanisms=0, no emergent states are produced, simulation uses raw scorecard
- Existing experiments work identically to before

**Implementation**:
```python
def get_effective_mechanisms(scorecard_data: dict) -> FeatureMechanisms:
    """Extract mechanisms with defaults."""
    raw = scorecard_data.get("mechanisms", {})
    return FeatureMechanisms(
        irreversibility=raw.get("irreversibility", 0.0),
        network_effect=raw.get("network_effect", 0.0),
        # ... all default to 0.0
    )

def get_sensitivities(simulation_attributes: dict) -> UserSensitivities:
    """Extract sensitivities with neutral defaults."""
    raw = simulation_attributes.get("sensitivities", {})
    return UserSensitivities(
        risk_aversion=raw.get("risk_aversion", 0.5),
        # ... all default to 0.5
    )
```

### RQ-5: How to implement same-world comparison mode?

**Decision**: Pre-sample all user states for a world, then replay against multiple features.

**Rationale**:
- A "world" is a specific instantiation of uncertainty (all random samples fixed)
- Same seed + same synths = same user_state samples
- For fair comparison, features must face identical user states
- This is already partially supported via seed parameter

**Implementation**:
```python
def run_same_world_comparison(
    synths: list[dict],
    features: list[FeatureScorecard],
    scenario: Scenario,
    seed: int,
    n_executions: int
) -> dict[str, SimulationResults]:
    """Compare multiple features in the same world."""
    # Sample user states once
    rng = np.random.default_rng(seed)
    world_states = []
    for synth in synths:
        synth_states = []
        for _ in range(n_executions):
            state = sample_user_state(synth, scenario, sigma, rng)
            synth_states.append(state)
        world_states.append(synth_states)

    # Run each feature against the same states
    results = {}
    for feature in features:
        feature_results = simulate_with_states(world_states, feature)
        results[feature.id] = feature_results

    return results
```

### RQ-6: How to generate explanation data efficiently?

**Decision**: Calculate and store top-N contributing interactions per synth outcome.

**Rationale**:
- Full interaction matrix per synth (6×6=36) is expensive to store
- Only top 3-5 contributors matter for explanation
- Calculate on-demand during simulation and store with outcome

**Implementation**:
```python
@dataclass
class EmergentStateExplanation:
    """Explanation of which interactions drove emergent state."""
    synth_id: str
    top_contributors: list[tuple[str, str, float]]  # (mechanism, sensitivity, product)
    perceived_risk_delta: float
    initial_effort_delta: float
    # ... deltas from raw scorecard

# Store in synth_outcomes.synth_attributes:
{
    "observables": {...},
    "latent_traits": {...},
    "sensitivities": {...},
    "emergent_explanation": {
        "top_contributors": [
            ["irreversibility", "risk_aversion", 0.66],
            ["network_effect", "social_dependency", 0.36],
            ["learning_curve", "learning_tolerance", 0.16]
        ],
        "perceived_risk_delta": 0.15,
        "initial_effort_delta": 0.08
    }
}
```

## Performance Considerations

### Current Performance Baseline
- 100 synths × 100 executions < 1 second
- O(N×M) where N=synths, M=executions

### Additional Computation
- 6 mechanism × sensitivity multiplications per user state sample
- 4-6 additions for emergent state aggregation
- ~10 extra float operations per sample

### Expected Impact
- Negligible (<5% overhead)
- NumPy operations are vectorized where possible
- No additional I/O or LLM calls

## Mechanism-Sensitivity Pairing Rationale

| Mechanism | Paired Sensitivity | Interaction Meaning |
|-----------|-------------------|---------------------|
| irreversibility | risk_aversion | High irreversibility × high risk aversion = strong barrier |
| network_effect | social_dependency | High network × high social dependency = waits for others |
| institutional_trust | institutional_trust_level | High required trust × low user trust = strong barrier |
| habit_displacement | habit_plasticity | High displacement × low plasticity = strong friction |
| learning_curve | learning_tolerance | High learning × low tolerance = strong effort barrier |
| social_visibility | social_influence | High visibility × high influence = social pressure effect |

## Test Strategy

### Unit Tests (Fast Battery)
1. FeatureMechanisms validation (values in [0,1])
2. UserSensitivities validation (values in [0,1], defaults to 0.5)
3. EmergentState calculation (interaction formula)
4. Backward compatibility (no mechanisms = current behavior)

### Integration Tests
1. Full simulation with mechanisms produces different results than without
2. Same-score features with different mechanisms produce >15% variance
3. Existing experiments run identically (regression test)
4. Same-world comparison produces reproducible results

### Validation Criteria
- SC-001: ≥15% variance between same-score different-mechanism features
- SC-003: Zero regression on existing experiments
- SC-004: Same seed = identical results

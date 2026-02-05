# Data Model: Mechanism-Based Simulation

**Feature**: 038-mechanism-based-simulation
**Date**: 2026-02-04

## Entity Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FEATURE SIDE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  FeatureScorecard (existing)                                        │
│  ├── identification: ScorecardIdentification                        │
│  ├── complexity: ScorecardDimension                                 │
│  ├── initial_effort: ScorecardDimension                             │
│  ├── perceived_risk: ScorecardDimension                             │
│  ├── time_to_value: ScorecardDimension                              │
│  ├── mechanisms: FeatureMechanisms (NEW)  ◄──┐                      │
│  └── feature_types: list[str] (NEW)          │                      │
│                                              │                      │
│  FeatureMechanisms (NEW)                     │                      │
│  ├── irreversibility: float [0,1]       ─────┘                      │
│  ├── network_effect: float [0,1]                                    │
│  ├── institutional_trust: float [0,1]                               │
│  ├── habit_displacement: float [0,1]                                │
│  ├── learning_curve: float [0,1]                                    │
│  └── social_visibility: float [0,1]                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          USER SIDE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SimulationAttributes (existing)                                    │
│  ├── observables: SimulationObservables                             │
│  ├── latent_traits: SimulationLatentTraits                          │
│  └── sensitivities: UserSensitivities (NEW)  ◄──┐                   │
│                                                 │                   │
│  UserSensitivities (NEW)                        │                   │
│  ├── risk_aversion: float [0,1]            ─────┘                   │
│  ├── social_dependency: float [0,1]                                 │
│  ├── institutional_trust_level: float [0,1]                         │
│  ├── habit_plasticity: float [0,1]                                  │
│  ├── learning_tolerance: float [0,1]                                │
│  └── social_influence: float [0,1]                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      INTERACTION LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  EmergentState (NEW - runtime only, stored in outcome)              │
│  ├── perceived_risk_delta: float                                    │
│  ├── initial_effort_delta: float                                    │
│  ├── trust_barrier: float                                           │
│  ├── social_barrier: float                                          │
│  ├── top_contributors: list[InteractionContribution]                │
│  └── raw_interactions: dict[str, float]                             │
│                                                                     │
│  InteractionContribution (NEW)                                      │
│  ├── mechanism: str                                                 │
│  ├── sensitivity: str                                               │
│  └── product: float                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Entity Definitions

### FeatureMechanisms (NEW)

Represents the structural mechanisms inherent to a feature that determine how it interacts with user psychology.

```python
class FeatureMechanisms(BaseModel):
    """
    Feature mechanisms that interact with user sensitivities.

    Each mechanism represents a structural property of the feature:
    - irreversibility: Actions cannot be undone (0=reversible, 1=permanent)
    - network_effect: Value depends on others using it (0=individual, 1=requires network)
    - institutional_trust: Requires trust in institution (0=peer, 1=institutional)
    - habit_displacement: Replaces existing habits (0=additive, 1=replacement)
    - learning_curve: Requires learning new skills (0=intuitive, 1=complex)
    - social_visibility: Usage is visible to others (0=private, 1=public)
    """

    irreversibility: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Degree to which actions are permanent/irreversible"
    )

    network_effect: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Degree to which value depends on others using it"
    )

    institutional_trust: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Degree to which feature requires trust in institution"
    )

    habit_displacement: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Degree to which feature replaces existing habits"
    )

    learning_curve: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Degree to which feature requires learning new skills"
    )

    social_visibility: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Degree to which usage is visible to others"
    )

    def has_any_mechanism(self) -> bool:
        """Check if any mechanism is non-zero."""
        return any([
            self.irreversibility > 0,
            self.network_effect > 0,
            self.institutional_trust > 0,
            self.habit_displacement > 0,
            self.learning_curve > 0,
            self.social_visibility > 0
        ])
```

### UserSensitivities (NEW)

Extension to SimulationAttributes representing user psychological sensitivities to mechanisms.

```python
class UserSensitivities(BaseModel):
    """
    User sensitivities that interact with feature mechanisms.

    Each sensitivity represents how a user responds to a mechanism:
    - risk_aversion: Sensitivity to irreversible actions (high = avoids risk)
    - social_dependency: Importance of others using feature (high = follower)
    - institutional_trust_level: Trust in institutions (high = trusts institutions)
    - habit_plasticity: Ease of changing habits (high = adaptable)
    - learning_tolerance: Tolerance for learning effort (high = patient learner)
    - social_influence: Influenced by social visibility (high = conformist)

    Default value of 0.5 represents neutral sensitivity.
    """

    risk_aversion: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Sensitivity to irreversible actions (0=risk-seeking, 1=risk-averse)"
    )

    social_dependency: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Importance of others using the feature (0=independent, 1=follower)"
    )

    institutional_trust_level: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Trust in institutions (0=distrustful, 1=trusting)"
    )

    habit_plasticity: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Ease of changing habits (0=rigid, 1=adaptable)"
    )

    learning_tolerance: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Tolerance for learning effort (0=impatient, 1=patient)"
    )

    social_influence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Influenced by social visibility (0=independent, 1=conformist)"
    )
```

### EmergentState (NEW)

Runtime calculation result showing how mechanism×sensitivity interactions modify the effective feature difficulty.

```python
@dataclass
class EmergentState:
    """
    Emergent behavioral state from mechanism × sensitivity interactions.

    Calculated per user per simulation execution.
    Modifies effective scorecard dimensions.
    """

    # Deltas to apply to scorecard dimensions
    perceived_risk_delta: float  # From irreversibility × risk_aversion
    initial_effort_delta: float  # From habit_displacement + learning_curve interactions
    trust_barrier: float  # From institutional_trust × (1 - trust_level)
    social_barrier: float  # From network_effect × (1 - social_dependency)

    # For explainability
    top_contributors: list[InteractionContribution]
    raw_interactions: dict[str, float]  # All mechanism_sensitivity products

    @classmethod
    def calculate(
        cls,
        mechanisms: FeatureMechanisms,
        sensitivities: UserSensitivities
    ) -> "EmergentState":
        """Calculate emergent state from mechanism × sensitivity interactions."""
        # ... implementation in mechanism_interaction.py
```

### InteractionContribution (NEW)

Single mechanism×sensitivity contribution for explainability.

```python
@dataclass
class InteractionContribution:
    """Single mechanism × sensitivity interaction contribution."""
    mechanism: str  # e.g., "irreversibility"
    sensitivity: str  # e.g., "risk_aversion"
    product: float  # mechanism_value × sensitivity_value
```

## Storage Schema Changes

### experiments.scorecard_data (JSONB extension)

No migration needed - JSONB schema evolves naturally.

```json
{
  "identification": {...},
  "description_text": "...",
  "complexity": {"score": 0.4, "rules_applied": [], ...},
  "initial_effort": {"score": 0.3, ...},
  "perceived_risk": {"score": 0.2, ...},
  "time_to_value": {"score": 0.5, ...},
  "justification": "...",
  "impact_hypotheses": [...],
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
```

### synths.data.simulation_attributes (JSONB extension)

No migration needed - JSONB schema evolves naturally.

```json
{
  "observables": {
    "digital_literacy": 0.6,
    "similar_tool_experience": 0.5,
    "motor_ability": 1.0,
    "time_availability": 0.5,
    "domain_expertise": 0.5
  },
  "latent_traits": {
    "capability_mean": 0.55,
    "trust_mean": 0.55,
    "friction_tolerance_mean": 0.52,
    "exploration_prob": 0.47
  },
  "sensitivities": {
    "risk_aversion": 0.73,
    "social_dependency": 0.45,
    "institutional_trust_level": 0.61,
    "habit_plasticity": 0.55,
    "learning_tolerance": 0.68,
    "social_influence": 0.40
  }
}
```

### synth_outcomes.synth_attributes (JSONB extension)

Enhanced with emergent state explanation for post-hoc analysis.

```json
{
  "observables": {...},
  "latent_traits": {...},
  "sensitivities": {...},
  "emergent_explanation": {
    "top_contributors": [
      {"mechanism": "irreversibility", "sensitivity": "risk_aversion", "product": 0.66},
      {"mechanism": "network_effect", "sensitivity": "social_dependency", "product": 0.36},
      {"mechanism": "learning_curve", "sensitivity": "learning_tolerance", "product": 0.16}
    ],
    "perceived_risk_delta": 0.15,
    "initial_effort_delta": 0.08
  }
}
```

## Validation Rules

### FeatureMechanisms
- All values MUST be in [0, 1]
- Defaults to 0.0 (mechanism not present)
- Missing in scorecard_data = all mechanisms 0.0

### UserSensitivities
- All values MUST be in [0, 1]
- Defaults to 0.5 (neutral sensitivity)
- Missing in simulation_attributes = all sensitivities 0.5

### Backward Compatibility
- Experiments without `mechanisms` key: Use all zeros
- Synths without `sensitivities` key: Use all 0.5s
- Result: Emergent state has zero effect, simulation identical to current

## State Transitions

### Scorecard State Flow

```
Draft (no mechanisms)
    │
    ▼
Mechanisms Defined (user inputs values)
    │
    ▼
Ready for Simulation (validation passes)
```

### Synth State Flow

```
Generated (no sensitivities)
    │
    ▼ [gensynth enhancement or post-processing]
    │
Sensitivities Added (values in [0,1])
    │
    ▼
Ready for Mechanism Simulation
```

## Relationships

```
Experiment 1──────1 FeatureScorecard 1────0..1 FeatureMechanisms
     │
     │ synth_group_id
     ▼
SynthGroup 1──────* Synth 1────1 SimulationAttributes 1────0..1 UserSensitivities

AnalysisRun 1──────* SynthOutcome
     │                    │
     │                    └── synth_attributes (snapshot with sensitivities + emergent_explanation)
     │
     └── config, aggregated_outcomes
```

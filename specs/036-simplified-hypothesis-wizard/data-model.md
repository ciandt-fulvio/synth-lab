# Data Model: Simplified Hypothesis Wizard

**Feature**: 036-simplified-hypothesis-wizard
**Date**: 2026-01-28
**Status**: Phase 1 Design

## Overview

This feature introduces NO new database entities. All wizard logic uses existing `Hypothesis`, `CausalDAG`, and `Variable` entities. The wizard orchestrates hypothesis generation using in-memory state (scenario profile, clarification responses) that is NOT persisted.

## Database Schema (No Changes)

### Existing Tables (Reused)

**hypotheses** (existing, no modifications):
```sql
CREATE TABLE hypotheses (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id),
    variable_name TEXT NOT NULL,
    distribution_type TEXT NOT NULL,  -- "normal", "uniform", "beta", "lognormal", "bernoulli", "triangular"
    distrib_params JSONB NOT NULL,    -- { "mu": 0.5, "sigma": 0.1 } or { "min": 0, "max": 1 }, etc.
    range_min REAL,
    range_max REAL,
    correlations JSONB,               -- [{ "with_variable": "X", "coefficient": 0.7 }]
    scenario_options JSONB,           -- NOT used by wizard (reserved for manual editor)
    selected_scenario TEXT,           -- NOT used by wizard
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**causal_dags** (existing, no modifications):
```sql
CREATE TABLE causal_dags (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id),
    version INTEGER NOT NULL,
    nodes JSONB NOT NULL,             -- [{ "name": "X", "type": "metric", "label": "User engagement", ... }]
    edges JSONB NOT NULL,             -- [{ "from": "X", "to": "Y", "strength_estimated": "moderate" }]
    assumptions JSONB,
    risks JSONB,
    created_at TIMESTAMP
);
```

**hypothesis_versions** (existing, optional use):
```sql
CREATE TABLE hypothesis_versions (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    hypotheses JSONB NOT NULL,        -- Snapshot of all hypotheses
    created_at TIMESTAMP,
    created_by TEXT
);
```

## Domain Entities

### Existing Entities (Reused)

**Hypothesis** (domain/entities/hypothesis.py):
```python
@dataclass
class Hypothesis:
    id: str                          # hyp_XXXXXXXX
    simulation_id: str               # sim_XXXXXXXX
    variable_name: str               # From DAG node
    distribution_type: DistributionType  # Enum: NORMAL, UNIFORM, BETA, etc.
    distrib_params: HypothesisParameters # Union of NormalParams, UniformParams, etc.
    range_min: float | None
    range_max: float | None
    correlations: list[Correlation] | None
    scenario_options: list[ScenarioOption] | None  # NOT populated by wizard
    selected_scenario: str | None                   # NOT populated by wizard
    created_at: datetime
    updated_at: datetime
```

**CausalDAG** (domain/entities/causal_dag.py):
```python
@dataclass
class CausalDAG:
    id: str
    simulation_id: str
    version: int
    nodes: list[Variable]
    edges: list[Edge]
    assumptions: list[Assumption] | None
    risks: list[Risk] | None
    created_at: datetime

@dataclass
class Variable:
    name: str                        # Unique identifier within DAG
    type: VariableType              # EVENT, METRIC, RATE, DURATION, ATTRIBUTE, COST, DECISION
    scope: VariableScope            # EXTERNAL, INTERNAL
    label: str                      # Human-readable name (e.g., "User Engagement")
    description: str | None
    controllability: Controllability # NONE, LOW, MEDIUM, HIGH
    is_intervention: bool
    is_outcome: bool
    is_critical_uncertainty: bool   # Domain expert flag for must-clarify variables
    position_x: float | None
    position_y: float | None
    unit: str | None
```

### New In-Memory Entities (NOT Persisted)

**ScenarioProfile** (services/simulation/hypothesis_wizard_service.py):
```python
class ScenarioProfile(str, Enum):
    """Predefined scenario profiles for hypothesis generation."""
    CONSERVATIVE = "conservative"   # Worse-than-average outcomes, higher uncertainty
    REALISTIC = "realistic"         # Market-average parameters (default)
    OPTIMISTIC = "optimistic"       # Better-than-average outcomes, lower uncertainty
```

**ClarificationQuestion** (services/simulation/hypothesis_wizard_service.py):
```python
@dataclass
class ClarificationQuestion:
    """A qualitative question about a critical variable."""
    variable_name: str              # Variable to clarify
    question_text: str              # Human-readable question (e.g., "Is X more common or rare?")
    criticality_score: float        # Ranking score (for debugging/logging)
```

**ClarificationResponse** (services/simulation/hypothesis_wizard_service.py):
```python
class ResponseType(str, Enum):
    """Qualitative response options."""
    MORE = "more"                   # Higher frequency/magnitude than expected
    LESS = "less"                   # Lower frequency/magnitude than expected
    EQUAL = "equal"                 # Matches expectation (profile default)
    DONT_KNOW = "dont_know"         # High uncertainty, increase variance

@dataclass
class ClarificationResponse:
    """User's response to a clarification question."""
    variable_name: str
    response: ResponseType
```

**WizardState** (in-memory only, not a persistent entity):
```python
@dataclass
class WizardState:
    """Ephemeral state during wizard execution."""
    simulation_id: str
    selected_profile: ScenarioProfile
    clarification_questions: list[ClarificationQuestion]
    clarification_responses: list[ClarificationResponse]
    generated_hypotheses: list[Hypothesis]
```

## Entity Relationships

```
Simulation (existing)
    ↓ 1:1
CausalDAG (existing)
    ↓ contains
Variables (existing, in DAG.nodes)
    ↓ generate
Hypotheses (existing, via wizard)
    ↓ optional snapshot
HypothesisVersion (existing)

[Wizard State]
    → ScenarioProfile (in-memory)
    → ClarificationQuestions (in-memory, generated from Variables)
    → ClarificationResponses (in-memory, user input)
    → WizardState (in-memory, orchestration)
```

## Data Flow

### Wizard Initialization (POST /wizard/init)

```
1. Load CausalDAG for simulation
   ↓
2. Extract variables from DAG.nodes
   ↓
3. User selects ScenarioProfile
   ↓
4. Call HypothesisParametrizerService.quantify(dag, profile_hint)
   → Generates baseline hypotheses with profile-aware parameters
   ↓
5. Apply profile adjustments (research.md Decision 1)
   ↓
6. Classify decision context (simple/complex) using DAG structure
   ↓
7. Rank variables by criticality (impact × uncertainty)
   ↓
8. Generate 3-5 ClarificationQuestions for top variables
   ↓
9. Persist baseline hypotheses to hypotheses table
   ↓
10. Return: { hypotheses, clarification_questions }
```

### Clarification (POST /wizard/clarify)

```
1. Load existing hypotheses for simulation
   ↓
2. Parse ClarificationResponses from request
   ↓
3. For each response:
   → Apply distribution adjustments (research.md Decision 3)
   → Update corresponding Hypothesis entity
   ↓
4. Persist updated hypotheses to hypotheses table
   ↓
5. Return: { hypotheses }
```

### Hypothesis Persistence

**Storage**:
- Wizard-generated hypotheses written to `hypotheses` table (same as manual editor)
- No distinction at storage layer between wizard vs manual origin
- Scenario profile and clarification responses NOT stored (ephemeral wizard state)

**Versioning** (optional):
- User can save hypothesis snapshot to `hypothesis_versions` table after wizard completion
- Allows comparing different profile/clarification combinations
- Uses existing `POST /api/simulations/{id}/hypotheses/versions` endpoint

## Migration Strategy

**No migrations required**. All wizard logic uses existing schema.

**Future Enhancement** (if provenance tracking needed):
```sql
-- OPTIONAL: Add generation metadata to hypotheses table
ALTER TABLE hypotheses ADD COLUMN generation_metadata JSONB;

-- Example metadata:
{
  "generation_method": "wizard",
  "wizard_profile": "conservative",
  "wizard_clarifications": [
    { "variable_name": "X", "response": "more" }
  ],
  "generated_at": "2026-01-28T10:30:00Z"
}
```

**Note**: This enhancement is OUT OF SCOPE for initial implementation. Current wizard is provenance-free (same as manual editor).

## Validation Rules

**Hypothesis Validation** (existing):
- `distribution_type` must be valid DistributionType enum
- `distrib_params` schema must match distribution_type (e.g., NormalParams for NORMAL)
- `range_min` < `range_max` if both specified
- Correlations reference existing variables in same simulation

**Wizard-Specific Validation** (new):
- `scenario_profile` must be one of: conservative, realistic, optimistic
- `clarification_responses` length ≤ number of clarification_questions
- `clarification_responses.variable_name` must exist in DAG
- `clarification_responses.response` must be one of: more, less, equal, dont_know

## API Schema Compatibility

**Existing Hypothesis Schema** (api/schemas/hypothesis.py):
```python
class HypothesisSchema(BaseModel):
    id: str
    simulation_id: str
    variable_name: str
    distribution_type: DistributionType
    distrib_params: dict  # Validated by distribution_type
    range_min: float | None = None
    range_max: float | None = None
    correlations: list[CorrelationSchema] | None = None
    scenario_options: list[ScenarioOptionSchema] | None = None
    selected_scenario: str | None = None
    created_at: datetime
    updated_at: datetime
```

**New Wizard Schemas** (to be added to api/schemas/hypothesis.py):
```python
class ScenarioProfileSchema(str, Enum):
    CONSERVATIVE = "conservative"
    REALISTIC = "realistic"
    OPTIMISTIC = "optimistic"

class WizardInitRequest(BaseModel):
    scenario_profile: ScenarioProfileSchema

class ClarificationQuestionSchema(BaseModel):
    variable_name: str
    question_text: str
    criticality_score: float

class WizardInitResponse(BaseModel):
    hypotheses: list[HypothesisSchema]
    clarification_questions: list[ClarificationQuestionSchema]

class ResponseTypeSchema(str, Enum):
    MORE = "more"
    LESS = "less"
    EQUAL = "equal"
    DONT_KNOW = "dont_know"

class ClarificationResponseSchema(BaseModel):
    variable_name: str
    response: ResponseTypeSchema

class WizardClarifyRequest(BaseModel):
    responses: list[ClarificationResponseSchema]

class WizardClarifyResponse(BaseModel):
    hypotheses: list[HypothesisSchema]
```

## Summary

**Zero schema changes**. Wizard is a "smart generator" for existing `Hypothesis` entities:
- Scenario profile → in-memory state (not persisted)
- Clarification questions → generated on-demand from DAG (not persisted)
- Clarification responses → in-memory state (not persisted)
- Final hypotheses → persisted to `hypotheses` table (same as manual editor)

**Benefits**:
- No migration risk
- Full backward compatibility with existing simulation engine
- Wizard and manual editor produce identical data structures
- Simple rollback strategy (just disable wizard UI, existing hypotheses unaffected)

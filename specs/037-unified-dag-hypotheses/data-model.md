# Data Model: Unified DAG & Hypothesis Generation

**Feature**: 037-unified-dag-hypotheses
**Date**: 2026-02-02
**Status**: Phase 1 Design

## Overview

This feature adds one new column (`relevance`) to the existing `hypotheses` table and populates existing unused columns (`range_min`, `range_max`). The unified generation produces DAG + hypotheses in a single LLM call, stored using existing entity structures.

## Database Schema Changes

### Migration: Add `relevance` column

**Table**: `hypotheses` (existing)

```sql
-- Alembic migration
ALTER TABLE hypotheses ADD COLUMN relevance VARCHAR(10) NOT NULL DEFAULT 'medium';
```

**Updated schema** (showing only modified/relevant columns):
```sql
CREATE TABLE hypotheses (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id),
    variable_id TEXT,
    variable_name TEXT NOT NULL,
    distribution_type TEXT NOT NULL,
    distribution_params JSONB NOT NULL,
    range_min REAL,                        -- EXISTS (now populated by unified generation)
    range_max REAL,                        -- EXISTS (now populated by unified generation)
    relevance VARCHAR(10) NOT NULL DEFAULT 'medium',  -- NEW: low, medium, high
    correlations JSONB,
    scenario_options JSONB,
    selected_scenario TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Columns Already Existing (Now Used)

- `range_min REAL`: Lower bound for clamping. Was nullable and unpopulated. Now populated by unified LLM generation. Remains nullable (null = no lower bound).
- `range_max REAL`: Upper bound for clamping. Same as above.

## Domain Entities

### Modified: Hypothesis (domain/entities/hypothesis.py)

```python
class Relevance(str, Enum):
    """Relevância da variável para o resultado da simulação."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Hypothesis:
    id: str                              # hyp_XXXXXXXX
    simulation_id: str                   # sim_XXXXXXXX
    variable_id: str | None              # DAG node ID
    variable_name: str                   # From DAG node
    distribution_type: DistributionType
    parameters: HypothesisParameters     # Union of param types
    relevance: Relevance                 # NEW: low, medium, high (default: medium)
    range_min: float | None              # EXISTING (now populated)
    range_max: float | None              # EXISTING (now populated)
    correlations: list[Correlation] | None
    temporality: Temporality | None
    scenario_options: list[ScenarioOption] | None
    selected_scenario: str | None
    version: int
    created_at: datetime
```

### New: Relevance Enum

```python
class Relevance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
```

### New: UnifiedDAGResponse (LLM structured output)

```python
class LLMHypothesis(BaseModel):
    """Hipótese gerada pelo LLM para uma variável do DAG."""
    variable_name: str
    distribution_type: str
    parameters: dict
    relevance: Literal["low", "medium", "high"]
    range_min: float | None = None
    range_max: float | None = None
    reasoning: str

class UnifiedDAGResponse(BaseModel):
    """Resposta unificada do LLM: DAG + hipóteses."""
    variables: list[LLMVariable]      # 8-20 (existing schema)
    edges: list[LLMEdge]             # (existing schema)
    assumptions: list[LLMAssumption]  # 2-3 (existing schema)
    risks: list[LLMRisk]            # 2-3 (existing schema)
    hypotheses: list[LLMHypothesis]  # 1 per variable (NEW)
```

## Entity Relationships

```
Simulation (existing)
    ↓ 1:1
CausalDAG (existing, unchanged)
    ↓ contains
Variables (existing, in DAG.nodes)
    ↓ 1:1
Hypotheses (existing, modified: +relevance, populated range_min/max)
```

## Data Flow

### Unified Generation (POST /{simulation_id}/confirm-question)

```
1. User confirms question/problem
   ↓
2. Set status = DAG_CONSTRUCTION
   ↓
3. Call UnifiedDAGConstructorService.generate(simulation_id, problem)
   → Single gpt-4o-mini call with extended prompt
   → Returns UnifiedDAGResponse (DAG + hypotheses)
   ↓
4. Validate DAG structure (existing DAGValidator)
   ↓
5. Convert LLM response to domain entities:
   → CausalDAG (nodes, edges, assumptions, risks)
   → list[Hypothesis] (with relevance, range_min, range_max)
   ↓
6. Handle missing hypotheses:
   → For any variable without hypothesis → assign defaults
   → Default: uniform(0,1), relevance=medium, no range
   ↓
7. Persist DAG to causal_dags table
   ↓
8. Persist hypotheses to hypotheses table
   ↓
9. Set status = AWAITING_DAG_VALIDATION
   ↓
10. Return simulation response (DAG + hypotheses available)
```

### Drawer Editing (PUT /hypotheses/{hypothesis_id})

```
1. User opens sheet for a node
   ↓
2. User edits relevance and/or range
   ↓
3. Frontend validates: range_min ≤ range_max (if both provided)
   ↓
4. PUT /hypotheses/{hypothesis_id}
   → Update relevance, range_min, range_max
   ↓
5. Response returns updated hypothesis
   ↓
6. Frontend updates node visual saturation immediately
```

### Range Clamping (during simulation)

```
1. SimulationEngine samples from hypothesis distribution
   ↓
2. DistributionSampler.sample(hypothesis, n)
   → Generate raw samples from distribution
   → Apply np.clip(samples, range_min, range_max)
   → Return clamped samples
```

## API Schema Changes

### Modified: HypothesisSchema (api/schemas/hypothesis.py)

```python
class RelevanceSchema(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class HypothesisSchema(BaseModel):
    # ... existing fields ...
    relevance: RelevanceSchema = RelevanceSchema.MEDIUM  # NEW
    range_min: float | None = None  # EXISTING (now exposed in API)
    range_max: float | None = None  # EXISTING (now exposed in API)
```

### New: HypothesisUpdateRequest (for drawer editing)

```python
class HypothesisUpdateRequest(BaseModel):
    relevance: RelevanceSchema | None = None
    range_min: float | None = None
    range_max: float | None = None
```

## Migration Strategy

**Single Alembic migration**:
1. Add `relevance VARCHAR(10) NOT NULL DEFAULT 'medium'` column
2. Existing rows get `'medium'` (backward compatible — renders at 70% saturation, close to current 100%)

**No migration needed for `range_min`/`range_max`** — columns already exist.

**Domain entity update**: Add `relevance` field with default `Relevance.MEDIUM`.

## Validation Rules

**Existing** (unchanged):
- `distribution_type` must be valid enum
- `distribution_params` schema must match type

**New**:
- `relevance` must be one of: `low`, `medium`, `high`
- If both `range_min` and `range_max` provided: `range_min ≤ range_max`
- `range_min` and `range_max` are independently optional (can set only min or only max)

## Summary

**One migration**: Add `relevance` column with default `'medium'`
**Zero new tables**: All data fits in existing `hypotheses` table
**Backward compatible**: Existing hypotheses default to `medium` relevance, null range (unchanged behavior)
**Minimal entity changes**: One new enum + one new field on Hypothesis dataclass

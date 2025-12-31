# Data Model: Sankey Diagram for Outcome Flow Visualization

**Feature**: 025-sankey-diagram
**Date**: 2025-12-31

## Entities

### SankeyFlowChart (Response Entity)

Main response entity containing all flows for the Sankey diagram.

```python
class SankeyFlowChart(BaseModel):
    """Complete Sankey flow data for visualization."""

    analysis_id: str                    # ana_[a-f0-9]{8}
    nodes: list[SankeyNode]             # All nodes in the diagram
    links: list[SankeyLink]             # All flows between nodes
    total_synths: int                   # Total population count
    outcome_counts: OutcomeCounts       # Aggregated counts per outcome
```

**Validation rules**:
- `analysis_id` must match pattern `ana_[a-f0-9]{8}`
- Sum of Level 1→Level 2 link values must equal `total_synths`
- Sum of Level 2→Level 3 link values for each outcome must equal that outcome's count

### SankeyNode

Represents a node in the Sankey diagram.

```python
class SankeyNode(BaseModel):
    """A node in the Sankey diagram."""

    id: str                             # Unique identifier (e.g., "population", "did_not_try", "trust_gap")
    label: str                          # Display label in Portuguese
    level: Literal[1, 2, 3]             # Diagram level (1=Population, 2=Outcome, 3=Cause)
    color: str                          # Hex color code
    value: int                          # Count of synths at this node
```

**Node types**:

| Level | ID | Label | Color |
|-------|-----|-------|-------|
| 1 | `population` | "População" | `#6366f1` (indigo) |
| 2 | `did_not_try` | "Não tentou" | `#f59e0b` (amber) |
| 2 | `failed` | "Falhou" | `#ef4444` (red) |
| 2 | `success` | "Sucesso" | `#22c55e` (green) |
| 3 | `effort_barrier` | "Esforço inicial alto" | `#fbbf24` |
| 3 | `risk_barrier` | "Risco percebido" | `#fb923c` |
| 3 | `complexity_barrier` | "Complexidade aparente" | `#f97316` |
| 3 | `capability_barrier` | "Capability insuficiente" | `#f87171` |
| 3 | `patience_barrier` | "Desistiu antes do valor" | `#fca5a5` |

### SankeyLink

Represents a flow between two nodes.

```python
class SankeyLink(BaseModel):
    """A flow link between two nodes."""

    source: str                         # Source node ID
    target: str                         # Target node ID
    value: int                          # Number of synths in this flow
```

**Valid link patterns**:
- Level 1→2: `population` → `did_not_try` | `failed` | `success`
- Level 2→3 (did_not_try): `did_not_try` → `effort_barrier` | `risk_barrier` | `complexity_barrier`
- Level 2→3 (failed): `failed` → `capability_barrier` | `patience_barrier`
- Level 2 terminal: `success` has no outgoing links

### OutcomeCounts

Aggregated outcome counts for summary display.

```python
class OutcomeCounts(BaseModel):
    """Aggregated outcome counts."""

    did_not_try: int                    # Count of synths with did_not_try dominant
    failed: int                         # Count of synths with failed dominant
    success: int                        # Count of synths with success dominant
```

### OutcomeDiagnosis (Internal Entity)

Used internally for computing root causes per synth.

```python
class OutcomeDiagnosis(BaseModel):
    """Root cause diagnosis for a single synth."""

    synth_id: str                       # syn_[a-f0-9]{8}
    dominant_outcome: Literal["did_not_try", "failed", "success"]
    root_cause: str | None              # None for success outcomes
    gap_values: dict[str, float]        # All computed gaps for debugging
```

**Root cause mapping**:

For `did_not_try`:
- `motivation_gap` → `"effort_barrier"`
- `trust_gap` → `"risk_barrier"`
- `friction_gap` → `"complexity_barrier"`

For `failed`:
- `capability_gap` → `"capability_barrier"`
- `patience_gap` → `"patience_barrier"`

## Relationships

```
AnalysisRun (1) ─────────────── (1) SankeyFlowChart
     │
     └──────── (1..n) SynthOutcome
                        │
                        └── synth_attributes.latent_traits
                                   │
                                   ├── capability_mean
                                   ├── trust_mean
                                   └── friction_tolerance_mean

Experiment (1) ─────────────── (1) FeatureScorecard
                                        │
                                        ├── complexity.score
                                        ├── initial_effort.score
                                        ├── perceived_risk.score
                                        └── time_to_value.score
```

## Gap Calculation Formulas

### For did_not_try diagnosis

```python
# Motivation approximated by baseline task_criticality (0.5)
motivation = 0.5

gaps = {
    "motivation_gap": scorecard.initial_effort.score - motivation,
    "trust_gap": scorecard.perceived_risk.score - synth.latent_traits.trust_mean,
    "friction_gap": scorecard.complexity.score - synth.latent_traits.friction_tolerance_mean,
}

# Largest positive gap wins (with tie-breaking priority)
root_cause = max(gaps, key=lambda k: (gaps[k], PRIORITY[k]))
```

### For failed diagnosis

```python
gaps = {
    "capability_gap": scorecard.complexity.score - synth.latent_traits.capability_mean,
    "patience_gap": scorecard.time_to_value.score - synth.latent_traits.friction_tolerance_mean,
}

# Largest positive gap wins (with tie-breaking priority)
root_cause = max(gaps, key=lambda k: (gaps[k], PRIORITY[k]))
```

## State Transitions

This feature does not introduce new state transitions. The Sankey data is computed on-demand from existing completed analysis results.

## Data Volume Assumptions

- Typical experiment: 100-500 synths
- Maximum supported: 10,000 synths
- Performance target: < 2 seconds for 10,000 synths
- No pagination required (single aggregated response)

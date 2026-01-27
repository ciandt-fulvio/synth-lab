# Data Model: Causal Simulation System

**Feature**: 035-causal-simulation
**Date**: 2026-01-26
**Status**: Draft

## Overview

This document defines the complete data model for the Causal Simulation System, covering 13 domain entities mapped to 8 database tables with JSONB columns for flexible storage of DAG structures and hypothesis parameters.

## Entity Relationship Diagram

```
┌─────────────┐
│ Simulation  │
└──────┬──────┘
       │ 1
       │
       │ 1
┌──────▼──────────┐         ┌────────────────┐
│  CausalDAG      │◄────────┤   Variable     │
│  (JSONB nodes)  │         │   (embedded)   │
└──────┬──────────┘         └────────────────┘
       │ 1
       │
       │ 1..N
┌──────▼──────────┐         ┌─────────────────┐
│  Hypothesis     │◄────────┤ HypothesisVersion│
│  (JSONB params) │         │ (complete snapshot)│
└──────┬──────────┘         └─────────────────┘
       │ 1
       │
       │ N
┌──────▼─────────────┐      ┌──────────────────┐
│ SimulatedWorld     │──────┤ SyntheticIndividual│
│ (world-level vars) │      │ (user-level vars)  │
└──────┬─────────────┘      └──────────────────┘
       │ N
       │
       │ 1
┌──────▼──────┐
│  Evidence   │
│ (aggregated)│
└──────┬──────┘
       │ 1
       │
       │ N        ┌─────────────┐
       ├──────────┤ FailureMode │
       │          └─────────────┘
       │
       │ N        ┌────────────────────┐
       ├──────────┤ BehavioralCluster  │
       │          └────────────────────┘
       │
       │ N        ┌──────────┐
       └──────────┤ Insight  │
                  └──────┬───┘
                         │ 1
                         │
                         │ 1
                  ┌──────▼──────┐
                  │ AuditTrail  │
                  └─────────────┘
```

## Domain Entities

### 1. Simulation

**Purpose**: Root aggregate representing a complete causal simulation session from question to insights.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^sim_[a-f0-9]{8}$` | Unique identifier |
| `question_text` | string | NOT NULL, max 2000 chars | Original natural language question |
| `problem_decomposition` | JSONB | NOT NULL | Structured problem: intervention, outcomes, time horizon, etc. |
| `status` | enum | NOT NULL | `parsing`, `dag_construction`, `hypothesis_generation`, `simulating`, `completed`, `failed` |
| `created_at` | timestamp | NOT NULL | Creation timestamp |
| `completed_at` | timestamp | nullable | Completion timestamp |
| `error_message` | string | nullable | Error details if status = failed |

**Problem Decomposition JSONB Schema**:
```json
{
  "intervention": "string (what action/change is being evaluated)",
  "primary_outcome": "string (main metric of interest)",
  "secondary_outcomes": ["string (additional metrics)"],
  "unit_of_analysis": "string (e.g., 'user', 'customer', 'transaction')",
  "time_horizon": "string (e.g., '3 months', '1 year')",
  "decision_type": "string (e.g., 'feature_launch', 'pricing_change', 'process_improvement')"
}
```

**Example JSON**:
```json
{
  "id": "sim_a1b2c3d4",
  "question_text": "What will be the adoption rate for a weekly meal subscription?",
  "problem_decomposition": {
    "intervention": "Launch weekly meal subscription service",
    "primary_outcome": "adoption_rate",
    "secondary_outcomes": ["customer_lifetime_value", "churn_rate"],
    "unit_of_analysis": "customer",
    "time_horizon": "6 months",
    "decision_type": "product_launch"
  },
  "status": "completed",
  "created_at": "2026-01-26T10:00:00Z",
  "completed_at": "2026-01-26T10:04:32Z",
  "error_message": null
}
```

---

### 2. CausalDAG

**Purpose**: Directed acyclic graph representing causal relationships between variables.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^dag_[a-f0-9]{8}$` | Unique identifier |
| `simulation_id` | string | FK to Simulation, NOT NULL | Parent simulation |
| `nodes` | JSONB | NOT NULL | Array of Variable objects |
| `edges` | JSONB | NOT NULL | Array of causal relationships |
| `assumptions` | JSONB | NOT NULL | Declared modeling assumptions |
| `risks` | JSONB | NOT NULL | Identified uncertainties |
| `is_validated` | boolean | NOT NULL, default false | Whether DAG passed validation |
| `validation_errors` | JSONB | nullable | Cycle detection, orphan nodes, etc. |
| `version` | integer | NOT NULL, default 1 | Version number for DAG edits |
| `created_at` | timestamp | NOT NULL | Creation timestamp |

**Nodes JSONB Schema** (array of Variable objects):
```json
[
  {
    "id": "string (unique node ID)",
    "name": "string (variable name)",
    "type": "observable | latent | friction | failure | process | temporal",
    "scope": "world | user",
    "description": "string (explanation of variable)",
    "controllability": "none | low | medium | high",
    "is_intervention": "boolean",
    "is_outcome": "boolean"
  }
]
```

**Edges JSONB Schema**:
```json
[
  {
    "from": "string (source node ID)",
    "to": "string (target node ID)",
    "relationship_type": "causal | mediating | confounding | moderating"
  }
]
```

**Assumptions JSONB Schema**:
```json
[
  {
    "assumption": "string (declared assumption)",
    "rationale": "string (why this assumption is necessary)",
    "confidence": "low | medium | high"
  }
]
```

**Risks JSONB Schema**:
```json
[
  {
    "risk": "string (identified risk or uncertainty)",
    "impact": "low | medium | high",
    "mitigation": "string (how to address)"
  }
]
```

**Example JSON**:
```json
{
  "id": "dag_12345678",
  "simulation_id": "sim_a1b2c3d4",
  "nodes": [
    {
      "id": "var_001",
      "name": "marketing_spend",
      "type": "observable",
      "scope": "world",
      "description": "Total marketing budget allocated",
      "controllability": "high",
      "is_intervention": false,
      "is_outcome": false
    },
    {
      "id": "var_002",
      "name": "brand_awareness",
      "type": "latent",
      "scope": "user",
      "description": "User's awareness of the brand",
      "controllability": "medium",
      "is_intervention": false,
      "is_outcome": false
    },
    {
      "id": "var_003",
      "name": "trial_signups",
      "type": "observable",
      "scope": "world",
      "description": "Number of users signing up for trial",
      "controllability": "none",
      "is_intervention": true,
      "is_outcome": false
    },
    {
      "id": "var_004",
      "name": "delivery_reliability",
      "type": "friction",
      "scope": "world",
      "description": "Percentage of on-time deliveries",
      "controllability": "medium",
      "is_intervention": false,
      "is_outcome": false
    },
    {
      "id": "var_005",
      "name": "adoption_rate",
      "type": "observable",
      "scope": "world",
      "description": "Percentage of trial users who adopt subscription",
      "controllability": "none",
      "is_intervention": false,
      "is_outcome": true
    }
  ],
  "edges": [
    {
      "from": "var_001",
      "to": "var_002",
      "relationship_type": "causal"
    },
    {
      "from": "var_002",
      "to": "var_003",
      "relationship_type": "causal"
    },
    {
      "from": "var_003",
      "to": "var_005",
      "relationship_type": "causal"
    },
    {
      "from": "var_004",
      "to": "var_005",
      "relationship_type": "moderating"
    }
  ],
  "assumptions": [
    {
      "assumption": "Marketing spend translates linearly to brand awareness",
      "rationale": "Simplifying assumption for initial model",
      "confidence": "medium"
    },
    {
      "assumption": "No interaction effects between variables beyond declared edges",
      "rationale": "Tractability for simulation",
      "confidence": "low"
    }
  ],
  "risks": [
    {
      "risk": "Delivery reliability may have non-linear impact",
      "impact": "medium",
      "mitigation": "Test sensitivity with different distributions"
    }
  ],
  "is_validated": true,
  "validation_errors": null,
  "version": 1,
  "created_at": "2026-01-26T10:00:15Z"
}
```

---

### 3. Variable

**Purpose**: Individual node in the causal DAG (embedded within CausalDAG.nodes).

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | Unique within DAG | Variable identifier |
| `name` | string | NOT NULL | Human-readable name |
| `type` | enum | NOT NULL | `observable`, `latent`, `friction`, `failure`, `process`, `temporal` |
| `scope` | enum | NOT NULL | `world` (system-level) or `user` (individual-level) |
| `description` | string | NOT NULL | Explanation of variable |
| `controllability` | enum | NOT NULL | `none`, `low`, `medium`, `high` |
| `is_intervention` | boolean | NOT NULL | True if this is the intervention variable |
| `is_outcome` | boolean | NOT NULL | True if this is a primary/secondary outcome |

**Type Definitions**:
- **observable**: Directly measurable (e.g., price, churn_rate)
- **latent**: Not directly measurable (e.g., brand_perception, trust)
- **friction**: Impediments to desired outcome (e.g., delivery_failures, signup_complexity)
- **failure**: Binary failure modes (e.g., payment_declined, stock_outage)
- **process**: Sequential/temporal variables (e.g., onboarding_step, days_since_signup)
- **temporal**: Time-dependent variables (e.g., seasonality, market_maturity)

---

### 4. Hypothesis

**Purpose**: Quantitative parametrization of a variable with distribution, range, and correlations.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^hyp_[a-f0-9]{8}$` | Unique identifier |
| `simulation_id` | string | FK to Simulation, NOT NULL | Parent simulation |
| `variable_id` | string | NOT NULL | References DAG node ID |
| `variable_name` | string | NOT NULL | Cached for convenience |
| `distribution_type` | enum | NOT NULL | `uniform`, `normal`, `beta`, `lognormal`, `bernoulli` |
| `parameters` | JSONB | NOT NULL | Distribution-specific parameters |
| `correlations` | JSONB | nullable | Declared correlations with other variables |
| `temporality` | JSONB | nullable | Time-dependent behavior if applicable |
| `version` | integer | NOT NULL, default 1 | Version for hypothesis edits |
| `created_at` | timestamp | NOT NULL | Creation timestamp |

**Parameters JSONB Schema** (varies by distribution):
```json
// Uniform
{
  "low": "number",
  "high": "number"
}

// Normal
{
  "mean": "number",
  "std": "number"
}

// Beta
{
  "alpha": "number",
  "beta": "number"
}

// Lognormal
{
  "mean": "number",
  "sigma": "number"
}

// Bernoulli
{
  "p": "number (probability)"
}
```

**Correlations JSONB Schema**:
```json
[
  {
    "with_variable_id": "string",
    "with_variable_name": "string",
    "correlation": "number (-1 to 1)",
    "rationale": "string (why this correlation)"
  }
]
```

**Temporality JSONB Schema**:
```json
{
  "type": "linear | exponential | seasonal",
  "parameters": {
    // Type-specific parameters
  }
}
```

**Example JSON**:
```json
{
  "id": "hyp_87654321",
  "simulation_id": "sim_a1b2c3d4",
  "variable_id": "var_005",
  "variable_name": "adoption_rate",
  "distribution_type": "beta",
  "parameters": {
    "alpha": 3.0,
    "beta": 7.0
  },
  "correlations": [
    {
      "with_variable_id": "var_004",
      "with_variable_name": "delivery_reliability",
      "correlation": 0.6,
      "rationale": "Higher reliability strongly predicts higher adoption"
    }
  ],
  "temporality": null,
  "version": 1,
  "created_at": "2026-01-26T10:00:30Z"
}
```

---

### 5. HypothesisVersion

**Purpose**: Named snapshot of complete hypothesis set for scenario planning.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^hv_[a-f0-9]{8}$` | Unique identifier |
| `simulation_id` | string | FK to Simulation, NOT NULL | Parent simulation |
| `name` | string | NOT NULL, max 100 chars | User-provided name (e.g., "Optimistic Case") |
| `description` | string | nullable, max 1000 chars | User-provided description |
| `snapshot` | JSONB | NOT NULL | Complete state of all hypotheses |
| `dag_snapshot` | JSONB | NOT NULL | Complete state of DAG at this version |
| `created_at` | timestamp | NOT NULL | Creation timestamp |

**Snapshot JSONB Schema**:
```json
{
  "hypotheses": [
    // Array of complete Hypothesis objects
  ],
  "dag_version": "integer"
}
```

**Example JSON**:
```json
{
  "id": "hv_abcdef12",
  "simulation_id": "sim_a1b2c3d4",
  "name": "Pessimistic Case",
  "description": "High friction, low delivery reliability, conservative adoption assumptions",
  "snapshot": {
    "hypotheses": [
      {
        "variable_id": "var_004",
        "variable_name": "delivery_reliability",
        "distribution_type": "beta",
        "parameters": {
          "alpha": 2.0,
          "beta": 8.0
        }
      }
    ],
    "dag_version": 1
  },
  "dag_snapshot": {
    "nodes": [],
    "edges": []
  },
  "created_at": "2026-01-26T10:02:00Z"
}
```

---

### 6. SimulatedWorld

**Purpose**: Single execution of simulation with specific parameter draws and outcomes.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^world_[a-f0-9]{8}$` | Unique identifier |
| `simulation_id` | string | FK to Simulation, NOT NULL | Parent simulation |
| `world_number` | integer | NOT NULL | Sequential world number (1-500) |
| `world_parameters` | JSONB | NOT NULL | Sampled world-level variable values |
| `aggregated_outcomes` | JSONB | NOT NULL | Aggregated outcomes across population |
| `random_seed` | integer | NOT NULL | Seed for this world's randomness |
| `created_at` | timestamp | NOT NULL | Creation timestamp |

**World Parameters JSONB Schema**:
```json
{
  "variable_id": "number (sampled value for world-scoped variables)"
}
```

**Aggregated Outcomes JSONB Schema**:
```json
{
  "outcome_name": {
    "mean": "number",
    "std": "number",
    "p5": "number",
    "p50": "number",
    "p95": "number"
  }
}
```

**Example JSON**:
```json
{
  "id": "world_11111111",
  "simulation_id": "sim_a1b2c3d4",
  "world_number": 1,
  "world_parameters": {
    "var_001": 50000.0,
    "var_004": 0.85,
    "var_005": 0.32
  },
  "aggregated_outcomes": {
    "adoption_rate": {
      "mean": 0.31,
      "std": 0.05,
      "p5": 0.23,
      "p50": 0.31,
      "p95": 0.39
    }
  },
  "random_seed": 42001,
  "created_at": "2026-01-26T10:03:00Z"
}
```

---

### 7. SyntheticIndividual

**Purpose**: Individual member within a simulated world with user-scoped attributes (optional, for detailed analysis).

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^ind_[a-f0-9]{8}$` | Unique identifier |
| `world_id` | string | FK to SimulatedWorld, NOT NULL | Parent world |
| `individual_number` | integer | NOT NULL | Sequential number within world (1-100) |
| `attributes` | JSONB | NOT NULL | User-scoped variable values |
| `outcome` | JSONB | NOT NULL | Individual outcome values |

**Note**: This entity is optional for Phase 1. Can be implemented later for detailed drill-down analysis.

**Example JSON**:
```json
{
  "id": "ind_99999999",
  "world_id": "world_11111111",
  "individual_number": 1,
  "attributes": {
    "var_002": 0.75
  },
  "outcome": {
    "adopted": true,
    "adoption_rate": 1.0
  }
}
```

---

### 8. Evidence

**Purpose**: Aggregated statistics from all simulated worlds.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^evd_[a-f0-9]{8}$` | Unique identifier |
| `simulation_id` | string | FK to Simulation, NOT NULL, UNIQUE | One-to-one with simulation |
| `outcome_distributions` | JSONB | NOT NULL | Percentile distributions for outcomes |
| `variance_explained` | JSONB | NOT NULL | Sensitivity analysis results |
| `correlation_matrix` | JSONB | NOT NULL | Correlations between variables and outcomes |
| `created_at` | timestamp | NOT NULL | Creation timestamp |

**Outcome Distributions JSONB Schema**:
```json
{
  "outcome_name": {
    "p5": "number",
    "p25": "number",
    "p50": "number",
    "p75": "number",
    "p95": "number",
    "mean": "number",
    "std": "number"
  }
}
```

**Variance Explained JSONB Schema**:
```json
[
  {
    "variable_name": "string",
    "variance_explained": "number (0-1)",
    "rank": "integer"
  }
]
```

**Correlation Matrix JSONB Schema**:
```json
{
  "variable_name": {
    "outcome_name": "number (correlation coefficient)"
  }
}
```

**Example JSON**:
```json
{
  "id": "evd_22222222",
  "simulation_id": "sim_a1b2c3d4",
  "outcome_distributions": {
    "adoption_rate": {
      "p5": 0.18,
      "p25": 0.25,
      "p50": 0.31,
      "p75": 0.37,
      "p95": 0.45,
      "mean": 0.31,
      "std": 0.08
    }
  },
  "variance_explained": [
    {
      "variable_name": "delivery_reliability",
      "variance_explained": 0.42,
      "rank": 1
    },
    {
      "variable_name": "brand_awareness",
      "variance_explained": 0.28,
      "rank": 2
    }
  ],
  "correlation_matrix": {
    "delivery_reliability": {
      "adoption_rate": 0.65
    },
    "brand_awareness": {
      "adoption_rate": 0.51
    }
  },
  "created_at": "2026-01-26T10:03:30Z"
}
```

---

### 9. FailureMode

**Purpose**: Detected pattern where specific variable conditions predict poor outcomes.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^fm_[a-f0-9]{8}$` | Unique identifier |
| `evidence_id` | string | FK to Evidence, NOT NULL | Parent evidence |
| `pattern` | JSONB | NOT NULL | Conditional pattern (variable ranges) |
| `outcome_threshold` | JSONB | NOT NULL | Outcome threshold that defines failure |
| `frequency` | float | NOT NULL, 0-1 | Percentage of worlds matching pattern |
| `severity` | enum | NOT NULL | `low`, `medium`, `high`, `critical` |
| `description` | string | NOT NULL | Natural language description |
| `created_at` | timestamp | NOT NULL | Creation timestamp |

**Pattern JSONB Schema**:
```json
{
  "variable_name": {
    "operator": "< | <= | > | >= | ==",
    "value": "number"
  }
}
```

**Outcome Threshold JSONB Schema**:
```json
{
  "outcome_name": {
    "operator": "string",
    "value": "number"
  }
}
```

**Example JSON**:
```json
{
  "id": "fm_33333333",
  "evidence_id": "evd_22222222",
  "pattern": {
    "delivery_reliability": {
      "operator": "<",
      "value": 0.70
    }
  },
  "outcome_threshold": {
    "adoption_rate": {
      "operator": "<",
      "value": 0.20
    }
  },
  "frequency": 0.85,
  "severity": "high",
  "description": "When delivery reliability falls below 70%, adoption rate drops below 20% in 85% of simulated worlds",
  "created_at": "2026-01-26T10:03:35Z"
}
```

---

### 10. BehavioralCluster

**Purpose**: Group of simulated worlds with similar variable patterns and outcomes.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^clust_[a-f0-9]{8}$` | Unique identifier |
| `evidence_id` | string | FK to Evidence, NOT NULL | Parent evidence |
| `cluster_number` | integer | NOT NULL | Sequential cluster number (1-N) |
| `world_ids` | JSONB | NOT NULL | Array of world IDs in this cluster |
| `centroid` | JSONB | NOT NULL | Representative variable values |
| `outcome_stats` | JSONB | NOT NULL | Outcome distributions for this cluster |
| `size` | integer | NOT NULL | Number of worlds in cluster |
| `percentage` | float | NOT NULL, 0-1 | Percentage of total worlds |
| `label` | string | NOT NULL | Human-readable cluster label |
| `created_at` | timestamp | NOT NULL | Creation timestamp |

**Centroid JSONB Schema**:
```json
{
  "variable_name": "number (mean value for this cluster)"
}
```

**Outcome Stats JSONB Schema**:
```json
{
  "outcome_name": {
    "mean": "number",
    "std": "number",
    "p50": "number"
  }
}
```

**Example JSON**:
```json
{
  "id": "clust_44444444",
  "evidence_id": "evd_22222222",
  "cluster_number": 1,
  "world_ids": ["world_11111111", "world_11111112"],
  "centroid": {
    "delivery_reliability": 0.92,
    "brand_awareness": 0.68
  },
  "outcome_stats": {
    "adoption_rate": {
      "mean": 0.41,
      "std": 0.03,
      "p50": 0.42
    }
  },
  "size": 127,
  "percentage": 0.254,
  "label": "High reliability + strong brand",
  "created_at": "2026-01-26T10:03:40Z"
}
```

---

### 11. Insight

**Purpose**: Actionable conclusion derived from evidence with full traceability.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^ins_[a-f0-9]{8}$` | Unique identifier |
| `simulation_id` | string | FK to Simulation, NOT NULL | Parent simulation |
| `insight_type` | enum | NOT NULL | `key_driver`, `failure_mode`, `cluster_finding`, `recommendation` |
| `title` | string | NOT NULL, max 200 chars | Brief summary |
| `description` | string | NOT NULL | Detailed explanation |
| `evidence_references` | JSONB | NOT NULL | Pointers to specific evidence |
| `variable_references` | JSONB | NOT NULL | Variables involved in this insight |
| `statistical_support` | JSONB | NOT NULL | Statistical results backing insight |
| `risk_assessment` | JSONB | nullable | Declared risks and counterfactuals |
| `recommended_actions` | JSONB | nullable | Suggested next steps |
| `confidence` | enum | NOT NULL | `low`, `medium`, `high` |
| `created_at` | timestamp | NOT NULL | Creation timestamp |

**Evidence References JSONB Schema**:
```json
{
  "variance_explained_rank": "integer",
  "failure_mode_ids": ["string"],
  "cluster_ids": ["string"],
  "affected_world_ids": ["string"]
}
```

**Variable References JSONB Schema**:
```json
[
  {
    "variable_id": "string",
    "variable_name": "string",
    "role": "driver | mediator | confound | outcome"
  }
]
```

**Statistical Support JSONB Schema**:
```json
{
  "correlation": "number",
  "variance_explained": "number",
  "sample_size": "integer (number of worlds)",
  "p_value": "number (if applicable)"
}
```

**Risk Assessment JSONB Schema**:
```json
{
  "assumptions": ["string"],
  "counterfactuals": ["string"],
  "limitations": ["string"]
}
```

**Recommended Actions JSONB Schema**:
```json
[
  {
    "action_type": "experiment | rollout_strategy | exclusion_criteria | data_collection",
    "description": "string",
    "priority": "low | medium | high"
  }
]
```

**Example JSON**:
```json
{
  "id": "ins_55555555",
  "simulation_id": "sim_a1b2c3d4",
  "insight_type": "key_driver",
  "title": "Delivery reliability is the primary driver of adoption",
  "description": "Delivery reliability explains 42% of variance in adoption rates across simulated scenarios. Worlds with reliability above 85% show median adoption of 38% vs 22% for reliability below 70%.",
  "evidence_references": {
    "variance_explained_rank": 1,
    "failure_mode_ids": ["fm_33333333"],
    "cluster_ids": ["clust_44444444"],
    "affected_world_ids": ["world_11111111"]
  },
  "variable_references": [
    {
      "variable_id": "var_004",
      "variable_name": "delivery_reliability",
      "role": "driver"
    },
    {
      "variable_id": "var_005",
      "variable_name": "adoption_rate",
      "role": "outcome"
    }
  ],
  "statistical_support": {
    "correlation": 0.65,
    "variance_explained": 0.42,
    "sample_size": 500
  },
  "risk_assessment": {
    "assumptions": [
      "Linear relationship between reliability and adoption"
    ],
    "counterfactuals": [
      "Non-linear effects may exist at extreme values"
    ],
    "limitations": [
      "Simulated data, not real customer behavior"
    ]
  },
  "recommended_actions": [
    {
      "action_type": "experiment",
      "description": "A/B test delivery SLA guarantees (95% vs 85% on-time)",
      "priority": "high"
    },
    {
      "action_type": "exclusion_criteria",
      "description": "Avoid launching in regions with delivery reliability < 75%",
      "priority": "medium"
    }
  ],
  "confidence": "high",
  "created_at": "2026-01-26T10:04:00Z"
}
```

---

### 12. AuditTrail

**Purpose**: Complete reproducibility record for any simulation run.

**Attributes**:

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | string | PK, pattern: `^audit_[a-f0-9]{8}$` | Unique identifier |
| `simulation_id` | string | FK to Simulation, NOT NULL, UNIQUE | One-to-one with simulation |
| `question_hash` | string | NOT NULL | Hash of original question |
| `dag_snapshot` | JSONB | NOT NULL | Complete DAG at time of simulation |
| `hypothesis_snapshot` | JSONB | NOT NULL | Complete hypotheses at time of simulation |
| `random_seed` | integer | NOT NULL | Master random seed for reproducibility |
| `llm_prompts` | JSONB | NOT NULL | All LLM prompts and responses |
| `execution_metadata` | JSONB | NOT NULL | Environment, versions, timestamps |
| `created_at` | timestamp | NOT NULL | Creation timestamp |

**LLM Prompts JSONB Schema**:
```json
[
  {
    "stage": "question_parsing | dag_generation | hypothesis_generation | insight_generation",
    "prompt": "string",
    "response": "string",
    "model": "string",
    "timestamp": "string"
  }
]
```

**Execution Metadata JSONB Schema**:
```json
{
  "python_version": "string",
  "numpy_version": "string",
  "networkx_version": "string",
  "start_time": "timestamp",
  "end_time": "timestamp",
  "total_duration_seconds": "number"
}
```

**Example JSON**:
```json
{
  "id": "audit_66666666",
  "simulation_id": "sim_a1b2c3d4",
  "question_hash": "sha256:abcdef...",
  "dag_snapshot": {},
  "hypothesis_snapshot": {},
  "random_seed": 42,
  "llm_prompts": [
    {
      "stage": "question_parsing",
      "prompt": "Extract structured problem from: What will be...",
      "response": "{\"intervention\": \"Launch weekly meal...\"}",
      "model": "gpt-4.1",
      "timestamp": "2026-01-26T10:00:05Z"
    }
  ],
  "execution_metadata": {
    "python_version": "3.13.1",
    "numpy_version": "1.26.4",
    "networkx_version": "3.2.1",
    "start_time": "2026-01-26T10:00:00Z",
    "end_time": "2026-01-26T10:04:32Z",
    "total_duration_seconds": 272.5
  },
  "created_at": "2026-01-26T10:04:32Z"
}
```

---

## Database Schema Design

### PostgreSQL Tables (8 total)

#### Table: `simulations`
```sql
CREATE TABLE simulations (
    id VARCHAR(20) PRIMARY KEY,  -- sim_[a-f0-9]{8}
    question_text TEXT NOT NULL CHECK (char_length(question_text) <= 2000),
    problem_decomposition JSONB NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('parsing', 'dag_construction', 'hypothesis_generation', 'simulating', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

CREATE INDEX idx_simulations_status ON simulations(status);
CREATE INDEX idx_simulations_created_at ON simulations(created_at DESC);
```

#### Table: `causal_dags`
```sql
CREATE TABLE causal_dags (
    id VARCHAR(20) PRIMARY KEY,  -- dag_[a-f0-9]{8}
    simulation_id VARCHAR(20) NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,
    assumptions JSONB NOT NULL,
    risks JSONB NOT NULL,
    is_validated BOOLEAN NOT NULL DEFAULT FALSE,
    validation_errors JSONB,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_causal_dags_simulation_id ON causal_dags(simulation_id);
CREATE INDEX idx_causal_dags_version ON causal_dags(simulation_id, version DESC);
```

#### Table: `hypotheses`
```sql
CREATE TABLE hypotheses (
    id VARCHAR(20) PRIMARY KEY,  -- hyp_[a-f0-9]{8}
    simulation_id VARCHAR(20) NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    variable_id VARCHAR(50) NOT NULL,
    variable_name VARCHAR(200) NOT NULL,
    distribution_type VARCHAR(50) NOT NULL CHECK (distribution_type IN ('uniform', 'normal', 'beta', 'lognormal', 'bernoulli')),
    parameters JSONB NOT NULL,
    correlations JSONB,
    temporality JSONB,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_hypotheses_simulation_id ON hypotheses(simulation_id);
CREATE INDEX idx_hypotheses_variable_id ON hypotheses(simulation_id, variable_id);
```

#### Table: `hypothesis_versions`
```sql
CREATE TABLE hypothesis_versions (
    id VARCHAR(20) PRIMARY KEY,  -- hv_[a-f0-9]{8}
    simulation_id VARCHAR(20) NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT CHECK (char_length(description) <= 1000),
    snapshot JSONB NOT NULL,
    dag_snapshot JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_hypothesis_versions_simulation_id ON hypothesis_versions(simulation_id);
CREATE INDEX idx_hypothesis_versions_name ON hypothesis_versions(simulation_id, name);
```

#### Table: `simulated_worlds`
```sql
CREATE TABLE simulated_worlds (
    id VARCHAR(20) PRIMARY KEY,  -- world_[a-f0-9]{8}
    simulation_id VARCHAR(20) NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    world_number INTEGER NOT NULL,
    world_parameters JSONB NOT NULL,
    aggregated_outcomes JSONB NOT NULL,
    random_seed INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(simulation_id, world_number)
);

CREATE INDEX idx_simulated_worlds_simulation_id ON simulated_worlds(simulation_id);
CREATE INDEX idx_simulated_worlds_number ON simulated_worlds(simulation_id, world_number);
```

#### Table: `evidence`
```sql
CREATE TABLE evidence (
    id VARCHAR(20) PRIMARY KEY,  -- evd_[a-f0-9]{8}
    simulation_id VARCHAR(20) NOT NULL UNIQUE REFERENCES simulations(id) ON DELETE CASCADE,
    outcome_distributions JSONB NOT NULL,
    variance_explained JSONB NOT NULL,
    correlation_matrix JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evidence_simulation_id ON evidence(simulation_id);
```

#### Table: `failure_modes` (child of evidence)
```sql
CREATE TABLE failure_modes (
    id VARCHAR(20) PRIMARY KEY,  -- fm_[a-f0-9]{8}
    evidence_id VARCHAR(20) NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    pattern JSONB NOT NULL,
    outcome_threshold JSONB NOT NULL,
    frequency FLOAT NOT NULL CHECK (frequency >= 0 AND frequency <= 1),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_failure_modes_evidence_id ON failure_modes(evidence_id);
CREATE INDEX idx_failure_modes_severity ON failure_modes(evidence_id, severity);
```

#### Table: `behavioral_clusters` (child of evidence)
```sql
CREATE TABLE behavioral_clusters (
    id VARCHAR(20) PRIMARY KEY,  -- clust_[a-f0-9]{8}
    evidence_id VARCHAR(20) NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    cluster_number INTEGER NOT NULL,
    world_ids JSONB NOT NULL,
    centroid JSONB NOT NULL,
    outcome_stats JSONB NOT NULL,
    size INTEGER NOT NULL,
    percentage FLOAT NOT NULL CHECK (percentage >= 0 AND percentage <= 1),
    label VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(evidence_id, cluster_number)
);

CREATE INDEX idx_behavioral_clusters_evidence_id ON behavioral_clusters(evidence_id);
```

#### Table: `insights`
```sql
CREATE TABLE insights (
    id VARCHAR(20) PRIMARY KEY,  -- ins_[a-f0-9]{8}
    simulation_id VARCHAR(20) NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL CHECK (insight_type IN ('key_driver', 'failure_mode', 'cluster_finding', 'recommendation')),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    evidence_references JSONB NOT NULL,
    variable_references JSONB NOT NULL,
    statistical_support JSONB NOT NULL,
    risk_assessment JSONB,
    recommended_actions JSONB,
    confidence VARCHAR(20) NOT NULL CHECK (confidence IN ('low', 'medium', 'high')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_insights_simulation_id ON insights(simulation_id);
CREATE INDEX idx_insights_type ON insights(simulation_id, insight_type);
CREATE INDEX idx_insights_confidence ON insights(confidence);
```

#### Table: `audit_trails`
```sql
CREATE TABLE audit_trails (
    id VARCHAR(20) PRIMARY KEY,  -- audit_[a-f0-9]{8}
    simulation_id VARCHAR(20) NOT NULL UNIQUE REFERENCES simulations(id) ON DELETE CASCADE,
    question_hash VARCHAR(100) NOT NULL,
    dag_snapshot JSONB NOT NULL,
    hypothesis_snapshot JSONB NOT NULL,
    random_seed INTEGER NOT NULL,
    llm_prompts JSONB NOT NULL,
    execution_metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_trails_simulation_id ON audit_trails(simulation_id);
CREATE INDEX idx_audit_trails_question_hash ON audit_trails(question_hash);
```

---

## SQLAlchemy ORM Models

### Example: Simulation Model

```python
"""
Simulation entity ORM model.

SQLAlchemy model for simulations table.
"""

import secrets
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Text, Enum as SQLEnum, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from synth_lab.infrastructure.database import Base


def generate_simulation_id() -> str:
    """Generate simulation ID with sim_ prefix and 8-char hex suffix."""
    return f"sim_{secrets.token_hex(4)}"


class SimulationStatus(str, Enum):
    """Status of simulation."""
    PARSING = "parsing"
    DAG_CONSTRUCTION = "dag_construction"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    SIMULATING = "simulating"
    COMPLETED = "completed"
    FAILED = "failed"


class Simulation(Base):
    """
    Simulation ORM model.

    Represents root aggregate for causal simulation session.
    """
    __tablename__ = "simulations"

    id = Column(String(20), primary_key=True, default=generate_simulation_id)
    question_text = Column(Text, nullable=False)
    problem_decomposition = Column(JSONB, nullable=False)
    status = Column(SQLEnum(SimulationStatus), nullable=False, default=SimulationStatus.PARSING)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    causal_dag = relationship("CausalDAG", back_populates="simulation", uselist=False, cascade="all, delete-orphan")
    hypotheses = relationship("Hypothesis", back_populates="simulation", cascade="all, delete-orphan")
    hypothesis_versions = relationship("HypothesisVersion", back_populates="simulation", cascade="all, delete-orphan")
    simulated_worlds = relationship("SimulatedWorld", back_populates="simulation", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="simulation", cascade="all, delete-orphan")
    audit_trail = relationship("AuditTrail", back_populates="simulation", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("char_length(question_text) <= 2000", name="question_text_length"),
    )
```

### Example: CausalDAG Model

```python
"""
CausalDAG entity ORM model.

SQLAlchemy model for causal_dags table.
"""

import secrets
from datetime import datetime, timezone

from sqlalchemy import Column, String, ForeignKey, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from synth_lab.infrastructure.database import Base


def generate_dag_id() -> str:
    """Generate DAG ID with dag_ prefix and 8-char hex suffix."""
    return f"dag_{secrets.token_hex(4)}"


class CausalDAG(Base):
    """
    CausalDAG ORM model.

    Represents directed acyclic graph of causal relationships.
    """
    __tablename__ = "causal_dags"

    id = Column(String(20), primary_key=True, default=generate_dag_id)
    simulation_id = Column(String(20), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    nodes = Column(JSONB, nullable=False)
    edges = Column(JSONB, nullable=False)
    assumptions = Column(JSONB, nullable=False)
    risks = Column(JSONB, nullable=False)
    is_validated = Column(Boolean, nullable=False, default=False)
    validation_errors = Column(JSONB, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    simulation = relationship("Simulation", back_populates="causal_dag")
```

---

## Usage Notes

1. **JSONB Indexing**: For frequently queried JSONB fields, add GIN indexes:
   ```sql
   CREATE INDEX idx_dag_nodes_gin ON causal_dags USING GIN (nodes);
   ```

2. **Cascading Deletes**: All child entities cascade on simulation deletion for clean cleanup.

3. **Versioning**: DAG and Hypothesis versions track iterative refinement by users.

4. **Traceability**: Every Insight must reference Evidence via `evidence_references` JSONB.

5. **Reproducibility**: AuditTrail stores complete state for exact replay via `random_seed`.

6. **Performance**: For 500 worlds, use bulk inserts via `executemany()` in repositories.

7. **JSONB Validation**: Use Pydantic models to validate JSONB structure before database insertion.

---

## Migration Script

```python
"""
Alembic migration for causal simulation tables.

Revision ID: 20260126_0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Create causal simulation tables."""

    # simulations
    op.create_table(
        'simulations',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('problem_decomposition', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.CheckConstraint("char_length(question_text) <= 2000", name='question_text_length'),
        sa.CheckConstraint("status IN ('parsing', 'dag_construction', 'hypothesis_generation', 'simulating', 'completed', 'failed')", name='status_enum')
    )
    op.create_index('idx_simulations_status', 'simulations', ['status'])
    op.create_index('idx_simulations_created_at', 'simulations', [sa.text('created_at DESC')])

    # causal_dags
    op.create_table(
        'causal_dags',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('simulation_id', sa.String(20), sa.ForeignKey('simulations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nodes', postgresql.JSONB(), nullable=False),
        sa.Column('edges', postgresql.JSONB(), nullable=False),
        sa.Column('assumptions', postgresql.JSONB(), nullable=False),
        sa.Column('risks', postgresql.JSONB(), nullable=False),
        sa.Column('is_validated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('validation_errors', postgresql.JSONB(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('idx_causal_dags_simulation_id', 'causal_dags', ['simulation_id'])
    op.create_index('idx_causal_dags_version', 'causal_dags', ['simulation_id', sa.text('version DESC')])

    # hypotheses
    op.create_table(
        'hypotheses',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('simulation_id', sa.String(20), sa.ForeignKey('simulations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('variable_id', sa.String(50), nullable=False),
        sa.Column('variable_name', sa.String(200), nullable=False),
        sa.Column('distribution_type', sa.String(50), nullable=False),
        sa.Column('parameters', postgresql.JSONB(), nullable=False),
        sa.Column('correlations', postgresql.JSONB(), nullable=True),
        sa.Column('temporality', postgresql.JSONB(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("distribution_type IN ('uniform', 'normal', 'beta', 'lognormal', 'bernoulli')", name='distribution_type_enum')
    )
    op.create_index('idx_hypotheses_simulation_id', 'hypotheses', ['simulation_id'])
    op.create_index('idx_hypotheses_variable_id', 'hypotheses', ['simulation_id', 'variable_id'])

    # hypothesis_versions
    op.create_table(
        'hypothesis_versions',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('simulation_id', sa.String(20), sa.ForeignKey('simulations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('dag_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("char_length(description) <= 1000", name='description_length')
    )
    op.create_index('idx_hypothesis_versions_simulation_id', 'hypothesis_versions', ['simulation_id'])
    op.create_index('idx_hypothesis_versions_name', 'hypothesis_versions', ['simulation_id', 'name'])

    # simulated_worlds
    op.create_table(
        'simulated_worlds',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('simulation_id', sa.String(20), sa.ForeignKey('simulations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('world_number', sa.Integer(), nullable=False),
        sa.Column('world_parameters', postgresql.JSONB(), nullable=False),
        sa.Column('aggregated_outcomes', postgresql.JSONB(), nullable=False),
        sa.Column('random_seed', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('simulation_id', 'world_number', name='uq_simulation_world_number')
    )
    op.create_index('idx_simulated_worlds_simulation_id', 'simulated_worlds', ['simulation_id'])
    op.create_index('idx_simulated_worlds_number', 'simulated_worlds', ['simulation_id', 'world_number'])

    # evidence
    op.create_table(
        'evidence',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('simulation_id', sa.String(20), sa.ForeignKey('simulations.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('outcome_distributions', postgresql.JSONB(), nullable=False),
        sa.Column('variance_explained', postgresql.JSONB(), nullable=False),
        sa.Column('correlation_matrix', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('idx_evidence_simulation_id', 'evidence', ['simulation_id'])

    # failure_modes
    op.create_table(
        'failure_modes',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('evidence_id', sa.String(20), sa.ForeignKey('evidence.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pattern', postgresql.JSONB(), nullable=False),
        sa.Column('outcome_threshold', postgresql.JSONB(), nullable=False),
        sa.Column('frequency', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("frequency >= 0 AND frequency <= 1", name='frequency_range'),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name='severity_enum')
    )
    op.create_index('idx_failure_modes_evidence_id', 'failure_modes', ['evidence_id'])
    op.create_index('idx_failure_modes_severity', 'failure_modes', ['evidence_id', 'severity'])

    # behavioral_clusters
    op.create_table(
        'behavioral_clusters',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('evidence_id', sa.String(20), sa.ForeignKey('evidence.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cluster_number', sa.Integer(), nullable=False),
        sa.Column('world_ids', postgresql.JSONB(), nullable=False),
        sa.Column('centroid', postgresql.JSONB(), nullable=False),
        sa.Column('outcome_stats', postgresql.JSONB(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('percentage', sa.Float(), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("percentage >= 0 AND percentage <= 1", name='percentage_range'),
        sa.UniqueConstraint('evidence_id', 'cluster_number', name='uq_evidence_cluster_number')
    )
    op.create_index('idx_behavioral_clusters_evidence_id', 'behavioral_clusters', ['evidence_id'])

    # insights
    op.create_table(
        'insights',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('simulation_id', sa.String(20), sa.ForeignKey('simulations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('insight_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_references', postgresql.JSONB(), nullable=False),
        sa.Column('variable_references', postgresql.JSONB(), nullable=False),
        sa.Column('statistical_support', postgresql.JSONB(), nullable=False),
        sa.Column('risk_assessment', postgresql.JSONB(), nullable=True),
        sa.Column('recommended_actions', postgresql.JSONB(), nullable=True),
        sa.Column('confidence', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("insight_type IN ('key_driver', 'failure_mode', 'cluster_finding', 'recommendation')", name='insight_type_enum'),
        sa.CheckConstraint("confidence IN ('low', 'medium', 'high')", name='confidence_enum')
    )
    op.create_index('idx_insights_simulation_id', 'insights', ['simulation_id'])
    op.create_index('idx_insights_type', 'insights', ['simulation_id', 'insight_type'])
    op.create_index('idx_insights_confidence', 'insights', ['confidence'])

    # audit_trails
    op.create_table(
        'audit_trails',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('simulation_id', sa.String(20), sa.ForeignKey('simulations.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('question_hash', sa.String(100), nullable=False),
        sa.Column('dag_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('hypothesis_snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('random_seed', sa.Integer(), nullable=False),
        sa.Column('llm_prompts', postgresql.JSONB(), nullable=False),
        sa.Column('execution_metadata', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('idx_audit_trails_simulation_id', 'audit_trails', ['simulation_id'])
    op.create_index('idx_audit_trails_question_hash', 'audit_trails', ['question_hash'])


def downgrade() -> None:
    """Drop causal simulation tables."""
    op.drop_table('audit_trails')
    op.drop_table('insights')
    op.drop_table('behavioral_clusters')
    op.drop_table('failure_modes')
    op.drop_table('evidence')
    op.drop_table('simulated_worlds')
    op.drop_table('hypothesis_versions')
    op.drop_table('hypotheses')
    op.drop_table('causal_dags')
    op.drop_table('simulations')
```

---

## Summary

This data model provides:

1. **Complete traceability**: Every insight traces back to evidence, variables, and assumptions
2. **Versioning**: DAG and hypothesis changes are tracked for scenario planning
3. **Reproducibility**: Audit trail enables exact replay via random seed
4. **Flexibility**: JSONB columns allow schema evolution without migrations
5. **Performance**: Indexes on critical query patterns (simulation_id, status, etc.)
6. **Referential integrity**: Cascading deletes maintain consistency
7. **Type safety**: Enums and constraints enforce valid states

Total storage estimate for 500-world simulation: ~5-10 MB per simulation (mostly worlds and evidence).

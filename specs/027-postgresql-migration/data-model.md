# Data Model: PostgreSQL Migration

**Feature Branch**: `027-postgresql-migration`
**Date**: 2026-01-01
**Status**: Complete

## Overview

This document defines SQLAlchemy ORM models for all 17 active database tables (plus 2 legacy tables) in the synth-lab application. Models are organized into logical modules and use cross-database compatible types.

## Model Organization

```text
src/synth_lab/models/
├── __init__.py          # Exports all models
├── base.py              # DeclarativeBase, mixins, custom types
├── experiment.py        # Experiment, InterviewGuide
├── synth.py             # Synth, SynthGroup
├── analysis.py          # AnalysisRun, SynthOutcome, AnalysisCache
├── research.py          # ResearchExecution, Transcript
├── exploration.py       # Exploration, ScenarioNode
├── insight.py           # ChartInsight, SensitivityResult, RegionAnalysis
├── document.py          # ExperimentDocument
└── legacy.py            # FeatureScorecard, SimulationRun (deprecated)
```

---

## Base Module

### base.py

```python
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Cross-database JSON type: JSONB on PostgreSQL, JSON on SQLite
JSONVariant = JSON().with_variant(JSONB(), "postgresql")
MutableJSON = MutableDict.as_mutable(JSONVariant)
MutableJSONList = MutableList.as_mutable(JSONVariant)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at: Mapped[str] = mapped_column(String(30), nullable=False)
    updated_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
```

---

## Entity Models

### 1. Experiment (experiments)

**Module**: `experiment.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID-style identifier |
| name | TEXT | NOT NULL, length <= 100 | Experiment name |
| hypothesis | TEXT | NOT NULL, length <= 500 | Research hypothesis |
| description | TEXT | length <= 2000 | Optional detailed description |
| scorecard_data | JSON | Valid JSON or NULL | Embedded scorecard configuration |
| status | TEXT | NOT NULL, DEFAULT 'active' | 'active' or 'deleted' (soft delete) |
| created_at | TEXT | NOT NULL | ISO timestamp |
| updated_at | TEXT | | ISO timestamp |

**Relationships**:
- `analysis_runs` (1:1) - Each experiment has at most one analysis run
- `interview_guide` (1:1) - Optional interview guide
- `research_executions` (1:N) - Multiple research executions
- `explorations` (1:N) - Multiple explorations
- `documents` (1:N) - Multiple documents (summary, prfaq, etc.)

**Indexes**:
- `idx_experiments_created` (created_at DESC)
- `idx_experiments_name` (name)
- `idx_experiments_status` (status)

---

### 2. AnalysisRun (analysis_runs)

**Module**: `analysis.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID-style identifier |
| experiment_id | TEXT | NOT NULL, UNIQUE, FK | Links to experiment (1:1) |
| scenario_id | TEXT | NOT NULL, DEFAULT 'baseline' | Scenario identifier |
| config | JSON | NOT NULL, valid JSON | Analysis configuration |
| status | TEXT | NOT NULL, DEFAULT 'pending' | pending/running/completed/failed |
| started_at | TEXT | NOT NULL | ISO timestamp |
| completed_at | TEXT | | ISO timestamp |
| total_synths | INTEGER | DEFAULT 0 | Number of synths analyzed |
| aggregated_outcomes | JSON | Valid JSON or NULL | Aggregated results |
| execution_time_seconds | REAL | | Total execution time |

**Relationships**:
- `experiment` (N:1) - Parent experiment
- `synth_outcomes` (1:N) - Individual synth results
- `analysis_cache` (1:N) - Cached chart data

**Indexes**:
- `idx_analysis_runs_experiment` (experiment_id)
- `idx_analysis_runs_status` (status)

---

### 3. SynthOutcome (synth_outcomes)

**Module**: `analysis.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID-style identifier |
| analysis_id | TEXT | NOT NULL, FK | Links to analysis run |
| synth_id | TEXT | NOT NULL | Links to synth |
| did_not_try_rate | REAL | NOT NULL | Rate of "did not try" |
| failed_rate | REAL | NOT NULL | Failure rate |
| success_rate | REAL | NOT NULL | Success rate |
| synth_attributes | JSON | Valid JSON | Synth attribute snapshot |

**Constraints**:
- UNIQUE(analysis_id, synth_id)

**Indexes**:
- `idx_outcomes_analysis` (analysis_id)

---

### 4. SynthGroup (synth_groups)

**Module**: `synth.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | Group identifier |
| name | TEXT | NOT NULL | Group name |
| description | TEXT | | Group description |
| created_at | TEXT | NOT NULL | ISO timestamp |

**Relationships**:
- `synths` (1:N) - Synths in this group

**Indexes**:
- `idx_synth_groups_created` (created_at DESC)

---

### 5. Synth (synths)

**Module**: `synth.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID-style identifier |
| synth_group_id | TEXT | FK | Optional group reference |
| nome | TEXT | NOT NULL | Synth name (Portuguese) |
| descricao | TEXT | | Description (Portuguese) |
| link_photo | TEXT | | External photo URL |
| avatar_path | TEXT | | Local avatar file path |
| created_at | TEXT | NOT NULL | ISO timestamp |
| version | TEXT | DEFAULT '2.0.0' | Schema version |
| data | JSON | Valid JSON or NULL | All synth attributes |

**Relationships**:
- `synth_group` (N:1) - Parent group

**Indexes**:
- `idx_synths_created_at` (created_at DESC)
- `idx_synths_nome` (nome)
- `idx_synths_group` (synth_group_id)

---

### 6. ResearchExecution (research_executions)

**Module**: `research.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| exec_id | TEXT | PRIMARY KEY | Execution identifier |
| experiment_id | TEXT | FK | Optional experiment reference |
| topic_name | TEXT | NOT NULL | Research topic |
| status | TEXT | NOT NULL, DEFAULT 'pending' | Status enum |
| synth_count | INTEGER | NOT NULL, DEFAULT 0 | Total synths |
| successful_count | INTEGER | DEFAULT 0 | Successful interviews |
| failed_count | INTEGER | DEFAULT 0 | Failed interviews |
| model | TEXT | DEFAULT 'gpt-4o-mini' | LLM model used |
| max_turns | INTEGER | DEFAULT 6 | Maximum conversation turns |
| started_at | TEXT | NOT NULL | ISO timestamp |
| completed_at | TEXT | | ISO timestamp |
| additional_context | TEXT | | Extra context for interviews |

**Status values**: pending, running, generating_summary, completed, failed

**Relationships**:
- `experiment` (N:1) - Parent experiment (optional)
- `transcripts` (1:N) - Interview transcripts

**Indexes**:
- `idx_executions_topic` (topic_name)
- `idx_executions_status` (status)
- `idx_executions_started` (started_at DESC)
- `idx_executions_experiment` (experiment_id)

---

### 7. Transcript (transcripts)

**Module**: `research.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | Transcript identifier |
| exec_id | TEXT | NOT NULL, FK | Research execution |
| synth_id | TEXT | NOT NULL | Synth identifier |
| synth_name | TEXT | NOT NULL | Synth name snapshot |
| status | TEXT | NOT NULL, DEFAULT 'pending' | Status |
| turn_count | INTEGER | DEFAULT 0 | Number of turns |
| timestamp | TEXT | NOT NULL | ISO timestamp |
| messages | JSON | Valid JSON | Conversation messages |

**Constraints**:
- UNIQUE(exec_id, synth_id)

**Indexes**:
- `idx_transcripts_exec` (exec_id)
- `idx_transcripts_synth` (synth_id)

---

### 8. InterviewGuide (interview_guide)

**Module**: `experiment.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| experiment_id | TEXT | PRIMARY KEY, FK | 1:1 with experiment |
| context_definition | TEXT | | Interview context |
| questions | TEXT | | Interview questions |
| context_examples | TEXT | | Example contexts |
| created_at | TEXT | NOT NULL | ISO timestamp |
| updated_at | TEXT | | ISO timestamp |

**Relationships**:
- `experiment` (1:1) - Parent experiment

---

### 9. AnalysisCache (analysis_cache)

**Module**: `analysis.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| analysis_id | TEXT | PK (composite), FK | Analysis run |
| cache_key | TEXT | PK (composite) | Cache key |
| data | JSON | NOT NULL, valid JSON | Cached data |
| params | JSON | Valid JSON or NULL | Cache parameters |
| computed_at | TEXT | NOT NULL | ISO timestamp |

**Indexes**:
- `idx_analysis_cache_analysis` (analysis_id)

---

### 10. ChartInsight (chart_insights)

**Module**: `insight.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | Insight identifier |
| simulation_id | TEXT | NOT NULL | Simulation/analysis ID |
| insight_type | TEXT | NOT NULL | Type of insight |
| response_json | JSON | NOT NULL, valid JSON | LLM response |
| created_at | TEXT | NOT NULL | ISO timestamp |
| updated_at | TEXT | NOT NULL | ISO timestamp |

**Constraints**:
- UNIQUE(simulation_id, insight_type)

**Indexes**:
- `idx_chart_insights_simulation` (simulation_id)
- `idx_chart_insights_type` (insight_type)

---

### 11. SensitivityResult (sensitivity_results)

**Module**: `insight.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | Result identifier |
| simulation_id | TEXT | NOT NULL, FK | Simulation run |
| analyzed_at | TEXT | NOT NULL | Analysis timestamp |
| deltas_used | JSON | NOT NULL, valid JSON | Delta values used |
| baseline_success | REAL | NOT NULL | Baseline success rate |
| most_sensitive_dimension | TEXT | NOT NULL | Most impactful dimension |
| dimensions | JSON | NOT NULL, valid JSON | All dimension results |
| created_at | TEXT | NOT NULL | ISO timestamp |

**Indexes**:
- `idx_sensitivity_simulation` (simulation_id)
- `idx_sensitivity_analyzed_at` (analyzed_at)

---

### 12. RegionAnalysis (region_analyses)

**Module**: `insight.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | Analysis identifier |
| simulation_id | TEXT | NOT NULL, FK | Simulation run |
| rules | JSON | NOT NULL, valid JSON | Region rules |
| rule_text | TEXT | NOT NULL | Human-readable rules |
| synth_count | INTEGER | NOT NULL | Synths in region |
| synth_percentage | REAL | NOT NULL | Percentage of total |
| did_not_try_rate | REAL | NOT NULL | Region DNT rate |
| failed_rate | REAL | NOT NULL | Region failure rate |
| success_rate | REAL | NOT NULL | Region success rate |
| failure_delta | REAL | NOT NULL | Delta from baseline |

**Indexes**:
- `idx_regions_simulation` (simulation_id)

---

### 13. Exploration (explorations)

**Module**: `exploration.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | Format: expl_[8 hex chars] |
| experiment_id | TEXT | NOT NULL, FK | Parent experiment |
| baseline_analysis_id | TEXT | NOT NULL, FK | Starting analysis |
| goal | JSON | NOT NULL, valid JSON | Exploration goal |
| config | JSON | NOT NULL, valid JSON | Configuration |
| status | TEXT | NOT NULL, DEFAULT 'running' | Status enum |
| current_depth | INTEGER | NOT NULL, DEFAULT 0 | Current tree depth |
| total_nodes | INTEGER | NOT NULL, DEFAULT 0 | Total nodes explored |
| total_llm_calls | INTEGER | NOT NULL, DEFAULT 0 | LLM API calls |
| best_success_rate | REAL | | Best rate found |
| started_at | TEXT | NOT NULL | ISO timestamp |
| completed_at | TEXT | | ISO timestamp |

**Status values**: running, goal_achieved, depth_limit_reached, cost_limit_reached, no_viable_paths

**Relationships**:
- `experiment` (N:1) - Parent experiment
- `baseline_analysis` (N:1) - Starting analysis run
- `nodes` (1:N) - Scenario nodes

**Indexes**:
- `idx_explorations_experiment` (experiment_id)
- `idx_explorations_status` (status)

---

### 14. ScenarioNode (scenario_nodes)

**Module**: `exploration.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | Format: node_[8 hex chars] |
| exploration_id | TEXT | NOT NULL, FK | Parent exploration |
| parent_id | TEXT | FK (self) | Parent node (tree) |
| depth | INTEGER | NOT NULL, >= 0 | Tree depth |
| action_applied | TEXT | | Action description |
| action_category | TEXT | | Action category |
| rationale | TEXT | | Why this action |
| short_action | TEXT | | Brief action summary |
| scorecard_params | JSON | NOT NULL, valid JSON | Scorecard parameters |
| simulation_results | JSON | Valid JSON or NULL | Simulation results |
| execution_time_seconds | REAL | >= 0 | Node execution time |
| node_status | TEXT | NOT NULL, DEFAULT 'active' | Status enum |
| created_at | TEXT | NOT NULL | ISO timestamp |

**Status values**: active, dominated, winner, expansion_failed

**Relationships**:
- `exploration` (N:1) - Parent exploration
- `parent` (N:1) - Parent node (self-referential)
- `children` (1:N) - Child nodes

**Indexes**:
- `idx_scenario_nodes_exploration` (exploration_id)
- `idx_scenario_nodes_parent` (parent_id)
- `idx_scenario_nodes_status` (exploration_id, node_status)
- `idx_scenario_nodes_depth` (exploration_id, depth)

---

### 15. ExperimentDocument (experiment_documents)

**Module**: `document.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | Document identifier |
| experiment_id | TEXT | NOT NULL, FK | Parent experiment |
| document_type | TEXT | NOT NULL | Type enum |
| markdown_content | TEXT | NOT NULL | Document content |
| metadata | JSON | Valid JSON or NULL | Generation metadata |
| generated_at | TEXT | NOT NULL | ISO timestamp |
| model | TEXT | DEFAULT 'gpt-4o-mini' | LLM model used |
| status | TEXT | NOT NULL, DEFAULT 'completed' | Status enum |
| error_message | TEXT | | Error details |

**Document types**: summary, prfaq, executive_summary
**Status values**: pending, generating, completed, failed, partial

**Constraints**:
- UNIQUE(experiment_id, document_type)

**Relationships**:
- `experiment` (N:1) - Parent experiment

**Indexes**:
- `idx_experiment_documents_experiment` (experiment_id)
- `idx_experiment_documents_type` (document_type)
- `idx_experiment_documents_status` (status)

---

## Legacy Models (Deprecated)

### 16. FeatureScorecard (feature_scorecards)

**Module**: `legacy.py`
**Note**: Scorecard data now embedded in `experiments.scorecard_data`

| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY |
| experiment_id | TEXT | FK |
| data | JSON | NOT NULL |
| created_at | TEXT | NOT NULL |
| updated_at | TEXT | |

---

### 17. SimulationRun (simulation_runs)

**Module**: `legacy.py`
**Note**: Replaced by `analysis_runs` table

| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY |
| scorecard_id | TEXT | NOT NULL, FK |
| scenario_id | TEXT | NOT NULL |
| config | JSON | NOT NULL |
| status | TEXT | NOT NULL |
| started_at | TEXT | NOT NULL |
| completed_at | TEXT | |
| total_synths | INTEGER | DEFAULT 0 |
| aggregated_outcomes | JSON | |
| execution_time_seconds | REAL | |

---

## Relationship Diagram

```text
experiments (1) ─────────────── (1) analysis_runs
     │                                   │
     │ (1:N)                            (1:N)
     ├── research_executions             └── synth_outcomes
     │        │
     │       (1:N)
     │        └── transcripts
     │
     │ (1:1)
     ├── interview_guide
     │
     │ (1:N)
     ├── explorations
     │        │
     │       (1:N)
     │        └── scenario_nodes (self-referential tree)
     │
     └── experiment_documents (1:N)

synth_groups (1) ──── (N) synths

simulation_runs (legacy) ──── chart_insights, sensitivity_results, region_analyses
```

---

## Migration Notes

1. **Initial Migration**: Generate Alembic migration from these models that creates schema equivalent to current SQLite v15
2. **JSON Fields**: Use `JSONVariant` type for all JSON columns
3. **Timestamps**: Store as ISO 8601 strings (TEXT) for compatibility
4. **IDs**: Keep as TEXT for UUID-style identifiers
5. **Indexes**: All indexes must be created in migrations
6. **Foreign Keys**: Enable foreign key constraints in engine configuration

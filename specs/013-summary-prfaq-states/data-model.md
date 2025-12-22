# Data Model: Summary and PR-FAQ State Management

**Feature Branch**: `013-summary-prfaq-states`
**Date**: 2025-12-21

## Overview

This document defines the data model extensions for artifact state management.

---

## Entities

### 1. ResearchExecution (Extended)

Existing entity with additional computed fields for artifact state.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| exec_id | TEXT (PK) | Unique execution identifier |
| topic_name | TEXT | Topic guide name |
| status | ExecutionStatus | Overall execution status |
| summary_content | TEXT (nullable) | Generated summary markdown |
| started_at | TIMESTAMP | Execution start time |
| completed_at | TIMESTAMP (nullable) | Execution completion time |
| synth_count | INTEGER | Total synths in batch |
| successful_count | INTEGER | Successfully completed interviews |
| failed_count | INTEGER | Failed interviews |

#### Computed Fields (in response model)

| Field | Type | Description |
|-------|------|-------------|
| summary_available | BOOLEAN | `summary_content IS NOT NULL AND LENGTH > 0` |
| prfaq_available | BOOLEAN | `EXISTS (SELECT 1 FROM prfaq_metadata WHERE exec_id = ?)` |

---

### 2. PRFAQMetadata (Extended)

Extended to track generation state and errors.

#### Current Fields

| Field | Type | Description |
|-------|------|-------------|
| exec_id | TEXT (PK, FK) | Links to research_executions |
| generated_at | TIMESTAMP | Generation completion time |
| model | TEXT | LLM model used |
| markdown_content | TEXT | Full PR-FAQ document |
| json_content | TEXT (nullable) | Structured JSON format |
| headline | TEXT | Extracted headline |
| one_liner | TEXT (nullable) | One-line summary |
| faq_count | INTEGER | Number of FAQ items |
| validation_status | TEXT | 'valid', 'invalid', 'pending' |
| confidence_score | REAL | Quality score 0-1 |

#### New Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| status | TEXT | 'completed' | 'generating', 'completed', 'failed' |
| error_message | TEXT (nullable) | NULL | Last failure reason |
| started_at | TIMESTAMP (nullable) | NULL | Generation start time |

---

### 3. ArtifactState (New Response Model)

Response model for unified artifact state endpoint.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| artifact_type | TEXT | 'summary' or 'prfaq' |
| state | ArtifactStateEnum | Current state |
| can_generate | BOOLEAN | Whether generate action is available |
| can_view | BOOLEAN | Whether view action is available |
| prerequisite_met | BOOLEAN | Whether prerequisites are satisfied |
| prerequisite_message | TEXT (nullable) | Message if prerequisite not met |
| error_message | TEXT (nullable) | Last error if failed |
| started_at | TIMESTAMP (nullable) | Generation start time |
| completed_at | TIMESTAMP (nullable) | Generation completion time |

---

## Enums

### ExecutionStatus (Existing)

```python
class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    GENERATING_SUMMARY = "generating_summary"
    COMPLETED = "completed"
    FAILED = "failed"
```

### PRFAQStatus (New)

```python
class PRFAQStatus(str, Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
```

### ArtifactStateEnum (New)

```python
class ArtifactStateEnum(str, Enum):
    UNAVAILABLE = "unavailable"
    GENERATING = "generating"
    AVAILABLE = "available"
    FAILED = "failed"
```

---

## State Transitions

### Summary State Machine

```
┌─────────────┐
│ unavailable │ ←── (initial state)
└─────┬───────┘
      │ execution.status = GENERATING_SUMMARY
      ▼
┌─────────────┐
│ generating  │
└─────┬───────┘
      │
      ├── execution.status = COMPLETED ──→ ┌───────────┐
      │                                     │ available │
      │                                     └───────────┘
      │
      └── execution.status = FAILED ──→ ┌────────┐
                                         │ failed │
                                         └────────┘
```

### PR-FAQ State Machine

```
┌─────────────┐
│ unavailable │ ←── (initial state)
└─────┬───────┘
      │
      ├── summary_available = false ──→ BLOCKED (disabled button)
      │
      ├── summary_available = true ──→ READY (enabled button)
      │
      │ POST /prfaq/generate
      ▼
┌─────────────┐
│ generating  │ ←── prfaq_metadata.status = 'generating'
└─────┬───────┘
      │
      ├── generation success ──→ ┌───────────┐
      │                           │ available │ ←── prfaq_metadata.status = 'completed'
      │                           └───────────┘
      │
      └── generation failed ──→ ┌────────┐
                                 │ failed │ ←── prfaq_metadata.status = 'failed'
                                 └────┬───┘
                                      │
                                      │ retry ──→ generating
                                      ▼
```

---

## Database Schema Changes

### Migration: Add PR-FAQ Status Columns

```sql
-- Add status and error tracking to prfaq_metadata
ALTER TABLE prfaq_metadata ADD COLUMN status TEXT DEFAULT 'completed';
ALTER TABLE prfaq_metadata ADD COLUMN error_message TEXT;
ALTER TABLE prfaq_metadata ADD COLUMN started_at TEXT;

-- For existing records, set status to 'completed' (already generated)
UPDATE prfaq_metadata SET status = 'completed' WHERE status IS NULL;
```

---

## Relationships

```
research_executions 1 ─────── 0..1 prfaq_metadata
        │                            │
        │ exec_id (PK)               │ exec_id (FK, PK)
        │                            │
        └── summary_content          └── markdown_content
            (nullable)                   status
                                         error_message
```

---

## Validation Rules

### ResearchExecution

- `exec_id` must be unique UUID format
- `status` must be valid ExecutionStatus enum value
- `summary_content` can only be set when status is GENERATING_SUMMARY or COMPLETED
- `completed_at` must be set when status is COMPLETED or FAILED

### PRFAQMetadata

- `exec_id` must reference existing research_executions
- `status` must be valid PRFAQStatus enum value
- `markdown_content` required when status is 'completed'
- `error_message` should be set when status is 'failed'
- `started_at` should be set when generation begins
- `generated_at` should be set when status changes to 'completed'

### ArtifactState Computation

- `can_generate` for summary is always false (auto-generated)
- `can_generate` for prfaq requires `summary_available = true` and `prfaq_state in ('unavailable', 'failed')`
- `can_view` requires state is 'available'
- `prerequisite_met` for prfaq requires `summary_available = true`

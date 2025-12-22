# Research: Summary and PR-FAQ State Management

**Feature Branch**: `013-summary-prfaq-states`
**Date**: 2025-12-21

## Overview

This document consolidates research findings for implementing robust state management for summary and PR-FAQ generation artifacts.

---

## 1. Current State Tracking Approach

### Decision: Database Content as Source of Truth

The codebase derives availability flags from actual database content rather than maintaining separate status fields.

### Rationale

- Avoids state synchronization bugs where status and content could diverge
- Single source of truth reduces maintenance burden
- Existing pattern proven in production

### Current Implementation

```python
# research_repository.py
summary_available = summary_content is not None and len(summary_content) > 0

prfaq_row = self.db.fetchone(
    "SELECT 1 FROM prfaq_metadata WHERE exec_id = ?",
    (row["exec_id"],),
)
prfaq_available = prfaq_row is not None
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Explicit status fields in DB | Requires maintaining enum consistency, risk of state drift |
| In-memory cache | Lost on restart, unreliable for multi-instance |

### Recommendation

**Extend current approach** by adding a `generating` state detection:
- Check if background task is running (via in-memory registry or status field)
- Add optional `prfaq_generating` flag to track ongoing PR-FAQ generation
- Summary generation already tracked via `ExecutionStatus.GENERATING_SUMMARY`

---

## 2. Concurrent Request Prevention

### Decision: Status Enum + Database Constraints

Existing pattern uses `ExecutionStatus` enum with database unique constraints.

### Rationale

- Status field prevents state machine violations
- Database constraints provide hard guarantees
- Works reliably without external dependencies

### Current Implementation

```python
class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    GENERATING_SUMMARY = "generating_summary"
    COMPLETED = "completed"
    FAILED = "failed"
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Database locks | Connection management overhead |
| In-memory locks | Doesn't work across processes |
| Celery/RQ | Adds external dependency |

### Recommendation

**Extend for PR-FAQ generation**:
- Add `prfaq_status` column: `null`, `generating`, `completed`, `failed`
- Check status before starting generation
- Return current state if already generating

---

## 3. React Query Polling Patterns

### Decision: Conditional Query with `enabled` Flag

Frontend uses React Query's conditional querying with smart cache invalidation.

### Rationale

- Prevents unnecessary requests before availability
- Query keys ensure proper cache isolation
- Mutation invalidation triggers fresh data fetch

### Current Implementation

```typescript
const { data: summaryMarkdown } = useResearchSummary(
  execId!,
  execution?.summary_available || false
);

// Invalidation after mutation
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: queryKeys.researchDetail(execId!) });
}
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| `refetchInterval` | Continuously polls even after completion |
| SSE streaming | Not yet implemented (infrastructure exists) |
| Manual polling | More code, less elegant |

### Recommendation

**Add short polling during generation**:
- When `prfaq_status === 'generating'`, enable `refetchInterval: 2000`
- Stop polling when status changes to `completed` or `failed`
- Use React Query's `select` to extract state efficiently

---

## 4. Button State Patterns

### Decision: Disabled + Dynamic Label + Loading Spinner

Current implementation uses multi-layered user feedback.

### Rationale

- Dual indication (disabled + label) handles keyboard and mouse users
- Loading spinner provides immediate visual feedback
- Conditional rendering shows appropriate action

### Current Implementation

```typescript
<Button
  onClick={() => generatePrfaqMutation.mutate()}
  disabled={!execution.summary_available || generatePrfaqMutation.isPending}
  className="w-full"
>
  {generatePrfaqMutation.isPending && (
    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
  )}
  Gerar PR/FAQ
</Button>
```

### Available UI Components

- `Button` with `disabled` prop
- `Tooltip` with `TooltipProvider`, `TooltipTrigger`, `TooltipContent`
- Icons: `FileText`, `FileCheck`, `Loader2`, `AlertCircle`
- `StatusBadge` for status indication

### Recommendation

**Create reusable ArtifactButton component**:
```typescript
interface ArtifactButtonProps {
  state: 'unavailable' | 'generating' | 'available' | 'failed';
  prerequisiteMessage?: string;
  onGenerate: () => void;
  onView: () => void;
  onRetry?: () => void;
}
```

---

## 5. Error Handling Patterns

### Decision: Exception Hierarchy + Service Layer Mapping

Errors follow layered approach with domain exceptions.

### Rationale

- Type-safe error handling
- Service layer validates preconditions
- Exception hierarchy maps cleanly to HTTP responses

### Current Implementation

```python
class SummaryNotFoundError(NotFoundError):
    code = "SUMMARY_NOT_FOUND"
    message = "Summary not found"

# Service validation
if not execution.summary_available:
    raise SummaryNotFoundError(request.exec_id)
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Storing error_message in DB | Overkill for current use case |
| Result<T> pattern | More verbose, less idiomatic Python |
| Returning error codes | Less type-safe |

### Recommendation

**Add error persistence for PR-FAQ failures**:
- Add optional `prfaq_error_message` column
- Store last failure reason for user-facing display
- Clear on successful retry

---

## 6. State Machine Definition

### Final State Machine

Based on research, define the following state transitions:

#### Summary States
| Current State | Event | Next State |
|---------------|-------|------------|
| unavailable | execution.status = RUNNING | unavailable |
| unavailable | execution.status = GENERATING_SUMMARY | generating |
| generating | execution.status = COMPLETED | available |
| generating | execution.status = FAILED | failed |
| failed | retry execution | unavailable |

#### PR-FAQ States
| Current State | Event | Next State |
|---------------|-------|------------|
| unavailable | summary_available = false | unavailable (blocked) |
| unavailable | summary_available = true | unavailable (ready) |
| unavailable | generate requested | generating |
| generating | generation complete | available |
| generating | generation failed | failed |
| failed | retry requested | generating |
| available | (terminal) | available |

### Backend State Computation

```python
def compute_artifact_states(execution, prfaq_metadata) -> dict:
    summary_state = 'unavailable'
    if execution.status == ExecutionStatus.GENERATING_SUMMARY:
        summary_state = 'generating'
    elif execution.summary_available:
        summary_state = 'available'
    elif execution.status == ExecutionStatus.FAILED:
        summary_state = 'failed'

    prfaq_state = 'unavailable'
    if prfaq_metadata and prfaq_metadata.status == 'generating':
        prfaq_state = 'generating'
    elif prfaq_metadata and prfaq_metadata.markdown_content:
        prfaq_state = 'available'
    elif prfaq_metadata and prfaq_metadata.status == 'failed':
        prfaq_state = 'failed'

    return {
        'summary': {
            'state': summary_state,
            'can_generate': False,  # Auto-generated
            'can_view': summary_state == 'available'
        },
        'prfaq': {
            'state': prfaq_state,
            'can_generate': summary_state == 'available' and prfaq_state in ('unavailable', 'failed'),
            'can_view': prfaq_state == 'available',
            'prerequisite_met': summary_state == 'available',
            'error_message': prfaq_metadata.error_message if prfaq_metadata else None
        }
    }
```

---

## Summary of Recommendations

1. **Extend current patterns** rather than introducing new architecture
2. **Add `prfaq_status` column** for generation state tracking
3. **Add `prfaq_error_message` column** for failure details
4. **Create unified state endpoint** returning computed artifact states
5. **Create reusable ArtifactButton component** for consistent UI
6. **Add conditional polling** during generation states
7. **Leverage existing exception hierarchy** for error handling

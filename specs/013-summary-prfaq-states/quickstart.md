# Quickstart: Summary and PR-FAQ State Management

**Feature Branch**: `013-summary-prfaq-states`
**Date**: 2025-12-21

## Overview

This feature adds robust state management for research artifacts (Summary and PR-FAQ), providing clear UI feedback and preventing duplicate generation requests.

---

## Quick Usage

### 1. Check Artifact States

```bash
# Get current states for all artifacts
curl http://localhost:8000/api/research/{exec_id}/artifacts
```

Response:
```json
{
  "exec_id": "abc123",
  "summary": {
    "artifact_type": "summary",
    "state": "available",
    "can_generate": false,
    "can_view": true,
    "prerequisite_met": true
  },
  "prfaq": {
    "artifact_type": "prfaq",
    "state": "unavailable",
    "can_generate": true,
    "can_view": false,
    "prerequisite_met": true
  }
}
```

### 2. Generate PR-FAQ

```bash
# Start PR-FAQ generation
curl -X POST http://localhost:8000/api/prfaq/generate \
  -H "Content-Type: application/json" \
  -d '{"exec_id": "abc123", "model": "gpt-4o-mini"}'
```

Response (generation started):
```json
{
  "exec_id": "abc123",
  "status": "generating",
  "message": "PR-FAQ generation started"
}
```

Response (already in progress):
```json
{
  "exec_id": "abc123",
  "status": "generating",
  "message": "Generation already in progress"
}
```

### 3. Poll for Completion

```bash
# Check state until completed
curl http://localhost:8000/api/research/{exec_id}/artifacts
```

When completed:
```json
{
  "exec_id": "abc123",
  "prfaq": {
    "state": "available",
    "can_view": true,
    "completed_at": "2025-12-21T10:30:00Z"
  }
}
```

---

## Frontend Integration

### Using the ArtifactButton Component

```tsx
import { ArtifactButton } from '@/components/shared/ArtifactButton';
import { useArtifactStates } from '@/hooks/use-artifact-states';
import { usePrfaqGenerate } from '@/hooks/use-prfaq-generate';

function InterviewDetail({ execId }: { execId: string }) {
  const { data: states } = useArtifactStates(execId);
  const generateMutation = usePrfaqGenerate();

  return (
    <div className="space-y-4">
      {/* Summary Button */}
      <ArtifactButton
        artifactType="summary"
        state={states?.summary.state || 'unavailable'}
        onView={() => setSummaryOpen(true)}
      />

      {/* PR-FAQ Button */}
      <ArtifactButton
        artifactType="prfaq"
        state={states?.prfaq.state || 'unavailable'}
        prerequisiteMessage={states?.prfaq.prerequisite_message}
        onGenerate={() => generateMutation.mutate({ exec_id: execId })}
        onView={() => setPrfaqOpen(true)}
        onRetry={() => generateMutation.mutate({ exec_id: execId })}
        isPending={generateMutation.isPending}
      />
    </div>
  );
}
```

### State-to-UI Mapping

| State | Button Label | Icon | Enabled | Tooltip |
|-------|-------------|------|---------|---------|
| unavailable (no prereq) | "Gerar" | - | No | "Summary necessario" |
| unavailable (prereq met) | "Gerar" | Plus | Yes | - |
| generating | "Gerando..." | Spinner | No | - |
| available | "Visualizar" | Eye | Yes | - |
| failed | "Tentar novamente" | AlertCircle | Yes | Error message |

---

## API Endpoints

### GET /research/{exec_id}/artifacts

Returns the current state of all artifacts for an execution.

**Parameters:**
- `exec_id` (path): Research execution ID

**Response:**
- `200`: `ArtifactStatesResponse`
- `404`: Execution not found

### POST /prfaq/generate

Initiates or retries PR-FAQ generation.

**Body:**
```json
{
  "exec_id": "string",
  "model": "gpt-4o-mini"  // optional
}
```

**Responses:**
- `200`: Generation started/completed
- `400`: Summary not available
- `404`: Execution not found
- `409`: Generation already in progress (returns current state)

---

## State Transitions

### Summary

```
unavailable → generating → available
                        ↘ failed
```

Summary generation is automatic during research execution.

### PR-FAQ

```
unavailable (blocked) ─── summary_available = false
         ↓
unavailable (ready) ─── summary_available = true
         ↓
   [user clicks]
         ↓
    generating ───→ available
         ↓              ↑
       failed ──────────┘
         [retry]
```

---

## Error Handling

### Prerequisite Not Met

```json
{
  "code": "SUMMARY_NOT_FOUND",
  "message": "Summary not found for execution: abc123"
}
```

Frontend should show disabled button with tooltip.

### Generation Failed

```json
{
  "exec_id": "abc123",
  "status": "failed",
  "error_message": "OpenAI API rate limit exceeded"
}
```

Frontend should show retry button with error message in tooltip.

---

## Polling Strategy

For best UX, implement conditional polling:

```typescript
const { data: states, refetch } = useQuery({
  queryKey: ['research', execId, 'artifacts'],
  queryFn: () => getArtifactStates(execId),
  // Poll every 2s only while generating
  refetchInterval: states?.prfaq.state === 'generating' ? 2000 : false,
});
```

---

## Testing

### Unit Tests

```bash
# Run state machine tests
pytest tests/unit/domain/test_artifact_state.py -v
```

### Integration Tests

```bash
# Run API integration tests
pytest tests/integration/api/test_artifact_state_api.py -v
```

### Manual Testing

1. Create a research execution
2. Wait for summary generation (status: COMPLETED)
3. Call POST /prfaq/generate
4. Poll GET /artifacts until prfaq.state = 'available'
5. View PR-FAQ content

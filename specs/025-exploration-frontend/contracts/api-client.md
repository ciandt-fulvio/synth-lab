# API Client Contract: Exploration Frontend

**Feature**: 025-exploration-frontend
**Date**: 2025-12-31

## Overview

Este documento define o contrato da camada de servico (API client) para a feature de exploracao. Os endpoints sao consumidos do backend implementado em spec 024.

## Service Functions

### exploration-api.ts

```typescript
// services/exploration-api.ts

import { fetchAPI } from './api';
import type {
  Exploration,
  ExplorationCreate,
  ExplorationTree,
  WinningPath,
  ActionCatalog,
  ExplorationSummary,
} from '@/types/exploration';

/**
 * Create a new exploration for an experiment.
 *
 * @param data - Exploration creation parameters
 * @returns Created exploration
 * @throws APIError if experiment not found or no baseline analysis
 */
export async function createExploration(
  data: ExplorationCreate
): Promise<Exploration> {
  return fetchAPI<Exploration>('/explorations', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get an exploration by ID.
 *
 * @param id - Exploration ID (expl_xxxxxxxx)
 * @returns Exploration data
 * @throws APIError if not found
 */
export async function getExploration(id: string): Promise<Exploration> {
  return fetchAPI<Exploration>(`/explorations/${id}`);
}

/**
 * Start running an exploration in background.
 *
 * @param id - Exploration ID
 * @returns Current exploration state (will update in background)
 */
export async function runExploration(id: string): Promise<Exploration> {
  return fetchAPI<Exploration>(`/explorations/${id}/run`, {
    method: 'POST',
  });
}

/**
 * Get the complete exploration tree with all nodes.
 *
 * @param id - Exploration ID
 * @returns Tree structure with nodes and status counts
 */
export async function getExplorationTree(id: string): Promise<ExplorationTree> {
  return fetchAPI<ExplorationTree>(`/explorations/${id}/tree`);
}

/**
 * Get the winning path if exploration achieved goal.
 *
 * @param id - Exploration ID
 * @returns Winning path or null if no winner
 */
export async function getWinningPath(id: string): Promise<WinningPath | null> {
  return fetchAPI<WinningPath | null>(`/explorations/${id}/winning-path`);
}

/**
 * Get the action catalog with all categories and examples.
 *
 * @returns Action catalog
 */
export async function getActionCatalog(): Promise<ActionCatalog> {
  return fetchAPI<ActionCatalog>('/explorations/catalog/actions');
}

/**
 * List explorations for an experiment.
 * NOTE: This endpoint needs to be added to backend.
 *
 * @param experimentId - Experiment ID
 * @returns List of exploration summaries
 */
export async function listExplorations(
  experimentId: string
): Promise<ExplorationSummary[]> {
  return fetchAPI<ExplorationSummary[]>(
    `/experiments/${experimentId}/explorations`
  );
}
```

## Endpoint Reference

| Function | Method | Endpoint | Request | Response |
|----------|--------|----------|---------|----------|
| `createExploration` | POST | `/api/explorations` | `ExplorationCreate` | `Exploration` |
| `getExploration` | GET | `/api/explorations/{id}` | - | `Exploration` |
| `runExploration` | POST | `/api/explorations/{id}/run` | - | `Exploration` |
| `getExplorationTree` | GET | `/api/explorations/{id}/tree` | - | `ExplorationTree` |
| `getWinningPath` | GET | `/api/explorations/{id}/winning-path` | - | `WinningPath \| null` |
| `getActionCatalog` | GET | `/api/explorations/catalog/actions` | - | `ActionCatalog` |
| `listExplorations` | GET | `/api/experiments/{id}/explorations` | - | `ExplorationSummary[]` |

## Error Handling

```typescript
// Expected error responses from backend

// 404 - Not Found
interface NotFoundError {
  detail: string; // e.g., "Exploration expl_12345678 not found"
}

// 422 - Unprocessable Entity
interface ValidationError {
  detail: string; // e.g., "Experiment has no scorecard data"
}

// Example error handling in hook
const mutation = useMutation({
  mutationFn: createExploration,
  onError: (error) => {
    if (error instanceof APIError) {
      if (error.status === 404) {
        toast.error('Experimento não encontrado');
      } else if (error.status === 422) {
        toast.error(error.message); // Backend provides clear message
      } else {
        toast.error('Erro ao criar exploração');
      }
    }
  },
});
```

## Polling Strategy

```typescript
// Conditional polling for running explorations
const { data: exploration } = useQuery({
  queryKey: queryKeys.explorationDetail(id),
  queryFn: () => getExploration(id),
  refetchInterval: (data) => {
    // Poll every 3 seconds only while running
    if (data?.status === 'running') {
      return 3000;
    }
    // Stop polling when complete
    return false;
  },
});
```

## Query Keys

```typescript
// lib/query-keys.ts additions

export const queryKeys = {
  // ... existing keys ...

  // Explorations
  explorationsList: (experimentId: string) =>
    ['explorations', 'list', experimentId] as const,
  explorationDetail: (id: string) =>
    ['explorations', 'detail', id] as const,
  explorationTree: (id: string) =>
    ['explorations', 'tree', id] as const,
  explorationWinningPath: (id: string) =>
    ['explorations', 'winning-path', id] as const,
  actionCatalog: ['explorations', 'catalog'] as const,
};
```

## Backend Endpoint to Add

O endpoint `GET /api/experiments/{id}/explorations` precisa ser adicionado ao backend para listar exploracoes de um experimento.

**Sugestao de implementacao**:

```python
# api/routers/experiment.py

@router.get("/{experiment_id}/explorations")
async def list_explorations(experiment_id: str) -> list[ExplorationSummary]:
    """List explorations for an experiment."""
    repo = ExplorationRepository()
    explorations = repo.get_by_experiment(experiment_id)
    return [
        ExplorationSummary(
            id=e.id,
            status=e.status.value,
            goal_value=e.goal.value,
            best_success_rate=e.best_success_rate,
            total_nodes=e.total_nodes,
            started_at=e.started_at,
            completed_at=e.completed_at,
        )
        for e in explorations
    ]
```

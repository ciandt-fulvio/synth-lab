# React Hooks Contract: Exploration Frontend

**Feature**: 025-exploration-frontend
**Date**: 2025-12-31

## Overview

Este documento define os hooks React Query para a feature de exploracao. Seguem o padrao estabelecido em `docs/arquitetura_front.md`.

## Hook Definitions

### use-exploration.ts

```typescript
// hooks/use-exploration.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  createExploration,
  getExploration,
  runExploration,
  getExplorationTree,
  getWinningPath,
  getActionCatalog,
  listExplorations,
} from '@/services/exploration-api';
import type { ExplorationCreate } from '@/types/exploration';

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * List explorations for an experiment.
 */
export function useExplorations(experimentId: string) {
  return useQuery({
    queryKey: queryKeys.explorationsList(experimentId),
    queryFn: () => listExplorations(experimentId),
    enabled: !!experimentId,
  });
}

/**
 * Get exploration by ID with conditional polling.
 * Polls every 3s while status is 'running'.
 */
export function useExploration(id: string) {
  return useQuery({
    queryKey: queryKeys.explorationDetail(id),
    queryFn: () => getExploration(id),
    enabled: !!id,
    refetchInterval: (data) => {
      // Poll while running
      if (data?.status === 'running') {
        return 3000; // 3 seconds
      }
      return false;
    },
  });
}

/**
 * Get exploration tree with all nodes.
 * Refetches when exploration is running.
 */
export function useExplorationTree(id: string, enabled = true) {
  const { data: exploration } = useExploration(id);

  return useQuery({
    queryKey: queryKeys.explorationTree(id),
    queryFn: () => getExplorationTree(id),
    enabled: enabled && !!id,
    refetchInterval: () => {
      // Poll while running
      if (exploration?.status === 'running') {
        return 5000; // 5 seconds for tree (heavier)
      }
      return false;
    },
  });
}

/**
 * Get winning path if exploration achieved goal.
 */
export function useWinningPath(id: string, enabled = true) {
  const { data: exploration } = useExploration(id);

  return useQuery({
    queryKey: queryKeys.explorationWinningPath(id),
    queryFn: () => getWinningPath(id),
    enabled: enabled && !!id && exploration?.status === 'goal_achieved',
  });
}

/**
 * Get action catalog.
 * Static data, cached indefinitely.
 */
export function useActionCatalog() {
  return useQuery({
    queryKey: queryKeys.actionCatalog,
    queryFn: getActionCatalog,
    staleTime: Infinity, // Never refetch automatically
  });
}

// =============================================================================
// Mutation Hooks
// =============================================================================

/**
 * Create a new exploration.
 */
export function useCreateExploration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExplorationCreate) => createExploration(data),
    onSuccess: (exploration) => {
      // Invalidate list cache
      queryClient.invalidateQueries({
        queryKey: queryKeys.explorationsList(exploration.experiment_id),
      });
    },
  });
}

/**
 * Start running an exploration.
 */
export function useRunExploration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => runExploration(id),
    onSuccess: (exploration) => {
      // Update detail cache
      queryClient.setQueryData(
        queryKeys.explorationDetail(exploration.id),
        exploration
      );
      // Invalidate list to show "running" status
      queryClient.invalidateQueries({
        queryKey: queryKeys.explorationsList(exploration.experiment_id),
      });
    },
  });
}

// =============================================================================
// Composed Hooks
// =============================================================================

/**
 * Hook for starting a new exploration and running it.
 * Combines create + run in one operation.
 */
export function useStartExploration() {
  const createMutation = useCreateExploration();
  const runMutation = useRunExploration();

  const startExploration = async (data: ExplorationCreate) => {
    // 1. Create exploration
    const exploration = await createMutation.mutateAsync(data);
    // 2. Start running it
    await runMutation.mutateAsync(exploration.id);
    return exploration;
  };

  return {
    startExploration,
    isPending: createMutation.isPending || runMutation.isPending,
    isError: createMutation.isError || runMutation.isError,
    error: createMutation.error || runMutation.error,
  };
}
```

## Usage Examples

### Pagina de Exploracao

```tsx
// pages/ExplorationDetail.tsx

export default function ExplorationDetail() {
  const { explorationId } = useParams<{ explorationId: string }>();
  const { data: exploration, isLoading } = useExploration(explorationId!);
  const { data: tree } = useExplorationTree(explorationId!);
  const { data: winningPath } = useWinningPath(explorationId!);

  if (isLoading) return <Loading />;

  return (
    <div>
      <ExplorationHeader exploration={exploration} />
      <ExplorationTree nodes={tree?.nodes} />
      {winningPath && <WinningPathPanel path={winningPath} />}
    </div>
  );
}
```

### Secao de Exploracoes na Pagina de Experimento

```tsx
// components/experiments/ExplorationSection.tsx

export function ExplorationSection({ experimentId }: Props) {
  const { data: explorations, isLoading } = useExplorations(experimentId);
  const { startExploration, isPending } = useStartExploration();
  const [isFormOpen, setIsFormOpen] = useState(false);

  const handleStart = async (data: ExplorationCreateForm) => {
    try {
      await startExploration({
        experiment_id: experimentId,
        goal_value: data.goal_value / 100, // Convert from % to 0-1
        beam_width: data.beam_width,
        max_depth: data.max_depth,
      });
      toast.success('Exploração iniciada');
      setIsFormOpen(false);
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div>
      <Button onClick={() => setIsFormOpen(true)}>
        Iniciar Exploração
      </Button>

      <ExplorationList explorations={explorations} />

      <NewExplorationDialog
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        onSubmit={handleStart}
        isPending={isPending}
      />
    </div>
  );
}
```

### Catalogo de Acoes

```tsx
// components/exploration/ActionCatalogDialog.tsx

export function ActionCatalogDialog({ open, onOpenChange }: Props) {
  const { data: catalog, isLoading } = useActionCatalog();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Catálogo de Ações</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <Skeleton className="h-64" />
        ) : (
          <div className="space-y-4">
            {catalog?.categories.map((category) => (
              <CategoryCard key={category.id} category={category} />
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
```

## Query Key Structure

```typescript
// Final query keys structure

queryKeys = {
  // Existing...
  experimentsList: ['experiments'] as const,
  experimentDetail: (id: string) => ['experiments', id] as const,

  // New for explorations
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

## Cache Invalidation Rules

| Action | Invalidates |
|--------|-------------|
| Create exploration | `explorationsList(experimentId)` |
| Run exploration | `explorationDetail(id)`, `explorationsList(experimentId)` |
| Tree/path data | Auto-refreshes via polling while running |

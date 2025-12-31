/**
 * React Query hooks for exploration feature.
 *
 * Provides data fetching and mutations for explorations.
 * See: specs/025-exploration-frontend/contracts/hooks.md
 */

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
    refetchInterval: (query) => {
      // Poll while running
      if (query.state.data?.status === 'running') {
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
      queryClient.setQueryData(queryKeys.explorationDetail(exploration.id), exploration);
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

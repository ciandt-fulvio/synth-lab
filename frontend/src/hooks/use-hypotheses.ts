/**
 * React Query hooks for Hypothesis operations.
 *
 * Provides hooks for hypothesis CRUD and versioning with caching.
 *
 * References:
 *   - API: services/hypotheses-api.ts
 *   - Types: types/hypothesis.ts
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  compareHypothesisVersions,
  getHypotheses,
  getHypothesesAtVersion,
  listHypothesisVersions,
  saveHypothesisVersion,
  updateHypotheses,
  updateHypothesis,
} from '@/services/hypotheses-api';
import type {
  HypothesesBulkUpdateRequest,
  HypothesisCompareRequest,
  HypothesisUpdateRequest,
  HypothesisVersionCreateRequest,
} from '@/types/hypothesis';

/**
 * Hook to fetch hypotheses for a simulation.
 *
 * @param simulationId - Simulation ID
 * @param options - Query options
 * @returns Query result with hypotheses
 */
export function useHypotheses(
  simulationId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.hypotheses.list(simulationId),
    queryFn: () => getHypotheses(simulationId),
    enabled: options?.enabled,
  });
}

/**
 * Hook to update multiple hypotheses.
 *
 * @returns Mutation for bulk updates
 */
export function useUpdateHypotheses() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      request,
    }: {
      simulationId: string;
      request: HypothesesBulkUpdateRequest;
    }) => updateHypotheses(simulationId, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.hypotheses.list(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to update a single hypothesis.
 *
 * @returns Mutation for single update
 */
export function useUpdateHypothesis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      variableName,
      request,
    }: {
      simulationId: string;
      variableName: string;
      request: HypothesisUpdateRequest;
    }) => updateHypothesis(simulationId, variableName, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.hypotheses.list(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to save a hypothesis version.
 *
 * @returns Mutation for saving version
 */
export function useSaveHypothesisVersion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      simulationId,
      request,
    }: {
      simulationId: string;
      request: HypothesisVersionCreateRequest;
    }) => saveHypothesisVersion(simulationId, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.hypotheses.versions(variables.simulationId),
      });
    },
  });
}

/**
 * Hook to list hypothesis versions.
 *
 * @param simulationId - Simulation ID
 * @param options - Query options
 * @returns Query result with versions
 */
export function useHypothesisVersions(
  simulationId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.hypotheses.versions(simulationId),
    queryFn: () => listHypothesisVersions(simulationId),
    enabled: options?.enabled,
  });
}

/**
 * Hook to get hypotheses at a specific version.
 *
 * @returns Mutation for fetching version
 */
export function useHypothesesAtVersion() {
  return useMutation({
    mutationFn: ({
      simulationId,
      version,
    }: {
      simulationId: string;
      version: number;
    }) => getHypothesesAtVersion(simulationId, version),
  });
}

/**
 * Hook to compare hypothesis versions.
 *
 * @returns Mutation for comparing versions
 */
export function useCompareHypothesisVersions() {
  return useMutation({
    mutationFn: ({
      simulationId,
      request,
    }: {
      simulationId: string;
      request: HypothesisCompareRequest;
    }) => compareHypothesisVersions(simulationId, request),
  });
}

/**
 * Combined hook for hypothesis editor workflow.
 *
 * @param simulationId - Simulation ID
 * @returns All hypothesis operations and data
 */
export function useHypothesisEditor(simulationId: string) {
  const hypothesesQuery = useHypotheses(simulationId);
  const versionsQuery = useHypothesisVersions(simulationId);
  const updateMutation = useUpdateHypotheses();
  const updateSingleMutation = useUpdateHypothesis();
  const saveVersionMutation = useSaveHypothesisVersion();
  const compareMutation = useCompareHypothesisVersions();

  return {
    // Data
    hypotheses: hypothesesQuery.data,
    versions: versionsQuery.data,
    isLoading: hypothesesQuery.isLoading,
    isLoadingVersions: versionsQuery.isLoading,
    error: hypothesesQuery.error,

    // Mutations
    updateHypotheses: (request: HypothesesBulkUpdateRequest) =>
      updateMutation.mutate({ simulationId, request }),
    updateHypothesis: (variableName: string, request: HypothesisUpdateRequest) =>
      updateSingleMutation.mutate({ simulationId, variableName, request }),
    saveVersion: (request: HypothesisVersionCreateRequest) =>
      saveVersionMutation.mutate({ simulationId, request }),
    compareVersions: (request: HypothesisCompareRequest) =>
      compareMutation.mutate({ simulationId, request }),

    // Mutation states
    isUpdating: updateMutation.isPending || updateSingleMutation.isPending,
    isSavingVersion: saveVersionMutation.isPending,
    comparisonResult: compareMutation.data,
  };
}

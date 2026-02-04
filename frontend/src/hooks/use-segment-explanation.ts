// frontend/src/hooks/use-segment-explanation.ts
// React Query hook for fetching segment explanations via mechanism×sensitivity interactions
// Reference: specs/038-mechanism-based-simulation/spec.md

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { fetchAPI } from '@/services/api';
import type { SegmentExplanation } from '@/types/simulation';

// =============================================================================
// Types
// =============================================================================

interface ExplainSegmentRequest {
  synth_ids: string[];
  compare_to_population?: boolean;
}

// =============================================================================
// API Functions
// =============================================================================

async function getSegmentExplanation(
  experimentId: string,
  request: ExplainSegmentRequest
): Promise<SegmentExplanation> {
  return fetchAPI(`/experiments/${experimentId}/analysis/explain-segment`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook to fetch segment explanation for a list of synth IDs.
 *
 * @param experimentId - Parent experiment ID
 * @param synthIds - List of synth IDs to explain
 * @param compareToPopulation - Whether to compare to population (default: true)
 * @param enabled - Whether the query should run
 * @returns Query result with segment explanation
 */
export function useSegmentExplanation(
  experimentId: string,
  synthIds: string[],
  compareToPopulation = true,
  enabled = true
) {
  return useQuery({
    queryKey: queryKeys.analysis.segmentExplanation(experimentId, synthIds),
    queryFn: () =>
      getSegmentExplanation(experimentId, {
        synth_ids: synthIds,
        compare_to_population: compareToPopulation,
      }),
    enabled: !!experimentId && synthIds.length > 0 && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Mutation hook to request segment explanation on-demand.
 *
 * Use this when you want to fetch explanation only when user explicitly requests it,
 * rather than automatically on component mount.
 *
 * @param experimentId - Parent experiment ID
 * @returns Mutation with explainSegment function
 */
export function useExplainSegmentMutation(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ExplainSegmentRequest) =>
      getSegmentExplanation(experimentId, request),
    onSuccess: (data, variables) => {
      // Cache the result for future queries
      queryClient.setQueryData(
        queryKeys.analysis.segmentExplanation(experimentId, variables.synth_ids),
        data
      );
    },
  });
}

export default useSegmentExplanation;

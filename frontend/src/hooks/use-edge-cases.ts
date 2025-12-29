// frontend/src/hooks/use-edge-cases.ts
// React Query hooks for edge cases and outliers (Phase 4)

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { getExtremeCases, getOutliers } from '@/services/simulation-api';

/**
 * Hook to fetch extreme cases (worst failures, best successes, unexpected)
 */
export function useExtremeCases(
  simulationId: string,
  nPerCategory = 10,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.simulation.extremeCases(simulationId), nPerCategory],
    queryFn: () => getExtremeCases(simulationId, nPerCategory),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch statistical outliers using Isolation Forest
 */
export function useOutliers(
  simulationId: string,
  contamination = 0.1,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.simulation.outliers(simulationId), contamination],
    queryFn: () => getOutliers(simulationId, contamination),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

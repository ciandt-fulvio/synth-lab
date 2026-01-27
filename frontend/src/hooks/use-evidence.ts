/**
 * React Query hook for simulation evidence.
 *
 * Provides hooks for fetching evidence with caching.
 *
 * References:
 *   - API: services/simulation-insights-api.ts
 *   - Types: types/simulation-insight.ts
 */

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { getEvidence } from '@/services/simulation-insights-api';

/**
 * Hook to fetch simulation evidence.
 *
 * @param simulationId - Simulation ID
 * @param options - Query options
 * @returns Query result with evidence
 */
export function useEvidence(
  simulationId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.simulations.evidence(simulationId),
    queryFn: () => getEvidence(simulationId),
    enabled: options?.enabled !== false && !!simulationId,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  });
}

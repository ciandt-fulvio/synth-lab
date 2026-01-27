/**
 * React Query hooks for simulation insights.
 *
 * Provides hooks for fetching insights and traceability.
 *
 * References:
 *   - API: services/simulation-insights-api.ts
 *   - Types: types/simulation-insight.ts
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { getInsights, getInsightTrace } from '@/services/simulation-insights-api';

/**
 * Hook to fetch simulation insights.
 *
 * @param simulationId - Simulation ID
 * @param options - Query options
 * @returns Query result with insights
 */
export function useSimulationInsights(
  simulationId: string,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: queryKeys.simulations.insights(simulationId),
    queryFn: () => getInsights(simulationId),
    enabled: options?.enabled !== false && !!simulationId,
  });
}

/**
 * Hook to fetch insight trace (lazy).
 *
 * @returns Mutation for fetching trace
 */
export function useInsightTrace() {
  return useMutation({
    mutationFn: (insightId: string) => getInsightTrace(insightId),
  });
}

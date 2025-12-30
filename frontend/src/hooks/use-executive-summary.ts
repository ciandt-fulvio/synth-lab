/**
 * Hook for fetching executive summary.
 *
 * Provides auto-refresh for pending/partial summaries and caching for completed ones.
 *
 * References:
 *   - API: src/services/insights-api.ts
 *   - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 2)
 *
 * Features:
 *   - Auto-refresh every 15s for pending/partial summaries
 *   - 5-minute cache for completed summaries
 *   - Error handling
 */

import { useQuery } from '@tanstack/react-query';
import { getExecutiveSummary } from '@/services/insights-api';
import type { ExecutiveSummary } from '@/types/insights';

interface UseExecutiveSummaryOptions {
  enabled?: boolean;
}

export function useExecutiveSummary(experimentId: string, options?: UseExecutiveSummaryOptions) {
  return useQuery<ExecutiveSummary, Error>({
    queryKey: ['executive-summary', experimentId],
    queryFn: () => getExecutiveSummary(experimentId),
    enabled: options?.enabled !== false,

    // Auto-refresh every 15s if summary is pending or partial
    refetchInterval: (query) => {
      const summary = query.state.data;
      return summary?.status === 'pending' || summary?.status === 'partial' ? 15000 : false;
    },

    // Cache for 5 minutes for completed summaries
    staleTime: (query) => {
      const summary = query.state.data;
      return summary?.status === 'completed' ? 5 * 60 * 1000 : 0;
    },

    // Don't refetch on window focus for completed summaries
    refetchOnWindowFocus: (query) => {
      const summary = query.state.data;
      return summary?.status !== 'completed';
    },

    // Retry on network errors, but not on 404 (summary not generated yet)
    retry: (failureCount, error) => {
      if (error.message?.includes('404')) {
        return false;
      }
      return failureCount < 3;
    },
  });
}

/**
 * Hook for fetching AI-generated chart insights.
 *
 * Provides auto-refresh for pending insights and caching for completed ones.
 *
 * References:
 *   - API: src/services/insights-api.ts
 *   - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 1)
 *
 * Features:
 *   - Auto-refresh every 10s for pending insights
 *   - 5-minute cache for completed insights
 *   - Error handling
 */

import { useQuery } from '@tanstack/react-query';
import { getChartInsight } from '@/services/insights-api';
import { APIError } from '@/services/api';
import type { ChartInsight } from '@/types/insights';

interface UseChartInsightOptions {
  enabled?: boolean;
}

export function useChartInsight(
  experimentId: string,
  chartType: string,
  options?: UseChartInsightOptions
) {
  return useQuery<ChartInsight, APIError>({
    queryKey: ['chart-insight', experimentId, chartType],
    queryFn: () => getChartInsight(experimentId, chartType),
    enabled: options?.enabled !== false,

    // Auto-refresh every 10s if insight is pending
    refetchInterval: (query) => {
      const insight = query.state.data;
      return insight?.status === 'pending' ? 10000 : false;
    },

    // Cache for 5 minutes for completed insights
    staleTime: (query) => {
      const insight = query.state.data;
      return insight?.status === 'completed' ? 5 * 60 * 1000 : 0;
    },

    // Don't refetch on window focus for completed insights or 404 errors
    refetchOnWindowFocus: (query) => {
      const insight = query.state.data;
      const error = query.state.error;
      // Don't refetch if completed or if we got 404 (insight not generated yet)
      if (insight?.status === 'completed' || error?.status === 404) {
        return false;
      }
      return true;
    },

    // Retry on network errors, but not on 404 (insight not generated yet)
    retry: (failureCount, error) => {
      if (error.status === 404) {
        return false;
      }
      return failureCount < 3;
    },
  });
}

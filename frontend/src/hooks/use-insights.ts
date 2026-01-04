// frontend/src/hooks/use-insights.ts
// React Query hooks for LLM-generated insights

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getAnalysisInsights,
  generateAnalysisChartInsight,
  generateAnalysisExecutiveSummary,
} from '@/services/experiments-api';

export function useAnalysisInsights(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.insights(experimentId),
    queryFn: () => getAnalysisInsights(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useGenerateAnalysisChartInsight(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      chartType,
      chartData,
    }: {
      chartType: string;
      chartData: Record<string, unknown>;
    }) => generateAnalysisChartInsight(experimentId, chartType, chartData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.insights(experimentId) });
    },
  });
}

export function useGenerateAnalysisExecutiveSummary(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => generateAnalysisExecutiveSummary(experimentId),
    onSuccess: () => {
      // Invalidate caches - polling is handled automatically by useDocumentAvailability
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.insights(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.availability(experimentId) });
    },
  });
}

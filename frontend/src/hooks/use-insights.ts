// frontend/src/hooks/use-insights.ts
// React Query hooks for LLM-generated insights

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getSimulationInsights,
  generateChartInsight,
  generateExecutiveSummary,
  clearInsights,
} from '@/services/simulation-api';
import {
  getAnalysisInsights,
  generateAnalysisChartInsight,
  generateAnalysisExecutiveSummary,
} from '@/services/experiments-api';
import type { ChartType } from '@/types/simulation';

export function useSimulationInsights(simulationId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation.insights(simulationId),
    queryFn: () => getSimulationInsights(simulationId),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useGenerateChartInsight(simulationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      chartType,
      chartData,
      forceRegenerate = false,
    }: {
      chartType: ChartType;
      chartData: Record<string, unknown>;
      forceRegenerate?: boolean;
    }) => generateChartInsight(simulationId, chartType, chartData, forceRegenerate),
    onSuccess: () => {
      // Invalidate insights to refetch all
      queryClient.invalidateQueries({ queryKey: queryKeys.simulation.insights(simulationId) });
    },
  });
}

export function useGenerateExecutiveSummary(simulationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => generateExecutiveSummary(simulationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.simulation.insights(simulationId) });
    },
  });
}

export function useClearInsights(simulationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => clearInsights(simulationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.simulation.insights(simulationId) });
    },
  });
}

// =============================================================================
// Analysis Insights Hooks (using experiment ID)
// =============================================================================

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

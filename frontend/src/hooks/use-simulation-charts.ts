// frontend/src/hooks/use-simulation-charts.ts
// React Query hooks for experiment analysis chart data

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getAnalysisDistributionChart,
  getAnalysisFailureHeatmap,
  getAnalysisScatterCorrelation,
} from '@/services/experiments-api';

// =============================================================================
// Phase 1: Overview Charts
// =============================================================================

export function useDistributionChart(
  experimentId: string,
  sortBy = 'adopted_rate',
  order = 'desc',
  limit = 50,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.distribution(experimentId), sortBy, order, limit],
    queryFn: () => getAnalysisDistributionChart(experimentId, sortBy, order, limit),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

// =============================================================================
// Phase 2: Problem Location Charts
// =============================================================================

export function useFailureHeatmap(
  experimentId: string,
  xAxis = 'capability_mean',
  yAxis = 'trust_mean',
  bins = 5,
  metric = 'not_adopted_rate',
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.failureHeatmap(experimentId), xAxis, yAxis, bins, metric],
    queryFn: () => getAnalysisFailureHeatmap(experimentId, xAxis, yAxis, bins, metric),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useScatterCorrelation(
  experimentId: string,
  xAxis = 'trust_mean',
  yAxis = 'adopted_rate',
  showTrendline = true,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.scatter(experimentId), xAxis, yAxis, showTrendline],
    queryFn: () => getAnalysisScatterCorrelation(experimentId, xAxis, yAxis, showTrendline),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}


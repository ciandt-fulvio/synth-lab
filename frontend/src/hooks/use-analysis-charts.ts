// frontend/src/hooks/use-analysis-charts.ts
// React Query hooks for experiment analysis chart data

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getAnalysisDistributionChart,
  getAnalysisFailureHeatmap,
  getAnalysisScatterCorrelation,
  // Phase 3: Edge Cases
  getAnalysisExtremeCases,
  getAnalysisOutliers,
  // Explainability
  getAnalysisShapSummary,
  getAnalysisShapExplanation,
} from '@/services/experiments-api';

// =============================================================================
// Phase 1: Overview Charts
// =============================================================================

export function useAnalysisDistributionChart(
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

export function useAnalysisFailureHeatmap(
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

export function useAnalysisScatterCorrelation(
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

// =============================================================================
// Phase 3: Edge Cases & Outliers
// =============================================================================

export function useAnalysisExtremeCases(
  experimentId: string,
  nPerCategory = 10,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.extremeCases(experimentId), nPerCategory],
    queryFn: () => getAnalysisExtremeCases(experimentId, nPerCategory),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useAnalysisOutliers(
  experimentId: string,
  contamination = 0.1,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.outliers(experimentId), contamination],
    queryFn: () => getAnalysisOutliers(experimentId, contamination),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

// =============================================================================
// Explainability (SHAP)
// =============================================================================

export function useAnalysisShapSummary(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.shapSummary(experimentId),
    queryFn: () => getAnalysisShapSummary(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useAnalysisShapExplanation(
  experimentId: string,
  synthId: string,
  enabled = true
) {
  return useQuery({
    queryKey: queryKeys.analysis.shapExplanation(experimentId, synthId),
    queryFn: () => getAnalysisShapExplanation(experimentId, synthId),
    enabled: !!experimentId && !!synthId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

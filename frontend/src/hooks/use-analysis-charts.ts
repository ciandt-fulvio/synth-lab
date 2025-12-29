// frontend/src/hooks/use-analysis-charts.ts
// React Query hooks for experiment analysis chart data

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getAnalysisTryVsSuccessChart,
  getAnalysisDistributionChart,
  getAnalysisSankeyChart,
  getAnalysisFailureHeatmap,
  getAnalysisScatterCorrelation,
  getAnalysisAttributeCorrelations,
  createAnalysisClustering,
  getAnalysisClustering,
  getAnalysisElbow,
  getAnalysisDendrogram,
  getAnalysisRadarComparison,
  cutAnalysisDendrogram,
  // Phase 4: Edge Cases
  getAnalysisExtremeCases,
  getAnalysisOutliers,
  // Phase 5: Explainability
  getAnalysisShapSummary,
  getAnalysisShapExplanation,
  getAnalysisPDP,
  getAnalysisPDPComparison,
} from '@/services/experiments-api';
import type { ClusterRequest, CutDendrogramRequest } from '@/types/simulation';

// =============================================================================
// Phase 1: Overview Charts
// =============================================================================

export function useAnalysisTryVsSuccessChart(
  experimentId: string,
  attemptRateThreshold = 0.5,
  successRateThreshold = 0.5,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.tryVsSuccess(experimentId), attemptRateThreshold, successRateThreshold],
    queryFn: () => getAnalysisTryVsSuccessChart(experimentId, attemptRateThreshold, successRateThreshold),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useAnalysisDistributionChart(
  experimentId: string,
  sortBy = 'success_rate',
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

export function useAnalysisSankeyChart(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.sankey(experimentId),
    queryFn: () => getAnalysisSankeyChart(experimentId),
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
  metric = 'failed_rate',
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
  yAxis = 'success_rate',
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

export function useAnalysisAttributeCorrelations(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.attributeCorrelations(experimentId),
    queryFn: () => getAnalysisAttributeCorrelations(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

// =============================================================================
// Phase 3: Clustering
// =============================================================================

export function useAnalysisClustering(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.clusters(experimentId),
    queryFn: () => getAnalysisClustering(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCreateAnalysisClustering(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ClusterRequest) => createAnalysisClustering(experimentId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.clusters(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.elbow(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.radarComparison(experimentId) });
    },
  });
}

export function useAnalysisElbow(experimentId: string, maxK = 10, enabled = true) {
  return useQuery({
    queryKey: [...queryKeys.analysis.elbow(experimentId), maxK],
    queryFn: () => getAnalysisElbow(experimentId, maxK),
    enabled: !!experimentId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useAnalysisDendrogram(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.dendrogram(experimentId),
    queryFn: () => getAnalysisDendrogram(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useAnalysisRadarComparison(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.radarComparison(experimentId),
    queryFn: () => getAnalysisRadarComparison(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCutAnalysisDendrogram(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CutDendrogramRequest) => cutAnalysisDendrogram(experimentId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.clusters(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.dendrogram(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis.radarComparison(experimentId) });
    },
  });
}

// =============================================================================
// Phase 4: Edge Cases & Outliers
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
// Phase 5: Explainability (SHAP & PDP)
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

export function useAnalysisPDP(
  experimentId: string,
  feature: string,
  gridResolution = 20,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.pdp(experimentId, feature), gridResolution],
    queryFn: () => getAnalysisPDP(experimentId, feature, gridResolution),
    enabled: !!experimentId && !!feature && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function useAnalysisPDPComparison(
  experimentId: string,
  features: string[],
  gridResolution = 20,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.analysis.pdpComparison(experimentId), features, gridResolution],
    queryFn: () => getAnalysisPDPComparison(experimentId, features, gridResolution),
    enabled: !!experimentId && features.length > 0 && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

// frontend/src/hooks/use-analysis-charts.ts
// React Query hooks for experiment analysis chart data

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getAnalysisTryVsSuccessChart,
  getAnalysisDistributionChart,
  getAnalysisSankeyChart,
} from '@/services/experiments-api';

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

// frontend/src/hooks/use-explainability.ts
// React Query hooks for SHAP and PDP explainability

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getAnalysisShapSummary,
  getAnalysisShapExplanation,
  getAnalysisPDP,
  getAnalysisPDPComparison,
} from '@/services/experiments-api';

// =============================================================================
// SHAP Hooks
// =============================================================================

export function useShapSummary(experimentId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analysis.shapSummary(experimentId),
    queryFn: () => getAnalysisShapSummary(experimentId),
    enabled: !!experimentId && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes (SHAP is expensive)
  });
}

export function useShapExplanation(
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

// =============================================================================
// PDP Hooks
// =============================================================================

export function usePDP(
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

export function usePDPComparison(
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

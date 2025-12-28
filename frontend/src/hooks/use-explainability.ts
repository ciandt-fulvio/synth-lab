// frontend/src/hooks/use-explainability.ts
// React Query hooks for SHAP and PDP explainability

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getShapSummary,
  getShapExplanation,
  getPDP,
  getPDPComparison,
} from '@/services/simulation-api';

// =============================================================================
// SHAP Hooks
// =============================================================================

export function useShapSummary(simulationId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation.shapSummary(simulationId),
    queryFn: () => getShapSummary(simulationId),
    enabled: !!simulationId && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes (SHAP is expensive)
  });
}

export function useShapExplanation(
  simulationId: string,
  synthId: string,
  enabled = true
) {
  return useQuery({
    queryKey: queryKeys.simulation.shapExplanation(simulationId, synthId),
    queryFn: () => getShapExplanation(simulationId, synthId),
    enabled: !!simulationId && !!synthId && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

// =============================================================================
// PDP Hooks
// =============================================================================

export function usePDP(
  simulationId: string,
  feature: string,
  gridResolution = 20,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.simulation.pdp(simulationId, feature), gridResolution],
    queryFn: () => getPDP(simulationId, feature, gridResolution),
    enabled: !!simulationId && !!feature && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

export function usePDPComparison(
  simulationId: string,
  features: string[],
  gridResolution = 20,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.simulation.pdpComparison(simulationId), features, gridResolution],
    queryFn: () => getPDPComparison(simulationId, features, gridResolution),
    enabled: !!simulationId && features.length > 0 && enabled,
    staleTime: 10 * 60 * 1000,
  });
}

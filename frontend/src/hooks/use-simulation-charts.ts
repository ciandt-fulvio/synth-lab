// frontend/src/hooks/use-simulation-charts.ts
// React Query hooks for simulation chart data

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  getTryVsSuccessChart,
  getDistributionChart,
  getSankeyChart,
  getFailureHeatmap,
  getBoxPlotChart,
  getScatterCorrelation,
  getTornadoChart,
} from '@/services/simulation-api';

// =============================================================================
// Phase 1: Overview Charts
// =============================================================================

export function useTryVsSuccessChart(
  simulationId: string,
  attemptRateThreshold = 0.5,
  successRateThreshold = 0.5,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.simulation.tryVsSuccess(simulationId), attemptRateThreshold, successRateThreshold],
    queryFn: () => getTryVsSuccessChart(simulationId, attemptRateThreshold, successRateThreshold),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useDistributionChart(
  simulationId: string,
  sortBy = 'success_rate',
  order = 'desc',
  limit = 50,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.simulation.distribution(simulationId), sortBy, order, limit],
    queryFn: () => getDistributionChart(simulationId, sortBy, order, limit),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useSankeyChart(simulationId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation.sankey(simulationId),
    queryFn: () => getSankeyChart(simulationId),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

// =============================================================================
// Phase 2: Problem Location Charts
// =============================================================================

export function useFailureHeatmap(
  simulationId: string,
  xAxis = 'capability_mean',
  yAxis = 'trust_mean',
  bins = 5,
  metric = 'failed_rate',
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.simulation.failureHeatmap(simulationId), xAxis, yAxis, bins, metric],
    queryFn: () => getFailureHeatmap(simulationId, xAxis, yAxis, bins, metric),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useBoxPlotChart(
  simulationId: string,
  attribute = 'trust_mean',
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.simulation.boxPlot(simulationId), attribute],
    queryFn: () => getBoxPlotChart(simulationId, attribute),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useScatterCorrelation(
  simulationId: string,
  xAxis = 'trust_mean',
  yAxis = 'success_rate',
  showTrendline = true,
  enabled = true
) {
  return useQuery({
    queryKey: [...queryKeys.simulation.scatter(simulationId), xAxis, yAxis, showTrendline],
    queryFn: () => getScatterCorrelation(simulationId, xAxis, yAxis, showTrendline),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useTornadoChart(simulationId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.simulation.tornado(simulationId),
    queryFn: () => getTornadoChart(simulationId),
    enabled: !!simulationId && enabled,
    staleTime: 5 * 60 * 1000,
  });
}

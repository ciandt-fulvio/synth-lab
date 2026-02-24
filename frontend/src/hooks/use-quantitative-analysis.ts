/**
 * useQuantitativeAnalysis hooks.
 *
 * React Query hooks for causal model generation, edge selection, and simulation.
 *
 * References:
 *   - API: src/services/quantitative-analysis-api.ts
 *   - Types: src/types/quantitative-analysis.ts
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  generateCausalModel,
  getCausalModel,
  updateEdgeSelections,
  updateNodeSelections,
  runBatchSimulation,
  getLatestBatch,
  getSynthProfiles,
  getProductSynthCorrelations,
  getSynthAttributeInsights,
  generateInterviewGuide,
  generateSimulationSummary,
  getInterviewGuide,
  getSimulationReport,
} from '@/services/quantitative-analysis-api';

/**
 * Hook to fetch the current causal model for an experiment.
 */
export function useCausalModel(experimentId: string) {
  return useQuery({
    queryKey: queryKeys.quantitativeAnalysis.model(experimentId),
    queryFn: () => getCausalModel(experimentId),
    enabled: !!experimentId,
    retry: false,
  });
}

/**
 * Hook to generate a causal model via LLM.
 *
 * Invalidates the model query on success.
 */
export function useGenerateCausalModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (experimentId: string) => generateCausalModel(experimentId),
    onSuccess: (_, experimentId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.quantitativeAnalysis.model(experimentId),
      });
    },
  });
}

/**
 * Hook to update edge selections with debounced persistence.
 *
 * Optimistically updates the local model cache for instant UI feedback.
 */
export function useUpdateEdgeSelections(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (selections: Record<string, number>) =>
      updateEdgeSelections(experimentId, selections),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.quantitativeAnalysis.model(experimentId),
      });
    },
  });
}

/**
 * Hook to update premissa selections for interaction/outcome nodes.
 *
 * Invalidates the model query on success.
 */
export function useUpdateNodeSelections(experimentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (selections: Record<string, number>) =>
      updateNodeSelections(experimentId, selections),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.quantitativeAnalysis.model(experimentId),
      });
    },
  });
}

/**
 * Hook to run multi-scenario batch simulation.
 *
 * Invalidates results queries on success.
 */
export function useRunBatchSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (experimentId: string) => runBatchSimulation(experimentId),
    onSuccess: (_, experimentId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.quantitativeAnalysis.results(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.quantitativeAnalysis.report(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: ['experiments', experimentId, 'interview-guide'],
      });
    },
  });
}

/**
 * Hook to generate interview guide from latest simulation sensitivity.
 *
 * Invalidates experiment detail query to update has_interview_guide.
 */
export function useGenerateInterviewGuide() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (experimentId: string) => generateInterviewGuide(experimentId),
    onSuccess: (_, experimentId) => {
      queryClient.invalidateQueries({
        queryKey: ['experiments', experimentId],
      });
      queryClient.invalidateQueries({
        queryKey: ['experiments', experimentId, 'interview-guide'],
      });
    },
  });
}

/**
 * Hook to generate or regenerate the simulation summary report.
 *
 * Invalidates document availability and list queries on success.
 */
export function useGenerateSimulationSummary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (experimentId: string) => generateSimulationSummary(experimentId),
    onSuccess: (_, experimentId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.availability(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.list(experimentId),
      });
    },
  });
}

/**
 * Hook to fetch the latest simulation batch for an experiment.
 */
export function useLatestBatch(experimentId: string) {
  return useQuery({
    queryKey: queryKeys.quantitativeAnalysis.results(experimentId),
    queryFn: () => getLatestBatch(experimentId),
    enabled: !!experimentId,
    retry: false,
  });
}

/**
 * Hook to fetch synth profile analysis for an experiment.
 */
export function useSynthProfiles(experimentId: string) {
  return useQuery({
    queryKey: ['quantitative-analysis', experimentId, 'synth-profiles'],
    queryFn: () => getSynthProfiles(experimentId),
    enabled: !!experimentId,
    retry: false,
  });
}

/**
 * Hook to fetch product × synth-cluster correlations for an experiment.
 */
export function useProductSynthCorrelations(experimentId: string) {
  return useQuery({
    queryKey: ['quantitative-analysis', experimentId, 'product-synth-correlations'],
    queryFn: () => getProductSynthCorrelations(experimentId),
    enabled: !!experimentId,
    retry: false,
  });
}

/**
 * Hook to fetch synth attribute correlation and heatmap insights.
 */
export function useSynthAttributeInsights(experimentId: string) {
  return useQuery({
    queryKey: ['quantitative-analysis', experimentId, 'synth-attribute-insights'],
    queryFn: () => getSynthAttributeInsights(experimentId),
    enabled: !!experimentId,
    retry: false,
  });
}

/**
 * Hook to fetch the interview guide markdown for an experiment.
 *
 * Polls every 4 seconds when:
 * - Guide is null (being regenerated — old guide was deleted, new one not yet ready)
 * - Guide exists but is older than latestBatchCreatedAt (stale, new batch ran)
 */
export function useInterviewGuide(
  experimentId: string,
  enabled = true,
  latestBatchCreatedAt?: string | null,
) {
  return useQuery({
    queryKey: ['experiments', experimentId, 'interview-guide'],
    queryFn: () => getInterviewGuide(experimentId),
    enabled: !!experimentId && enabled,
    retry: false,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data === null) return 4000;
      if (
        data &&
        latestBatchCreatedAt &&
        data.created_at &&
        new Date(data.created_at) < new Date(latestBatchCreatedAt)
      ) return 4000;
      return false;
    },
  });
}

/**
 * Hook to fetch the latest LLM-generated simulation report for an experiment.
 *
 * Polls every 4 seconds while report is not yet available (null), so the UI
 * auto-updates when the background generation completes.
 */
export function useSimulationReport(experimentId: string) {
  return useQuery({
    queryKey: queryKeys.quantitativeAnalysis.report(experimentId),
    queryFn: () => getSimulationReport(experimentId),
    enabled: !!experimentId,
    retry: false,
    refetchInterval: (query) => (query.state.data === null ? 4000 : false),
  });
}

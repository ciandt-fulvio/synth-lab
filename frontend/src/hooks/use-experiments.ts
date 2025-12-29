/**
 * T021 useExperiments hook.
 *
 * React Query hooks for experiment CRUD operations.
 *
 * References:
 *   - API: src/services/experiments-api.ts
 *   - Types: src/types/experiment.ts
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  listExperiments,
  getExperiment,
  createExperiment,
  updateExperiment,
  deleteExperiment,
  createScorecardForExperiment,
  createInterviewForExperiment,
  getAutoInterview,
  createAutoInterview,
  estimateScorecardForExperiment,
  estimateScorecardFromText,
  runAnalysis,
  type ScorecardEstimateRequest,
  type RunAnalysisRequest,
} from '@/services/experiments-api';
import type { PaginationParams } from '@/types';
import type { ExperimentCreate, ExperimentUpdate, ScorecardCreate } from '@/types/experiment';
import type { InterviewCreateRequest } from '@/types/research';

/**
 * Hook to fetch paginated list of experiments.
 */
export function useExperiments(params?: PaginationParams) {
  return useQuery({
    queryKey: [...queryKeys.experimentsList, params],
    queryFn: () => listExperiments(params),
  });
}

/**
 * Hook to fetch experiment details by ID.
 */
export function useExperiment(id: string) {
  return useQuery({
    queryKey: queryKeys.experimentDetail(id),
    queryFn: () => getExperiment(id),
    enabled: !!id,
  });
}

// Type for experiment list cache data
type ExperimentListCache = {
  data: Array<{
    id: string;
    name: string;
    hypothesis: string;
    description?: string | null;
    has_scorecard: boolean;
    has_analysis: boolean;
    has_interview_guide: boolean;
    interview_count: number;
    created_at: string;
    updated_at?: string | null;
    _isOptimistic?: boolean;
  }>;
  pagination: { total: number; limit: number; offset: number };
};

/**
 * Hook to create a new experiment with optimistic update.
 *
 * Shows the experiment card immediately while the API call is in progress.
 * Rolls back if the creation fails.
 */
export function useCreateExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExperimentCreate) => createExperiment(data),

    // Optimistic update: add placeholder to cache immediately
    onMutate: async (newExperiment) => {
      // Cancel any outgoing refetches to avoid overwriting our optimistic update
      await queryClient.cancelQueries({ queryKey: queryKeys.experimentsList });

      // Get all experiment list queries (they include params in the key)
      const queries = queryClient.getQueriesData<ExperimentListCache>({
        queryKey: queryKeys.experimentsList,
      });

      // Snapshot all queries for rollback
      const previousQueries = queries.map(([key, data]) => ({ key, data }));

      // Create optimistic experiment with temporary ID
      const optimisticExperiment = {
        id: `temp_${Date.now()}`,
        name: newExperiment.name,
        hypothesis: newExperiment.hypothesis,
        description: newExperiment.description ?? null,
        has_scorecard: !!newExperiment.scorecard_data,
        has_analysis: false,
        has_interview_guide: false,
        interview_count: 0,
        created_at: new Date().toISOString(),
        updated_at: null,
        _isOptimistic: true,
      };

      // Update all experiment list caches
      queries.forEach(([key, data]) => {
        if (data) {
          queryClient.setQueryData(key, {
            ...data,
            data: [optimisticExperiment, ...data.data],
            pagination: {
              ...data.pagination,
              total: data.pagination.total + 1,
            },
          });
        }
      });

      return { previousQueries };
    },

    // On success: replace optimistic item with real data
    onSuccess: (createdExperiment) => {
      const queries = queryClient.getQueriesData<ExperimentListCache>({
        queryKey: queryKeys.experimentsList,
      });

      queries.forEach(([key, data]) => {
        if (data) {
          const newData = data.data.map((exp) =>
            exp._isOptimistic
              ? {
                  id: createdExperiment.id,
                  name: createdExperiment.name,
                  hypothesis: createdExperiment.hypothesis,
                  description: createdExperiment.description ?? null,
                  has_scorecard: createdExperiment.has_scorecard,
                  has_analysis: !!createdExperiment.analysis,
                  has_interview_guide: createdExperiment.has_interview_guide,
                  interview_count: createdExperiment.interview_count,
                  created_at: createdExperiment.created_at,
                  updated_at: createdExperiment.updated_at ?? null,
                }
              : exp
          );
          queryClient.setQueryData(key, { ...data, data: newData });
        }
      });
    },

    // On error: rollback to previous state
    onError: (_err, _newExperiment, context) => {
      context?.previousQueries?.forEach(({ key, data }) => {
        queryClient.setQueryData(key, data);
      });
    },

    // Always refetch after error or success to ensure consistency
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.experimentsList });
    },
  });
}

/**
 * Hook to update an existing experiment.
 */
export function useUpdateExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ExperimentUpdate }) =>
      updateExperiment(id, data),
    onSuccess: (_, variables) => {
      // Invalidate specific experiment and list
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentDetail(variables.id),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.experimentsList });
    },
  });
}

/**
 * Hook to delete an experiment.
 */
export function useDeleteExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteExperiment(id),
    onSuccess: (_, id) => {
      // Invalidate specific experiment and list
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentDetail(id),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.experimentsList });
    },
  });
}

/**
 * Hook to create a scorecard linked to an experiment.
 */
export function useCreateScorecardForExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ experimentId, data }: { experimentId: string; data: ScorecardCreate }) =>
      createScorecardForExperiment(experimentId, data),
    onSuccess: (_, variables) => {
      // Invalidate experiment detail to show the new scorecard
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentDetail(variables.experimentId),
      });
    },
  });
}

/**
 * Hook to create an interview linked to an experiment.
 */
export function useCreateInterviewForExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ experimentId, data }: { experimentId: string; data: InterviewCreateRequest }) =>
      createInterviewForExperiment(experimentId, data),
    onSuccess: (_, variables) => {
      // Invalidate experiment detail to show the new interview
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentDetail(variables.experimentId),
      });
    },
  });
}

/**
 * Hook to check if an auto-interview exists for an experiment.
 */
export function useAutoInterview(experimentId: string) {
  return useQuery({
    queryKey: queryKeys.autoInterview(experimentId),
    queryFn: () => getAutoInterview(experimentId),
    enabled: !!experimentId,
  });
}

/**
 * Hook to create an automatic interview with extreme cases (top 5 + bottom 5).
 */
export function useCreateAutoInterview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (experimentId: string) => createAutoInterview(experimentId),
    onSuccess: (_, experimentId) => {
      // Invalidate experiment detail and auto-interview query
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentDetail(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.autoInterview(experimentId),
      });
    },
  });
}

/**
 * Hook to estimate scorecard dimensions using AI for an existing experiment.
 */
export function useEstimateScorecardForExperiment() {
  return useMutation({
    mutationFn: (experimentId: string) => estimateScorecardForExperiment(experimentId),
  });
}

/**
 * Hook to estimate scorecard dimensions from text input (before experiment exists).
 */
export function useEstimateScorecardFromText() {
  return useMutation({
    mutationFn: (data: ScorecardEstimateRequest) => estimateScorecardFromText(data),
  });
}

/**
 * Hook to run quantitative analysis for an experiment.
 *
 * Creates and executes a Monte Carlo simulation.
 * On success, invalidates experiment detail to refresh analysis data.
 */
export function useRunAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ experimentId, config }: { experimentId: string; config?: RunAnalysisRequest }) =>
      runAnalysis(experimentId, config),
    onSuccess: (_, variables) => {
      // Invalidate experiment detail to show the new analysis
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentDetail(variables.experimentId),
      });
    },
  });
}

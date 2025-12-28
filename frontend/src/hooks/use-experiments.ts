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

/**
 * Hook to create a new experiment.
 */
export function useCreateExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExperimentCreate) => createExperiment(data),
    onSuccess: () => {
      // Invalidate experiments list to show the new experiment
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

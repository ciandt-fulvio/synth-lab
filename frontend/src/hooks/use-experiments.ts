/**
 * useExperiments hook.
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
  createInterviewForExperiment,
  getAutoInterview,
  createAutoInterview,
  type ExperimentsListParams,
} from '@/services/experiments-api';
import type { ExperimentCreate, ExperimentUpdate } from '@/types/experiment';
import type { InterviewCreateRequest } from '@/types/research';

/**
 * Hook to fetch paginated list of experiments with search and sort.
 */
export function useExperiments(params?: ExperimentsListParams) {
  return useQuery({
    queryKey: [...queryKeys.experimentsList, params],
    queryFn: () => listExperiments(params),
    placeholderData: (previousData) => previousData,
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
 */
export function useCreateExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExperimentCreate) => createExperiment(data),

    onMutate: async (newExperiment) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.experimentsList });

      const queries = queryClient.getQueriesData<ExperimentListCache>({
        queryKey: queryKeys.experimentsList,
      });

      const previousQueries = queries.map(([key, data]) => ({ key, data }));

      const optimisticExperiment = {
        id: `temp_${Date.now()}`,
        name: newExperiment.name,
        hypothesis: newExperiment.hypothesis,
        description: newExperiment.description ?? null,
        has_interview_guide: false,
        interview_count: 0,
        created_at: new Date().toISOString(),
        updated_at: null,
        _isOptimistic: true,
      };

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

    onError: (_err, _newExperiment, context) => {
      context?.previousQueries?.forEach(({ key, data }) => {
        queryClient.setQueryData(key, data);
      });
    },

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
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentDetail(id),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.experimentsList });
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
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentDetail(experimentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.autoInterview(experimentId),
      });
    },
  });
}

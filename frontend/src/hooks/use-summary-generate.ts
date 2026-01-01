// src/hooks/use-summary-generate.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { generateSummary, SummaryGenerateRequest } from '@/services/research-api';
import type { DocumentAvailability } from '@/types/document';

/**
 * Hook for generating Summary with proper cache invalidation.
 *
 * Features:
 * - Optimistic update to show "generating" state immediately
 * - Handles 400 errors (invalid state) gracefully
 * - Invalidates artifact states, research detail, and summary caches
 * - Provides isPending state for loading indicators
 *
 * @param execId - Execution ID for cache invalidation
 * @param experimentId - Experiment ID for document cache invalidation (optional)
 * @returns Mutation object with mutate, isPending, isError, etc.
 */
export function useSummaryGenerate(execId: string, experimentId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request?: Partial<SummaryGenerateRequest>) =>
      generateSummary(execId, {
        model: request?.model ?? 'gpt-5',
      }),
    onMutate: async () => {
      // Optimistic update: immediately show "generating" state
      if (!experimentId) return;

      // Cancel outgoing refetches to avoid overwriting optimistic update
      await queryClient.cancelQueries({
        queryKey: queryKeys.documents.availability(experimentId),
      });

      // Snapshot previous value for rollback
      const previousData = queryClient.getQueryData<DocumentAvailability>(
        queryKeys.documents.availability(experimentId)
      );

      // Optimistically update to "generating"
      queryClient.setQueryData<DocumentAvailability>(
        queryKeys.documents.availability(experimentId),
        (old) =>
          old
            ? {
                ...old,
                summary: { available: false, status: 'generating' },
              }
            : undefined
      );

      return { previousData };
    },
    onSuccess: () => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.researchDetail(execId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.researchSummary(execId) });
      // Force refetch document availability to start polling
      if (experimentId) {
        queryClient.refetchQueries({ queryKey: queryKeys.documents.availability(experimentId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.documents.markdown(experimentId, 'summary') });
      }
    },
    onError: (error: Error & { status?: number }, _variables, context) => {
      // Rollback optimistic update on error
      if (experimentId && context?.previousData) {
        queryClient.setQueryData(
          queryKeys.documents.availability(experimentId),
          context.previousData
        );
      }
      // Refresh the artifact states to get current status
      queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId) });
    },
  });
}

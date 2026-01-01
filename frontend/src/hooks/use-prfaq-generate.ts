// src/hooks/use-prfaq-generate.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { generatePrfaq } from '@/services/prfaq-api';
import type { PRFAQGenerateRequest } from '@/types';
import type { DocumentAvailability } from '@/types/document';

/**
 * Hook for generating PR-FAQ with proper cache invalidation.
 *
 * Features:
 * - Optimistic update to show "generating" state immediately
 * - Handles 409 Conflict (already generating) gracefully
 * - Invalidates artifact states, research detail, and prfaq markdown caches
 * - Provides isPending state for loading indicators
 *
 * @param execId - Execution ID for cache invalidation
 * @param experimentId - Experiment ID for document cache invalidation (optional)
 * @returns Mutation object with mutate, isPending, isError, etc.
 */
export function usePrfaqGenerate(execId: string, experimentId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request?: Partial<PRFAQGenerateRequest>) =>
      generatePrfaq({
        exec_id: execId,
        model: request?.model ?? 'gpt-4o-mini',
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
                prfaq: { available: false, status: 'generating' },
              }
            : undefined
      );

      return { previousData };
    },
    onSuccess: () => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.researchDetail(execId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.prfaqMarkdown(execId) });
      // Force refetch document availability to start polling
      if (experimentId) {
        queryClient.refetchQueries({ queryKey: queryKeys.documents.availability(experimentId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.documents.markdown(experimentId, 'prfaq') });
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
      // On 409 (already generating), just refresh the artifact states
      if (error.status === 409) {
        queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId) });
      }
    },
  });
}

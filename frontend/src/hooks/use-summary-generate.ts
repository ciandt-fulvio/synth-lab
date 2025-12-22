// src/hooks/use-summary-generate.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { generateSummary, SummaryGenerateRequest } from '@/services/research-api';

/**
 * Hook for generating Summary with proper cache invalidation.
 *
 * Features:
 * - Handles 400 errors (invalid state) gracefully
 * - Invalidates artifact states, research detail, and summary caches
 * - Provides isPending state for loading indicators
 *
 * @param execId - Execution ID for cache invalidation
 * @returns Mutation object with mutate, isPending, isError, etc.
 */
export function useSummaryGenerate(execId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request?: Partial<SummaryGenerateRequest>) =>
      generateSummary(execId, {
        model: request?.model ?? 'gpt-5',
      }),
    onSuccess: () => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.researchDetail(execId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.researchSummary(execId) });
    },
    onError: (error: Error & { status?: number }) => {
      // On error, refresh the artifact states to get current status
      queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId) });
    },
  });
}

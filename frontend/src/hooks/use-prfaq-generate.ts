// src/hooks/use-prfaq-generate.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { generatePrfaq } from '@/services/prfaq-api';
import type { PRFAQGenerateRequest } from '@/types';

/**
 * Hook for generating PR-FAQ with proper cache invalidation.
 *
 * Features:
 * - Handles 409 Conflict (already generating) gracefully
 * - Invalidates artifact states, research detail, and prfaq markdown caches
 * - Provides isPending state for loading indicators
 *
 * @param execId - Execution ID for cache invalidation
 * @returns Mutation object with mutate, isPending, isError, etc.
 */
export function usePrfaqGenerate(execId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request?: Partial<PRFAQGenerateRequest>) =>
      generatePrfaq({
        exec_id: execId,
        model: request?.model ?? 'gpt-4o-mini',
      }),
    onSuccess: () => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.researchDetail(execId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.prfaqMarkdown(execId) });
    },
    onError: (error: Error & { status?: number }) => {
      // On 409 (already generating), just refresh the artifact states
      if (error.status === 409) {
        queryClient.invalidateQueries({ queryKey: queryKeys.artifactStates(execId) });
      }
    },
  });
}

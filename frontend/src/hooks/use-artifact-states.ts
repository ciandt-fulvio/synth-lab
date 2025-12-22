// src/hooks/use-artifact-states.ts

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { getArtifactStates } from '@/services/research-api';
import type { ArtifactStateEnum } from '@/types/artifact-state';

/**
 * Hook to fetch artifact states for a research execution.
 *
 * @param execId - Execution ID
 * @param options - Query options
 * @returns Query result with artifact states
 */
export function useArtifactStates(
  execId: string,
  options?: {
    /** Enable automatic refetching at interval (for polling during generation) */
    refetchInterval?: number | false;
    /** Enable/disable the query */
    enabled?: boolean;
  }
) {
  const { refetchInterval = false, enabled = true } = options ?? {};

  return useQuery({
    queryKey: queryKeys.artifactStates(execId),
    queryFn: () => getArtifactStates(execId),
    enabled: enabled && !!execId,
    refetchInterval,
  });
}

/**
 * Conditional polling hook for artifact states.
 * Automatically polls when any artifact is in 'generating' state.
 *
 * @param execId - Execution ID
 * @param pollingInterval - Polling interval in ms (default: 2000)
 * @returns Query result with artifact states
 */
export function useArtifactStatesWithPolling(
  execId: string,
  pollingInterval: number = 2000
) {
  const query = useArtifactStates(execId, {
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;

      // Poll if any artifact is generating
      const isGenerating =
        data.summary.state === 'generating' ||
        data.prfaq.state === 'generating';

      return isGenerating ? pollingInterval : false;
    },
  });

  return query;
}

/**
 * Helper to determine if an artifact can be viewed.
 */
export function canViewArtifact(state: ArtifactStateEnum): boolean {
  return state === 'available';
}

/**
 * Helper to determine if an artifact can be generated.
 */
export function canGenerateArtifact(
  state: ArtifactStateEnum,
  prerequisiteMet: boolean
): boolean {
  return (
    prerequisiteMet &&
    (state === 'unavailable' || state === 'failed')
  );
}

/**
 * Helper to determine if an artifact is currently being generated.
 */
export function isGeneratingArtifact(state: ArtifactStateEnum): boolean {
  return state === 'generating';
}

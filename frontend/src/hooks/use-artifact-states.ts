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
 * Polls at different rates:
 * - Fast (2s): When any artifact is generating
 * - Slow (10s): When artifacts might start generating (to catch state transitions)
 * - Off: When both artifacts are available or unavailable with unmet prerequisites
 *
 * @param execId - Execution ID
 * @param pollingInterval - Fast polling interval in ms (default: 2000)
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

      // Fast poll if any artifact is generating
      const isGenerating =
        data.summary.state === 'generating' ||
        data.prfaq.state === 'generating';

      if (isGenerating) {
        return pollingInterval; // Fast: 2s
      }

      // Slow poll if artifacts might start generating soon
      // (prerequisites are met but not yet available)
      const mightStartGenerating =
        (data.summary.state === 'unavailable' && data.summary.prerequisite_met) ||
        (data.prfaq.state === 'unavailable' && data.prfaq.prerequisite_met);

      if (mightStartGenerating) {
        return pollingInterval * 5; // Slow: 10s
      }

      // Stop polling if both are available or can't generate
      return false;
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

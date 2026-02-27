/**
 * useSharing hooks.
 *
 * React Query hooks for sharing experiments and synth groups.
 *
 * References:
 *   - API: src/services/sharing-api.ts
 *   - Types: src/types/sharing.ts
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  shareExperiment,
  listExperimentShares,
  revokeExperimentShare,
  shareSynthGroup,
  listSynthGroupShares,
  revokeSynthGroupShare,
} from '@/services/sharing-api';

/**
 * Hook to list all shares and pending invites for an experiment.
 */
export function useExperimentShares(experimentId: string, enabled = false) {
  return useQuery({
    queryKey: queryKeys.experimentShares(experimentId),
    queryFn: () => listExperimentShares(experimentId),
    enabled: !!experimentId && enabled,
  });
}

/**
 * Hook to share an experiment by email.
 */
export function useShareExperiment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ experimentId, email }: { experimentId: string; email: string }) =>
      shareExperiment(experimentId, email),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentShares(variables.experimentId),
      });
    },
  });
}

/**
 * Hook to revoke experiment access by email.
 */
export function useRevokeExperimentShare() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ experimentId, email }: { experimentId: string; email: string }) =>
      revokeExperimentShare(experimentId, email),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.experimentShares(variables.experimentId),
      });
    },
  });
}

/**
 * Hook to list all shares for a synth group.
 */
export function useSynthGroupShares(synthGroupId: string, enabled = false) {
  return useQuery({
    queryKey: queryKeys.synthGroupShares(synthGroupId),
    queryFn: () => listSynthGroupShares(synthGroupId),
    enabled: !!synthGroupId && enabled,
  });
}

/**
 * Hook to share a synth group by email.
 */
export function useShareSynthGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ synthGroupId, email }: { synthGroupId: string; email: string }) =>
      shareSynthGroup(synthGroupId, email),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.synthGroupShares(variables.synthGroupId),
      });
    },
  });
}

/**
 * Hook to revoke synth group access by email.
 */
export function useRevokeSynthGroupShare() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ synthGroupId, email }: { synthGroupId: string; email: string }) =>
      revokeSynthGroupShare(synthGroupId, email),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.synthGroupShares(variables.synthGroupId),
      });
    },
  });
}

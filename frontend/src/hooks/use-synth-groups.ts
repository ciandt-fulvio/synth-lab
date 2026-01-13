/**
 * T022 useSynthGroups hook.
 *
 * React Query hooks for synth group operations.
 *
 * References:
 *   - API: src/services/synth-groups-api.ts
 *   - Types: src/types/synthGroup.ts
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  listSynthGroups,
  getSynthGroup,
  createSynthGroup,
  deleteSynthGroup,
  createSynthGroupWithConfig,
} from '@/services/synth-groups-api';
import type { PaginationParams } from '@/types';
import type { SynthGroupCreate, CreateSynthGroupRequest } from '@/types/synthGroup';

/**
 * Hook to fetch paginated list of synth groups.
 */
export function useSynthGroups(params?: PaginationParams) {
  return useQuery({
    queryKey: [...queryKeys.synthGroupsList, params],
    queryFn: () => listSynthGroups(params),
  });
}

/**
 * Hook to fetch synth group details by ID.
 */
export function useSynthGroup(id: string) {
  return useQuery({
    queryKey: queryKeys.synthGroupDetail(id),
    queryFn: () => getSynthGroup(id),
    enabled: !!id,
  });
}

/**
 * Hook to create a new synth group.
 */
export function useCreateSynthGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SynthGroupCreate) => createSynthGroup(data),
    onSuccess: () => {
      // Invalidate synth groups list to show the new group
      queryClient.invalidateQueries({ queryKey: queryKeys.synthGroupsList });
    },
  });
}

/**
 * Hook to delete a synth group.
 */
export function useDeleteSynthGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteSynthGroup(id),
    onSuccess: (_, id) => {
      // Invalidate specific group and list
      queryClient.invalidateQueries({
        queryKey: queryKeys.synthGroupDetail(id),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.synthGroupsList });
    },
  });
}

/**
 * Hook to create a synth group with custom distribution configuration.
 * Generates N synths using the provided distributions.
 */
export function useCreateSynthGroupWithConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSynthGroupRequest) => createSynthGroupWithConfig(data),
    onSuccess: () => {
      // Invalidate synth groups list to show the new group
      queryClient.invalidateQueries({ queryKey: queryKeys.synthGroupsList });
    },
  });
}

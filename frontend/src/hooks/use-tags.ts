/**
 * React hooks for tag operations.
 *
 * Custom hooks using TanStack Query for tag management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import {
  listTags,
  createTag,
  addTagToExperiment,
  removeTagFromExperiment,
} from '@/services/tags-api';
import type { Tag, TagCreateRequest, AddTagRequest } from '@/types/tag';

/**
 * Hook to list all available tags.
 *
 * @returns Query result with list of tags.
 */
export function useTags() {
  return useQuery<Tag[], Error>({
    queryKey: queryKeys.tags(),
    queryFn: listTags,
  });
}

/**
 * Hook to create a new tag.
 *
 * Invalidates tags query on success.
 *
 * @returns Mutation for creating a tag.
 */
export function useCreateTag() {
  const queryClient = useQueryClient();

  return useMutation<Tag, Error, TagCreateRequest>({
    mutationFn: createTag,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tags() });
    },
  });
}

/**
 * Hook to add a tag to an experiment.
 *
 * Invalidates experiments queries on success.
 *
 * @returns Mutation for adding a tag to an experiment.
 */
export function useAddTagToExperiment() {
  const queryClient = useQueryClient();

  return useMutation<
    void,
    Error,
    { experimentId: string; data: AddTagRequest }
  >({
    mutationFn: ({ experimentId, data }) => addTagToExperiment(experimentId, data),
    onSuccess: () => {
      // Invalidate experiments list and detail queries
      queryClient.invalidateQueries({ queryKey: queryKeys.experiments() });
    },
  });
}

/**
 * Hook to remove a tag from an experiment.
 *
 * Invalidates experiments queries on success.
 *
 * @returns Mutation for removing a tag from an experiment.
 */
export function useRemoveTagFromExperiment() {
  const queryClient = useQueryClient();

  return useMutation<
    void,
    Error,
    { experimentId: string; tagName: string }
  >({
    mutationFn: ({ experimentId, tagName }) =>
      removeTagFromExperiment(experimentId, tagName),
    onSuccess: () => {
      // Invalidate experiments list and detail queries
      queryClient.invalidateQueries({ queryKey: queryKeys.experiments() });
    },
  });
}

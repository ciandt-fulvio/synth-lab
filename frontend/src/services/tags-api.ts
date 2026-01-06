/**
 * API client for tags.
 *
 * Functions for tag management and experiment tagging.
 */

import { fetchAPI } from './api';
import type { Tag, TagCreateRequest, AddTagRequest } from '@/types/tag';

/**
 * List all available tags.
 *
 * @returns Promise resolving to list of all tags.
 */
export async function listTags(): Promise<Tag[]> {
  return fetchAPI<Tag[]>('/tags');
}

/**
 * Create a new tag.
 *
 * Creates a new tag if it doesn't already exist. If a tag with the same name
 * exists, returns that existing tag instead of creating a duplicate.
 *
 * @param data - Tag creation request.
 * @returns Promise resolving to created or existing tag.
 */
export async function createTag(data: TagCreateRequest): Promise<Tag> {
  return fetchAPI<Tag>('/tags', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Add a tag to an experiment.
 *
 * Creates the tag if it doesn't exist, then associates it with the experiment.
 * If the experiment already has this tag, does nothing (idempotent).
 *
 * @param experimentId - ID of the experiment.
 * @param data - Request with tag name to add.
 * @returns Promise resolving when tag is added.
 */
export async function addTagToExperiment(
  experimentId: string,
  data: AddTagRequest
): Promise<void> {
  await fetchAPI(`/tags/experiments/${experimentId}/tags`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Remove a tag from an experiment.
 *
 * Removes the association between the tag and the experiment.
 * The tag itself is not deleted from the system.
 *
 * @param experimentId - ID of the experiment.
 * @param tagName - Name of the tag to remove.
 * @returns Promise resolving when tag is removed.
 */
export async function removeTagFromExperiment(
  experimentId: string,
  tagName: string
): Promise<void> {
  await fetchAPI(`/tags/experiments/${experimentId}/tags/${encodeURIComponent(tagName)}`, {
    method: 'DELETE',
  });
}

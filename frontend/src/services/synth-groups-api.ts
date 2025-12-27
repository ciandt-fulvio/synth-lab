/**
 * T022 Synth Groups API service.
 *
 * API client for synth group operations.
 *
 * References:
 *   - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
 *   - Types: src/types/synthGroup.ts
 */

import { fetchAPI } from './api';
import type {
  SynthGroupCreate,
  SynthGroupDetail,
  SynthGroupSummary,
  PaginatedSynthGroup,
} from '@/types/synthGroup';
import type { PaginationParams } from '@/types';

/**
 * List synth groups with pagination.
 */
export async function listSynthGroups(
  params?: PaginationParams
): Promise<PaginatedSynthGroup> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  const query = queryParams.toString();
  const endpoint = query ? `/synth-groups/list?${query}` : '/synth-groups/list';

  return fetchAPI<PaginatedSynthGroup>(endpoint);
}

/**
 * Get synth group details by ID.
 */
export async function getSynthGroup(id: string): Promise<SynthGroupDetail> {
  return fetchAPI<SynthGroupDetail>(`/synth-groups/${id}`);
}

/**
 * Create a new synth group.
 */
export async function createSynthGroup(
  data: SynthGroupCreate
): Promise<SynthGroupSummary> {
  return fetchAPI<SynthGroupSummary>('/synth-groups', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a synth group.
 */
export async function deleteSynthGroup(id: string): Promise<void> {
  return fetchAPI<void>(`/synth-groups/${id}`, {
    method: 'DELETE',
  });
}

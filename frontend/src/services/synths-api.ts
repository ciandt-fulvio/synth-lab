// src/services/synths-api.ts

import { fetchAPI } from './api';
import type {
  PaginatedResponse,
  PaginationParams,
  SynthSummary,
  SynthDetail,
  SynthSearchRequest,
} from '@/types';

export async function listSynths(
  params?: PaginationParams
): Promise<PaginatedResponse<SynthSummary>> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());
  if (params?.sort_by) queryParams.append('sort_by', params.sort_by);
  if (params?.sort_order) queryParams.append('sort_order', params.sort_order);

  const query = queryParams.toString();
  const endpoint = query ? `/synths/list?${query}` : '/synths/list';

  return fetchAPI<PaginatedResponse<SynthSummary>>(endpoint);
}

export async function getSynth(synthId: string): Promise<SynthDetail> {
  return fetchAPI<SynthDetail>(`/synths/${synthId}`);
}

export function getSynthAvatarUrl(synthId: string): string {
  return `/api/synths/${synthId}/avatar`;
}

export async function searchSynths(
  request: SynthSearchRequest,
  params?: PaginationParams
): Promise<PaginatedResponse<SynthSummary>> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  const query = queryParams.toString();
  const endpoint = query ? `/synths/search?${query}` : '/synths/search';

  return fetchAPI<PaginatedResponse<SynthSummary>>(endpoint, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

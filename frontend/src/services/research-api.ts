// src/services/research-api.ts

import { fetchAPI } from './api';
import type {
  PaginatedResponse,
  PaginationParams,
  ResearchExecutionSummary,
  ResearchExecutionDetail,
  TranscriptSummary,
  TranscriptDetail,
  ResearchExecuteRequest,
  ResearchExecuteResponse,
} from '@/types';

export async function listExecutions(
  params?: PaginationParams
): Promise<PaginatedResponse<ResearchExecutionSummary>> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());
  if (params?.sort_by) queryParams.append('sort_by', params.sort_by);
  if (params?.sort_order) queryParams.append('sort_order', params.sort_order);

  const query = queryParams.toString();
  const endpoint = query ? `/research/list?${query}` : '/research/list';

  return fetchAPI<PaginatedResponse<ResearchExecutionSummary>>(endpoint);
}

export async function getExecution(
  execId: string
): Promise<ResearchExecutionDetail> {
  return fetchAPI<ResearchExecutionDetail>(`/research/${execId}`);
}

export async function getTranscripts(
  execId: string,
  params?: PaginationParams
): Promise<PaginatedResponse<TranscriptSummary>> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

  const query = queryParams.toString();
  const endpoint = query
    ? `/research/${execId}/transcripts?${query}`
    : `/research/${execId}/transcripts`;

  return fetchAPI<PaginatedResponse<TranscriptSummary>>(endpoint);
}

export async function getTranscript(
  execId: string,
  synthId: string
): Promise<TranscriptDetail> {
  return fetchAPI<TranscriptDetail>(
    `/research/${execId}/transcripts/${synthId}`
  );
}

export async function getSummary(execId: string): Promise<string> {
  return fetchAPI<string>(`/research/${execId}/summary`);
}

export async function executeResearch(
  request: ResearchExecuteRequest
): Promise<ResearchExecuteResponse> {
  return fetchAPI<ResearchExecuteResponse>('/research/execute', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export function getStreamUrl(execId: string): string {
  return `/api/research/${execId}/stream`;
}

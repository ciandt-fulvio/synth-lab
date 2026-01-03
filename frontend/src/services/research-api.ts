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
import type { ArtifactStatesResponse } from '@/types/artifact-state';
import type { ExperimentDocument } from '@/types/document';

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

export interface SummaryGenerateRequest {
  model?: string;
}

export interface SummaryGenerateResponse {
  exec_id: string;
  status: string;
  message?: string;
  generated_at?: string;
}

/**
 * @deprecated Use generateResearchSummary instead
 */
export async function generateSummary(
  execId: string,
  request?: SummaryGenerateRequest
): Promise<SummaryGenerateResponse> {
  return fetchAPI<SummaryGenerateResponse>(`/research/${execId}/summary/generate`, {
    method: 'POST',
    body: JSON.stringify(request ?? {}),
  });
}

// =============================================================================
// Document Endpoints - Summary
// =============================================================================

/**
 * Generate summary document for a research execution.
 *
 * @param execId - Execution ID
 * @returns Generated summary document (with 'generating' status)
 * @throws APIError if execution not found or not completed
 */
export async function generateResearchSummary(execId: string): Promise<ExperimentDocument> {
  return fetchAPI<ExperimentDocument>(`/research/${execId}/documents/summary/generate`, {
    method: 'POST',
  });
}

/**
 * Get summary document for a research execution.
 *
 * @param execId - Execution ID
 * @returns Summary document or null if not exists
 */
export async function getResearchSummary(execId: string): Promise<ExperimentDocument | null> {
  return fetchAPI<ExperimentDocument | null>(`/research/${execId}/documents/summary`);
}

/**
 * Delete summary document for a research execution.
 *
 * @param execId - Execution ID
 */
export async function deleteResearchSummary(execId: string): Promise<void> {
  await fetchAPI(`/research/${execId}/documents/summary`, {
    method: 'DELETE',
  });
}

// =============================================================================
// Document Endpoints - PRFAQ
// =============================================================================

/**
 * Generate PRFAQ document for a research execution.
 *
 * @param execId - Execution ID
 * @returns Generated PRFAQ document (with 'generating' status)
 * @throws APIError if execution not found or summary not completed
 */
export async function generateResearchPRFAQ(execId: string): Promise<ExperimentDocument> {
  return fetchAPI<ExperimentDocument>(`/research/${execId}/documents/prfaq/generate`, {
    method: 'POST',
  });
}

/**
 * Get PRFAQ document for a research execution.
 *
 * @param execId - Execution ID
 * @returns PRFAQ document or null if not exists
 */
export async function getResearchPRFAQ(execId: string): Promise<ExperimentDocument | null> {
  return fetchAPI<ExperimentDocument | null>(`/research/${execId}/documents/prfaq`);
}

/**
 * Delete PRFAQ document for a research execution.
 *
 * @param execId - Execution ID
 */
export async function deleteResearchPRFAQ(execId: string): Promise<void> {
  await fetchAPI(`/research/${execId}/documents/prfaq`, {
    method: 'DELETE',
  });
}

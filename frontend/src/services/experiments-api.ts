/**
 * Experiments API service.
 *
 * API client for experiment CRUD operations.
 *
 * References:
 *   - Types: src/types/experiment.ts
 */

import { fetchAPI } from './api';
import type {
  ExperimentCreate,
  ExperimentUpdate,
  ExperimentDetail,
  PaginatedExperimentSummary,
} from '@/types/experiment';
import type { InterviewCreateRequest, ResearchExecuteResponse } from '@/types/research';

/**
 * Pagination parameters for experiments list.
 */
export interface ExperimentsListParams {
  limit?: number;
  offset?: number;
  search?: string;
  tag?: string;
  sort_by?: 'created_at' | 'name';
  sort_order?: 'asc' | 'desc';
}

/**
 * List experiments with pagination, search, and sorting.
 */
export async function listExperiments(
  params?: ExperimentsListParams
): Promise<PaginatedExperimentSummary> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());
  if (params?.search) queryParams.append('search', params.search);
  if (params?.tag) queryParams.append('tag', params.tag);
  if (params?.sort_by) queryParams.append('sort_by', params.sort_by);
  if (params?.sort_order) queryParams.append('sort_order', params.sort_order);

  const query = queryParams.toString();
  const endpoint = query ? `/experiments/list?${query}` : '/experiments/list';

  return fetchAPI<PaginatedExperimentSummary>(endpoint);
}

/**
 * Get experiment details by ID.
 */
export async function getExperiment(id: string): Promise<ExperimentDetail> {
  return fetchAPI<ExperimentDetail>(`/experiments/${id}`);
}

/**
 * Create a new experiment.
 */
export async function createExperiment(
  data: ExperimentCreate
): Promise<ExperimentDetail> {
  return fetchAPI<ExperimentDetail>('/experiments', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update an existing experiment.
 */
export async function updateExperiment(
  id: string,
  data: ExperimentUpdate
): Promise<ExperimentDetail> {
  return fetchAPI<ExperimentDetail>(`/experiments/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Delete an experiment.
 */
export async function deleteExperiment(id: string): Promise<void> {
  return fetchAPI<void>(`/experiments/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Create an interview linked to an experiment.
 */
export async function createInterviewForExperiment(
  experimentId: string,
  data: InterviewCreateRequest
): Promise<ResearchExecuteResponse> {
  return fetchAPI<ResearchExecuteResponse>(`/experiments/${experimentId}/interviews`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get auto-interview for an experiment if it exists.
 */
export async function getAutoInterview(
  experimentId: string
): Promise<ResearchExecuteResponse | null> {
  return fetchAPI<ResearchExecuteResponse | null>(
    `/experiments/${experimentId}/interviews/auto`
  );
}

/**
 * Create auto-interview with extreme cases (5 best + 5 worst).
 */
export async function createAutoInterview(
  experimentId: string
): Promise<ResearchExecuteResponse> {
  return fetchAPI<ResearchExecuteResponse>(`/experiments/${experimentId}/interviews/auto`, {
    method: 'POST',
  });
}

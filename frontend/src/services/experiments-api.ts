/**
 * T021 Experiments API service.
 *
 * API client for experiment CRUD operations.
 *
 * References:
 *   - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
 *   - Types: src/types/experiment.ts
 */

import { fetchAPI } from './api';
import type {
  ExperimentCreate,
  ExperimentUpdate,
  ExperimentDetail,
  PaginatedExperimentSummary,
  ScorecardCreate,
  ScorecardResponse,
  ScorecardEstimateResponse,
} from '@/types/experiment';
import type { InterviewCreateRequest, ResearchExecuteResponse } from '@/types/research';
import type { PaginationParams } from '@/types';

/**
 * List experiments with pagination.
 */
export async function listExperiments(
  params?: PaginationParams
): Promise<PaginatedExperimentSummary> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

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
 * Create a scorecard linked to an experiment.
 *
 * The scorecard is automatically associated with the specified experiment.
 */
export async function createScorecardForExperiment(
  experimentId: string,
  data: ScorecardCreate
): Promise<ScorecardResponse> {
  return fetchAPI<ScorecardResponse>(`/experiments/${experimentId}/scorecards`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Create an interview linked to an experiment.
 *
 * The interview is automatically associated with the specified experiment.
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
 * Estimate scorecard dimensions using AI.
 *
 * Uses the experiment's name, hypothesis, and description to generate
 * AI-powered estimates for all scorecard dimensions.
 */
export async function estimateScorecardForExperiment(
  experimentId: string
): Promise<ScorecardEstimateResponse> {
  return fetchAPI<ScorecardEstimateResponse>(
    `/experiments/${experimentId}/estimate-scorecard`,
    { method: 'POST' }
  );
}

/**
 * Request for scorecard estimation from text.
 */
export interface ScorecardEstimateRequest {
  name: string;
  hypothesis: string;
  description?: string;
}

/**
 * Estimate scorecard dimensions using AI from text input.
 *
 * This allows estimation before an experiment exists.
 * Useful for the experiment form to get AI-generated slider values.
 */
export async function estimateScorecardFromText(
  data: ScorecardEstimateRequest
): Promise<ScorecardEstimateResponse> {
  return fetchAPI<ScorecardEstimateResponse>(
    '/experiments/estimate-scorecard',
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  );
}

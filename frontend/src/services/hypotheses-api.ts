/**
 * API service for Hypothesis operations.
 *
 * Provides typed functions for hypothesis CRUD and versioning.
 *
 * References:
 *   - Backend: api/routers/hypotheses.py
 *   - Types: types/hypothesis.ts
 */

import { fetchAPI } from './api';
import type {
  Hypothesis,
  HypothesesBulkUpdateRequest,
  HypothesisCompareRequest,
  HypothesisCompareResponse,
  HypothesisUpdateRequest,
  HypothesisVersion,
  HypothesisVersionCreateRequest,
} from '@/types/hypothesis';

/**
 * Get all hypotheses for a simulation.
 *
 * @param simulationId - Simulation ID
 * @returns List of hypotheses
 */
export async function getHypotheses(
  simulationId: string
): Promise<Hypothesis[]> {
  return fetchAPI<Hypothesis[]>(`/simulations/${simulationId}/hypotheses`);
}

/**
 * Update multiple hypotheses at once.
 *
 * @param simulationId - Simulation ID
 * @param request - Updates keyed by variable name
 * @returns Updated hypotheses
 */
export async function updateHypotheses(
  simulationId: string,
  request: HypothesesBulkUpdateRequest
): Promise<Hypothesis[]> {
  return fetchAPI<Hypothesis[]>(`/simulations/${simulationId}/hypotheses`, {
    method: 'PUT',
    body: JSON.stringify(request),
  });
}

/**
 * Update a single hypothesis.
 *
 * @param simulationId - Simulation ID
 * @param variableName - Variable name
 * @param request - Update request
 * @returns Updated hypothesis
 */
export async function updateHypothesis(
  simulationId: string,
  variableName: string,
  request: HypothesisUpdateRequest
): Promise<Hypothesis> {
  return fetchAPI<Hypothesis>(
    `/simulations/${simulationId}/hypotheses/${variableName}`,
    {
      method: 'PUT',
      body: JSON.stringify(request),
    }
  );
}

/**
 * Save current hypothesis state as a named version.
 *
 * @param simulationId - Simulation ID
 * @param request - Version name and description
 * @returns Created version info
 */
export async function saveHypothesisVersion(
  simulationId: string,
  request: HypothesisVersionCreateRequest
): Promise<HypothesisVersion> {
  return fetchAPI<HypothesisVersion>(
    `/simulations/${simulationId}/hypotheses/versions`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
}

/**
 * List all hypothesis versions for a simulation.
 *
 * @param simulationId - Simulation ID
 * @returns List of version summaries
 */
export async function listHypothesisVersions(
  simulationId: string
): Promise<HypothesisVersion[]> {
  return fetchAPI<HypothesisVersion[]>(
    `/simulations/${simulationId}/hypotheses/versions`
  );
}

/**
 * Get hypotheses at a specific version.
 *
 * @param simulationId - Simulation ID
 * @param version - Version number
 * @returns Hypotheses at that version
 */
export async function getHypothesesAtVersion(
  simulationId: string,
  version: number
): Promise<Hypothesis[]> {
  return fetchAPI<Hypothesis[]>(
    `/simulations/${simulationId}/hypotheses/versions/${version}`
  );
}

/**
 * Compare two hypothesis versions.
 *
 * @param simulationId - Simulation ID
 * @param request - Versions to compare
 * @returns Diff showing changes
 */
export async function compareHypothesisVersions(
  simulationId: string,
  request: HypothesisCompareRequest
): Promise<HypothesisCompareResponse> {
  return fetchAPI<HypothesisCompareResponse>(
    `/simulations/${simulationId}/hypotheses/compare`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
}

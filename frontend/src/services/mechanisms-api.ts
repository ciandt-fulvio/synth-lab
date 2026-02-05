/**
 * Mechanisms API service.
 *
 * API client for mechanism configuration and narrative generation.
 *
 * References:
 *   - OpenAPI: specs/039-narrative-mechanism-config/contracts/api.yaml
 *   - Types: src/types/mechanisms.ts
 */

import { fetchAPI } from './api';
import type {
  MechanismListResponse,
  FeatureTypeListResponse,
  GenerateNarrativeRequest,
  GenerateNarrativeResponse,
} from '@/types/mechanisms';

/**
 * List all mechanism definitions with their options.
 *
 * @returns List of mechanisms with options ordered by display_order
 */
export async function listMechanisms(): Promise<MechanismListResponse> {
  return fetchAPI<MechanismListResponse>('/mechanisms');
}

/**
 * List all feature types with their amplified mechanisms.
 *
 * @returns List of feature types
 */
export async function listFeatureTypes(): Promise<FeatureTypeListResponse> {
  return fetchAPI<FeatureTypeListResponse>('/mechanisms/feature-types');
}

/**
 * Generate narrative with mechanism placeholders.
 *
 * Analyzes the feature description and generates a narrative text with
 * placeholders for relevant mechanisms. The LLM infers feature types
 * and selects appropriate mechanisms.
 *
 * @param request - Feature name, hypothesis, and optional description
 * @returns Generated narrative with selected mechanisms
 */
export async function generateNarrative(
  request: GenerateNarrativeRequest
): Promise<GenerateNarrativeResponse> {
  return fetchAPI<GenerateNarrativeResponse>('/experiments/generate-narrative', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

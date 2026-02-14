/**
 * Quantitative analysis API client for synth-lab.
 *
 * API calls for causal model generation, edge selection, and simulation.
 *
 * References:
 *   - Contracts: specs/042-quantitative-analysis/contracts/api.md
 *   - Types: src/types/quantitative-analysis.ts
 */

import { fetchAPI } from './api';
import type {
  CausalModel,
  EdgeUpdateResponse,
  SimulationRun,
} from '@/types/quantitative-analysis';

/**
 * Generate a causal DAG model for an experiment via LLM (gpt-5.1).
 *
 * Deletes any existing model and generates a new one.
 * All selected_option values start as null.
 */
export async function generateCausalModel(
  experimentId: string
): Promise<CausalModel> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/generate`, {
    method: 'POST',
  });
}

/**
 * Get the current causal model for an experiment with edge selections.
 */
export async function getCausalModel(
  experimentId: string
): Promise<CausalModel> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/model`);
}

/**
 * Update PM's Likert selections for causal model edges.
 *
 * Accepts partial updates — only specified edges are modified.
 * Called with debounce from the frontend.
 */
export async function updateEdgeSelections(
  experimentId: string,
  selections: Record<string, number>
): Promise<EdgeUpdateResponse> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/edges`, {
    method: 'PATCH',
    body: JSON.stringify({ selections }),
  });
}

/**
 * Run Monte Carlo simulation with current edge selections.
 *
 * Returns full results including stats, segments, sensitivity, and AI interpretations.
 */
export async function runSimulation(
  experimentId: string
): Promise<SimulationRun> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/simulate`, {
    method: 'POST',
  });
}

/**
 * Get results from the latest simulation run.
 */
export async function getSimulationResults(
  experimentId: string
): Promise<SimulationRun> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/results`);
}

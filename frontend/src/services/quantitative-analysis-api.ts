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
  NodeSelectionsResponse,
  ProductCalibrationResponse,
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
 * Update PM's premissa selections for interaction/outcome nodes.
 *
 * Accepts partial updates — only specified nodes are modified.
 */
export async function updateNodeSelections(
  experimentId: string,
  selections: Record<string, number>
): Promise<NodeSelectionsResponse> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/node-selections`, {
    method: 'PATCH',
    body: JSON.stringify({ selections }),
  });
}

/**
 * Update product node calibrations (low/medium/high).
 */
export async function updateProductCalibration(
  experimentId: string,
  calibrations: Record<string, string>
): Promise<ProductCalibrationResponse> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/product-calibration`, {
    method: 'PATCH',
    body: JSON.stringify({ calibrations }),
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
 * Generate interview guide from the latest simulation sensitivity results.
 *
 * Overwrites any existing guide for this experiment.
 */
export async function generateInterviewGuide(
  experimentId: string
): Promise<{ status: string }> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/generate-interview-guide`, {
    method: 'POST',
  });
}

/**
 * Generate or regenerate the simulation summary report.
 */
export async function generateSimulationSummary(
  experimentId: string
): Promise<{ status: string }> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/generate-simulation-summary`, {
    method: 'POST',
  });
}

/**
 * Get the interview guide for an experiment, formatted as markdown.
 * Returns null if no guide exists (404).
 */
export async function getInterviewGuide(
  experimentId: string
): Promise<{ markdown_content: string } | null> {
  try {
    return await fetchAPI<{ markdown_content: string }>(`/experiments/${experimentId}/interview-guide`);
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

/**
 * Get results from the latest simulation run.
 * Returns null if no simulation has been run yet (404).
 */
export async function getSimulationResults(
  experimentId: string
): Promise<SimulationRun | null> {
  try {
    return await fetchAPI<SimulationRun>(`/experiments/${experimentId}/quantitative-analysis/results`);
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

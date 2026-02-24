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
  MultiScenarioResponse,
  NodeSelectionsResponse,
  SimulationReport,
  SynthProfilesResponse,
  ProductSynthCorrelationResponse,
  SynthAttributeInsightsResponse,
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
 * Run multi-scenario batch simulation.
 *
 * Auto-generates random scenarios by sampling {low, medium, high}
 * for each product node. PM premissas (edges, nodes) stay fixed.
 */
export async function runBatchSimulation(
  experimentId: string
): Promise<MultiScenarioResponse> {
  return fetchAPI(`/experiments/${experimentId}/quantitative-analysis/simulate-scenarios`, {
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
): Promise<{ markdown_content: string; created_at: string | null } | null> {
  try {
    return await fetchAPI<{ markdown_content: string; created_at: string | null }>(
      `/experiments/${experimentId}/interview-guide`
    );
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

/**
 * Get the latest simulation batch results for an experiment.
 * Returns null if no batch exists (404).
 */
export async function getLatestBatch(
  experimentId: string
): Promise<MultiScenarioResponse | null> {
  try {
    return await fetchAPI<MultiScenarioResponse>(
      `/experiments/${experimentId}/quantitative-analysis/latest-batch`
    );
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

/**
 * Get synth profile analysis (adopters vs rejectors + clusters).
 * Returns null if no data exists (404).
 */
export async function getSynthProfiles(
  experimentId: string
): Promise<SynthProfilesResponse | null> {
  try {
    return await fetchAPI<SynthProfilesResponse>(
      `/experiments/${experimentId}/quantitative-analysis/synth-profiles`
    );
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

/**
 * Get synth attribute Pearson r correlations and 3×3 segment heatmap.
 * Returns null if no data exists (404).
 */
export async function getSynthAttributeInsights(
  experimentId: string
): Promise<SynthAttributeInsightsResponse | null> {
  try {
    return await fetchAPI<SynthAttributeInsightsResponse>(
      `/experiments/${experimentId}/quantitative-analysis/synth-attribute-insights`
    );
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

/**
 * Get product × synth-cluster correlation matrix.
 * Returns null if no data exists (404).
 */
export async function getProductSynthCorrelations(
  experimentId: string
): Promise<ProductSynthCorrelationResponse | null> {
  try {
    return await fetchAPI<ProductSynthCorrelationResponse>(
      `/experiments/${experimentId}/quantitative-analysis/product-synth-correlations`
    );
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

/**
 * Get the latest LLM-generated simulation report for an experiment.
 * Returns null if no report has been generated yet (404).
 */
export async function getSimulationReport(
  experimentId: string
): Promise<SimulationReport | null> {
  try {
    return await fetchAPI<SimulationReport>(
      `/experiments/${experimentId}/quantitative-analysis/report`
    );
  } catch (err: any) {
    if (err?.status === 404) return null;
    throw err;
  }
}

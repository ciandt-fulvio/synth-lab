/**
 * API service for simulation insights and evidence.
 *
 * Provides typed functions for evidence, failure modes, clusters, and insights.
 *
 * References:
 *   - Backend: api/routers/simulation_insights.py
 *   - Types: types/simulation-insight.ts
 */

import { fetchAPI } from './api';
import type {
  Evidence,
  SimulationInsight,
  InsightTrace,
} from '@/types/simulation-insight';

/**
 * Get simulation evidence with percentiles, sensitivity, and patterns.
 *
 * @param simulationId - Simulation ID
 * @returns Evidence with failure modes and clusters
 */
export async function getEvidence(simulationId: string): Promise<Evidence> {
  return fetchAPI<Evidence>(`/simulations/${simulationId}/evidence`);
}

/**
 * Get all insights for a simulation.
 *
 * @param simulationId - Simulation ID
 * @returns List of insights
 */
export async function getInsights(
  simulationId: string
): Promise<SimulationInsight[]> {
  return fetchAPI<SimulationInsight[]>(`/simulations/${simulationId}/insights`);
}

/**
 * Get insight traceability details.
 *
 * @param insightId - Insight ID
 * @returns Trace with statistical support and affected worlds
 */
export async function getInsightTrace(insightId: string): Promise<InsightTrace> {
  return fetchAPI<InsightTrace>(`/simulations/insights/${insightId}/trace`);
}

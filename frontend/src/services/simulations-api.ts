/**
 * API service for causal simulation endpoints.
 *
 * Provides typed functions for simulation lifecycle operations.
 *
 * References:
 *   - Backend: src/synth_lab/api/routers/simulations.py
 *   - Spec: specs/035-causal-simulation/spec.md
 */

import { fetchAPI } from './api';

/**
 * Simulation status enum.
 */
export type SimulationStatus =
  | 'parsing'
  | 'awaiting_question_validation'
  | 'dag_construction'
  | 'awaiting_dag_validation'
  | 'hypothesis_generation'
  | 'awaiting_hypothesis_validation'
  | 'ready_to_run'
  | 'simulating'
  | 'completed'
  | 'failed';

/**
 * Request schema for updating problem decomposition.
 */
export interface ProblemDecompositionUpdate {
  intervention?: string;
  primary_outcome?: string;
  secondary_outcomes?: string[];
  unit_of_analysis?: string;
  time_horizon?: string;
  decision_type?: string;
}

/**
 * Problem decomposition structure from question parsing.
 * Matches backend: src/synth_lab/domain/entities/simulation.py
 */
export interface ProblemDecomposition {
  intervention: string;
  primary_outcome: string;
  secondary_outcomes: string[];
  unit_of_analysis: string;
  time_horizon: string;
  decision_type: string;
}

/**
 * Percentile distribution for outcome variables.
 */
export interface PercentileDistribution {
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
}

/**
 * Request schema for creating a simulation.
 */
export interface SimulationCreateRequest {
  question_text: string;
  random_seed?: number;
  n_worlds?: number;
}

/**
 * Response schema for simulation details.
 */
export interface SimulationResponse {
  id: string;
  question_text: string;
  problem_decomposition: ProblemDecomposition | null;
  status: SimulationStatus;
  random_seed: number | null;
  n_worlds: number | null;
  created_at: string;
}

/**
 * Request schema for running a simulation.
 */
export interface SimulationRunRequest {
  n_worlds?: number;
}

/**
 * Response schema for simulation run results.
 */
export interface SimulationRunResponse {
  simulation_id: string;
  status: string;
  n_worlds: number;
  n_insights: number;
  outcome_distributions: Record<string, PercentileDistribution>;
}

/**
 * Insight response schema.
 */
export interface InsightResponse {
  id: string;
  simulation_id: string;
  insight_type: 'key_driver' | 'failure_mode' | 'cluster_finding' | 'recommendation';
  title: string;
  description: string;
  evidence_references: Record<string, any>;
  recommended_actions: Array<{
    action: string;
    priority: 'high' | 'medium' | 'low';
    rationale: string;
  }>;
  created_at: string;
}

/**
 * Insight traceability response schema.
 */
export interface InsightTraceResponse {
  insight_id: string;
  simulation_id: string;
  evidence_references: Record<string, any>;
  statistical_support: Record<string, any>;
  affected_worlds: string[];
}

/**
 * Create a new simulation from a natural language question.
 *
 * @param request - Question text and optional parameters
 * @returns Created simulation with ID
 */
export async function createSimulation(
  request: SimulationCreateRequest
): Promise<SimulationResponse> {
  return fetchAPI<SimulationResponse>('/simulations', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get simulation details by ID.
 *
 * @param simulationId - Simulation ID
 * @returns Simulation details
 */
export async function getSimulation(simulationId: string): Promise<SimulationResponse> {
  return fetchAPI<SimulationResponse>(`/simulations/${simulationId}`);
}

/**
 * List all simulations with optional filtering.
 *
 * @param options - Filter options
 * @returns List of simulations
 */
export async function listSimulations(options?: {
  status?: SimulationStatus;
  limit?: number;
}): Promise<SimulationResponse[]> {
  const params = new URLSearchParams();
  if (options?.status) params.append('status', options.status);
  if (options?.limit) params.append('limit', options.limit.toString());

  const query = params.toString();
  const url = query ? `/simulations?${query}` : '/simulations';

  return fetchAPI<SimulationResponse[]>(url);
}

/**
 * Delete a simulation and all associated data.
 *
 * @param simulationId - Simulation ID
 */
export async function deleteSimulation(simulationId: string): Promise<void> {
  await fetchAPI<void>(`/simulations/${simulationId}`, {
    method: 'DELETE',
  });
}

/**
 * Update problem decomposition for a simulation.
 *
 * Can only be called when simulation is in awaiting_question_validation status.
 *
 * @param simulationId - Simulation ID
 * @param update - Fields to update
 * @returns Updated simulation
 */
export async function updateProblemDecomposition(
  simulationId: string,
  update: ProblemDecompositionUpdate
): Promise<SimulationResponse> {
  return fetchAPI<SimulationResponse>(`/simulations/${simulationId}/problem-decomposition`, {
    method: 'PUT',
    body: JSON.stringify(update),
  });
}

/**
 * Confirm question and generate DAG.
 *
 * @param simulationId - Simulation ID
 * @returns Simulation with updated status
 */
export async function confirmQuestion(simulationId: string): Promise<SimulationResponse> {
  return fetchAPI<SimulationResponse>(`/simulations/${simulationId}/confirm-question`, {
    method: 'POST',
  });
}

/**
 * Confirm DAG and generate hypotheses.
 *
 * @param simulationId - Simulation ID
 * @returns Simulation with updated status
 */
export async function confirmDAG(simulationId: string): Promise<SimulationResponse> {
  return fetchAPI<SimulationResponse>(`/simulations/${simulationId}/confirm-dag`, {
    method: 'POST',
  });
}

/**
 * Confirm hypotheses and mark ready to run.
 *
 * @param simulationId - Simulation ID
 * @returns Simulation with updated status
 */
export async function confirmHypotheses(simulationId: string): Promise<SimulationResponse> {
  return fetchAPI<SimulationResponse>(`/simulations/${simulationId}/confirm-hypotheses`, {
    method: 'POST',
  });
}

/**
 * Run a simulation to generate synthetic worlds and insights.
 *
 * @param simulationId - Simulation ID
 * @param request - Optional run parameters
 * @returns Run results summary
 */
export async function runSimulation(
  simulationId: string,
  request?: SimulationRunRequest
): Promise<SimulationRunResponse> {
  return fetchAPI<SimulationRunResponse>(`/simulations/${simulationId}/run`, {
    method: 'POST',
    body: request ? JSON.stringify(request) : undefined,
  });
}

/**
 * Get all insights for a simulation.
 *
 * @param simulationId - Simulation ID
 * @returns List of insights with evidence and recommendations
 */
export async function getSimulationInsights(
  simulationId: string
): Promise<InsightResponse[]> {
  return fetchAPI<InsightResponse[]>(`/simulations/${simulationId}/insights`);
}

/**
 * Get full traceability for an insight.
 *
 * @param insightId - Insight ID
 * @returns Traceability details
 */
export async function getInsightTrace(insightId: string): Promise<InsightTraceResponse> {
  return fetchAPI<InsightTraceResponse>(`/insights/${insightId}/trace`);
}

/**
 * Audit trail response schema.
 */
export interface AuditTrailResponse {
  id: string;
  simulation_id: string;
  question: string;
  random_seed: number;
  n_worlds: number;
  dag_version: number;
  n_hypotheses: number;
  n_failure_modes: number;
  n_clusters: number;
  n_insights: number;
  created_at: string;
}

/**
 * Replay response schema.
 */
export interface ReplayResponse {
  simulation_id: string;
  status: string;
  n_worlds: number;
  message: string;
}

/**
 * Export response schema.
 */
export interface ExportResponse {
  audit_id: string;
  simulation_id: string;
  export_package: Record<string, unknown>;
}

/**
 * Get audit trail for a simulation.
 *
 * @param simulationId - Simulation ID
 * @returns Audit trail details
 */
export async function getSimulationAudit(
  simulationId: string
): Promise<AuditTrailResponse> {
  return fetchAPI<AuditTrailResponse>(`/simulations/${simulationId}/audit`);
}

/**
 * Replay a simulation using stored audit trail.
 *
 * @param simulationId - Simulation ID
 * @returns Replay results
 */
export async function replaySimulation(simulationId: string): Promise<ReplayResponse> {
  return fetchAPI<ReplayResponse>(`/simulations/${simulationId}/replay`, {
    method: 'POST',
  });
}

/**
 * Export audit trail as a portable JSON package.
 *
 * @param simulationId - Simulation ID
 * @returns Export package
 */
export async function exportSimulationAudit(
  simulationId: string
): Promise<ExportResponse> {
  return fetchAPI<ExportResponse>(`/simulations/${simulationId}/audit/export`);
}

/**
 * API service for Causal DAG operations.
 *
 * Provides typed functions for DAG CRUD, validation, and versioning.
 *
 * References:
 *   - Backend: api/routers/causal_dag.py
 *   - Types: types/causal-dag.ts
 */

import { fetchAPI } from './api';
import type {
  CausalDAG,
  DAGCompareRequest,
  DAGCompareResponse,
  DAGUpdateRequest,
  DAGValidationRequest,
  DAGValidationResponse,
  DAGVersion,
} from '@/types/causal-dag';

/**
 * Get DAG for a simulation.
 *
 * @param simulationId - Simulation ID
 * @returns DAG with nodes and edges
 */
export async function getDAG(simulationId: string): Promise<CausalDAG> {
  return fetchAPI<CausalDAG>(`/simulations/${simulationId}/dag`);
}

/**
 * Update DAG structure.
 *
 * Supports full replacement or incremental updates.
 *
 * @param simulationId - Simulation ID
 * @param request - Update request with changes
 * @returns Updated DAG
 */
export async function updateDAG(
  simulationId: string,
  request: DAGUpdateRequest
): Promise<CausalDAG> {
  return fetchAPI<CausalDAG>(`/simulations/${simulationId}/dag`, {
    method: 'PUT',
    body: JSON.stringify(request),
  });
}

/**
 * Validate DAG structure without persisting.
 *
 * @param simulationId - Simulation ID
 * @param request - Nodes and edges to validate
 * @returns Validation result
 */
export async function validateDAG(
  simulationId: string,
  request: DAGValidationRequest
): Promise<DAGValidationResponse> {
  return fetchAPI<DAGValidationResponse>(
    `/simulations/${simulationId}/dag/validate`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
}

/**
 * List all DAG versions for a simulation.
 *
 * @param simulationId - Simulation ID
 * @returns List of version summaries
 */
export async function listDAGVersions(
  simulationId: string
): Promise<DAGVersion[]> {
  return fetchAPI<DAGVersion[]>(`/simulations/${simulationId}/dag/versions`);
}

/**
 * Compare two DAG versions.
 *
 * @param simulationId - Simulation ID
 * @param request - Versions to compare
 * @returns Diff showing changes
 */
export async function compareDAGVersions(
  simulationId: string,
  request: DAGCompareRequest
): Promise<DAGCompareResponse> {
  return fetchAPI<DAGCompareResponse>(
    `/simulations/${simulationId}/dag/compare`,
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
}

/**
 * Add a node to the DAG.
 *
 * Convenience function for incremental updates.
 *
 * @param simulationId - Simulation ID
 * @param node - Node to add
 * @returns Updated DAG
 */
export async function addNode(
  simulationId: string,
  node: CausalDAG['nodes'][0]
): Promise<CausalDAG> {
  return updateDAG(simulationId, { add_nodes: [node] });
}

/**
 * Remove a node from the DAG.
 *
 * Also removes connected edges.
 *
 * @param simulationId - Simulation ID
 * @param nodeName - Name of node to remove
 * @returns Updated DAG
 */
export async function removeNode(
  simulationId: string,
  nodeName: string
): Promise<CausalDAG> {
  return updateDAG(simulationId, { remove_nodes: [nodeName] });
}

/**
 * Add an edge to the DAG.
 *
 * @param simulationId - Simulation ID
 * @param edge - Edge to add
 * @returns Updated DAG
 */
export async function addEdge(
  simulationId: string,
  edge: CausalDAG['edges'][0]
): Promise<CausalDAG> {
  return updateDAG(simulationId, { add_edges: [edge] });
}

/**
 * Remove an edge from the DAG.
 *
 * @param simulationId - Simulation ID
 * @param source - Source node name
 * @param target - Target node name
 * @returns Updated DAG
 */
export async function removeEdge(
  simulationId: string,
  source: string,
  target: string
): Promise<CausalDAG> {
  return updateDAG(simulationId, { remove_edges: [[source, target]] });
}

/**
 * Save node positions for visualization.
 *
 * Updates position_x and position_y without incrementing version.
 *
 * @param simulationId - Simulation ID
 * @param positions - Map of node names to {x, y} coordinates
 * @returns Updated DAG
 */
export async function saveNodePositions(
  simulationId: string,
  positions: Record<string, { x: number; y: number }>
): Promise<CausalDAG> {
  return fetchAPI<CausalDAG>(`/simulations/${simulationId}/dag/positions`, {
    method: 'PATCH',
    body: JSON.stringify(positions),
  });
}

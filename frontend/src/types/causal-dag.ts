/**
 * TypeScript types for Causal DAG structures.
 *
 * References:
 *   - Backend: api/schemas/causal_dag.py
 *   - Spec: specs/035-causal-simulation/spec.md
 */

/**
 * Variable type in the DAG.
 */
export type VariableType = 'input' | 'intermediate' | 'output';

/**
 * Variable scope.
 */
export type VariableScope = 'world' | 'user';

/**
 * Controllability level for a variable.
 */
export type Controllability = 'none' | 'low' | 'medium' | 'high';

/**
 * Estimated strength of causal relationship.
 */
export type StrengthEstimated = 'high' | 'low';

/**
 * Single DAG variable/node.
 */
export interface Variable {
  name: string;
  label: string;
  variable_type: VariableType;
  scope: VariableScope;
  description?: string | null;
  unit?: string | null;
  controllability?: Controllability | null;
  is_intervention?: boolean;
  is_outcome?: boolean;
  is_critical_uncertainty?: boolean;
  position_x?: number | null;
  position_y?: number | null;
}

/**
 * Edge relationship type.
 */
export type RelationshipType = 'causal' | 'correlation';

/**
 * DAG edge connecting two variables.
 */
export interface Edge {
  source: string;
  target: string;
  relationship_type: RelationshipType;
  strength_estimated?: StrengthEstimated | null;
  strength?: number | null;
  strength_user?: number | null;
  description?: string | null;
}

/**
 * Assumption about the model.
 */
export interface Assumption {
  assumption: string;
  rationale: string;
  confidence: 'low' | 'medium' | 'high';
}

/**
 * Identified risk or uncertainty.
 */
export interface Risk {
  risk: string;
  impact: 'low' | 'medium' | 'high';
  mitigation: string;
}

/**
 * Complete DAG structure.
 */
export interface CausalDAG {
  id: string;
  simulation_id: string;
  nodes: Variable[];
  edges: Edge[];
  assumptions?: Assumption[];
  risks?: Risk[];
  version: number;
  created_at: string;
  updated_at?: string | null;
}

/**
 * Request to update a DAG.
 */
export interface DAGUpdateRequest {
  nodes?: Variable[];
  edges?: Edge[];
  add_nodes?: Variable[];
  remove_nodes?: string[];
  add_edges?: Edge[];
  remove_edges?: [string, string][];
}

/**
 * DAG validation request.
 */
export interface DAGValidationRequest {
  nodes: Variable[];
  edges: Edge[];
}

/**
 * DAG validation response.
 */
export interface DAGValidationResponse {
  valid: boolean;
  errors: string[];
  warnings: string[];
  has_cycles: boolean;
  orphan_nodes: string[];
}

/**
 * DAG version summary.
 */
export interface DAGVersion {
  version: number;
  created_at: string;
  node_count: number;
  edge_count: number;
  description?: string | null;
}

/**
 * DAG comparison request.
 */
export interface DAGCompareRequest {
  version_a: number;
  version_b: number;
}

/**
 * DAG comparison response.
 */
export interface DAGCompareResponse {
  added_nodes: string[];
  removed_nodes: string[];
  added_edges: [string, string][];
  removed_edges: [string, string][];
  modified_nodes: string[];
}

/**
 * React Flow node data type.
 */
export interface DAGNodeData {
  variable: Variable;
  isSelected?: boolean;
  isHighlighted?: boolean;
}

/**
 * React Flow edge data type.
 */
export interface DAGEdgeData {
  edge: Edge;
  isSelected?: boolean;
}

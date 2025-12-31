/**
 * Types for exploration feature.
 *
 * These types mirror the backend API schemas from spec 024 and add
 * frontend-specific types for tree visualization.
 */

import { z } from 'zod';

// =============================================================================
// Core Types (API Response)
// =============================================================================

/**
 * Goal definition for exploration.
 */
export interface ExplorationGoal {
  metric: 'success_rate';
  operator: '>=';
  value: number; // 0-1
}

/**
 * Configuration for exploration search.
 */
export interface ExplorationConfig {
  beam_width: number;
  max_depth: number;
  max_llm_calls: number;
  n_executions: number;
  sigma: number;
  seed: number | null;
}

/**
 * Status of an exploration.
 */
export type ExplorationStatus =
  | 'running'
  | 'goal_achieved'
  | 'depth_limit_reached'
  | 'cost_limit_reached'
  | 'no_viable_paths';

/**
 * Exploration entity from API.
 */
export interface Exploration {
  id: string;
  experiment_id: string;
  baseline_analysis_id: string;
  goal: ExplorationGoal;
  config: ExplorationConfig;
  status: ExplorationStatus;
  current_depth: number;
  total_nodes: number;
  total_llm_calls: number;
  best_success_rate: number | null;
  started_at: string;
  completed_at: string | null;
}

/**
 * Scorecard parameters for a scenario.
 */
export interface ScorecardParams {
  complexity: number;
  initial_effort: number;
  perceived_risk: number;
  time_to_value: number;
}

/**
 * Simulation results for a scenario.
 */
export interface SimulationResults {
  success_rate: number;
  fail_rate: number;
  did_not_try_rate: number;
}

/**
 * Status of a scenario node.
 */
export type NodeStatus = 'active' | 'dominated' | 'winner' | 'expansion_failed';

/**
 * Scenario node from API.
 */
export interface ScenarioNode {
  id: string;
  exploration_id: string;
  parent_id: string | null;
  depth: number;
  action_applied: string | null;
  action_category: string | null;
  rationale: string | null;
  scorecard_params: ScorecardParams;
  simulation_results: SimulationResults | null;
  execution_time_seconds: number | null;
  node_status: NodeStatus;
  created_at: string;
}

/**
 * Exploration tree response from API.
 */
export interface ExplorationTree {
  exploration: Exploration;
  nodes: ScenarioNode[];
  node_count_by_status: Record<NodeStatus, number>;
}

/**
 * Path step in winning path.
 */
export interface PathStep {
  depth: number;
  action: string | null;
  category: string | null;
  rationale: string | null;
  success_rate: number;
  delta_success_rate: number;
}

/**
 * Winning path response from API.
 */
export interface WinningPath {
  exploration_id: string;
  winner_node_id: string;
  path: PathStep[];
  total_improvement: number;
}

// =============================================================================
// Action Catalog Types
// =============================================================================

/**
 * Impact range for an action parameter.
 */
export interface ImpactRange {
  min: number;
  max: number;
}

/**
 * Example action in catalog.
 */
export interface ActionExample {
  action: string;
  typical_impacts: Record<string, ImpactRange>;
}

/**
 * Action category in catalog.
 */
export interface ActionCategory {
  id: string;
  name: string;
  description: string;
  examples: ActionExample[];
}

/**
 * Action catalog response.
 */
export interface ActionCatalog {
  version: string;
  categories: ActionCategory[];
}

// =============================================================================
// Request Types
// =============================================================================

/**
 * Request to create a new exploration.
 */
export interface ExplorationCreate {
  experiment_id: string;
  goal_value: number;
  beam_width?: number;
  max_depth?: number;
  max_llm_calls?: number;
  n_executions?: number;
  seed?: number | null;
}

// =============================================================================
// Tree Visualization Types
// =============================================================================

/**
 * Node data for react-d3-tree.
 * Extends base node with visualization properties.
 */
export interface TreeNodeData {
  name: string; // Display label (success_rate %)
  attributes?: {
    action?: string; // Truncated action text
    status: NodeStatus; // For color coding
  };
  children?: TreeNodeData[];
  // Original node data for detail panel
  __nodeData: ScenarioNode;
}

/**
 * Props for custom node element.
 */
export interface CustomNodeProps {
  nodeDatum: TreeNodeData;
  toggleNode: () => void;
  onNodeClick?: (node: ScenarioNode) => void;
}

/**
 * Colors for node status.
 */
export const NODE_STATUS_COLORS: Record<NodeStatus, string> = {
  winner: '#22c55e', // green-500
  active: '#3b82f6', // blue-500
  dominated: '#94a3b8', // slate-400
  expansion_failed: '#ef4444', // red-500
};

/**
 * Badge variants for node status.
 */
export const NODE_STATUS_BADGES: Record<
  NodeStatus,
  {
    label: string;
    variant: 'success' | 'info' | 'neutral' | 'error';
  }
> = {
  winner: { label: 'Vencedor', variant: 'success' },
  active: { label: 'Ativo', variant: 'info' },
  dominated: { label: 'Dominado', variant: 'neutral' },
  expansion_failed: { label: 'Falhou', variant: 'error' },
};

// =============================================================================
// Exploration List Types (for experiment page)
// =============================================================================

/**
 * Summary of exploration for list view.
 */
export interface ExplorationSummary {
  id: string;
  status: ExplorationStatus;
  goal_value: number;
  best_success_rate: number | null;
  total_nodes: number;
  started_at: string;
  completed_at: string | null;
}

// =============================================================================
// Zod Schema (for form validation)
// =============================================================================

export const explorationCreateSchema = z.object({
  experiment_id: z.string().min(1, 'ID do experimento é obrigatório'),
  goal_value: z
    .number()
    .min(0.01, 'Meta deve ser maior que 0%')
    .max(1, 'Meta deve ser menor ou igual a 100%'),
  beam_width: z
    .number()
    .int()
    .min(1, 'Beam width mínimo é 1')
    .max(10, 'Beam width máximo é 10')
    .default(3),
  max_depth: z
    .number()
    .int()
    .min(1, 'Profundidade mínima é 1')
    .max(10, 'Profundidade máxima é 10')
    .default(5),
});

export type ExplorationCreateForm = z.infer<typeof explorationCreateSchema>;

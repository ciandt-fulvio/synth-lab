# Data Model: Frontend para Exploracao de Cenarios

**Feature**: 025-exploration-frontend
**Date**: 2025-12-31

## Overview

Este documento define os tipos TypeScript para o frontend da feature de exploracao de cenarios. Os tipos espelham os schemas da API backend (spec 024) e adicionam tipos especificos para a visualizacao.

## TypeScript Types

### Core Types (API Response)

```typescript
// types/exploration.ts

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
```

### Action Catalog Types

```typescript
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
```

### Request Types

```typescript
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
```

### Tree Visualization Types

```typescript
/**
 * Node data for react-d3-tree.
 * Extends base node with visualization properties.
 */
export interface TreeNodeData {
  name: string;           // Display label (success_rate %)
  attributes?: {
    action?: string;      // Truncated action text
    status: NodeStatus;   // For color coding
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
  winner: '#22c55e',      // green-500
  active: '#3b82f6',      // blue-500
  dominated: '#94a3b8',   // slate-400
  expansion_failed: '#ef4444', // red-500
};

/**
 * Badge variants for node status.
 */
export const NODE_STATUS_BADGES: Record<NodeStatus, {
  label: string;
  variant: 'success' | 'info' | 'neutral' | 'error';
}> = {
  winner: { label: 'Vencedor', variant: 'success' },
  active: { label: 'Ativo', variant: 'info' },
  dominated: { label: 'Dominado', variant: 'neutral' },
  expansion_failed: { label: 'Falhou', variant: 'error' },
};
```

### Exploration List Types (for experiment page)

```typescript
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

/**
 * Status badge configuration.
 */
export const EXPLORATION_STATUS_CONFIG: Record<ExplorationStatus, {
  label: string;
  variant: 'success' | 'info' | 'warning' | 'error' | 'neutral';
  icon: string; // Lucide icon name
}> = {
  running: { label: 'Executando', variant: 'info', icon: 'Loader2' },
  goal_achieved: { label: 'Meta Atingida', variant: 'success', icon: 'CheckCircle' },
  depth_limit_reached: { label: 'Limite Profundidade', variant: 'warning', icon: 'AlertTriangle' },
  cost_limit_reached: { label: 'Limite Custo', variant: 'warning', icon: 'AlertTriangle' },
  no_viable_paths: { label: 'Sem Caminhos', variant: 'error', icon: 'XCircle' },
};
```

## Data Flow

```
API Backend                    Frontend
────────────────────────────────────────────

GET /explorations/{id}/tree
    │
    ▼
ExplorationTree ───────────► transformToTreeData()
    │                              │
    │                              ▼
    │                        TreeNodeData[]
    │                              │
    │                              ▼
    │                        <Tree data={...} />
    │
    ▼
ScenarioNode[] ────────────► NodeDetailsPanel
                              (selected node)
```

## Utility Functions

```typescript
/**
 * Transform API nodes to react-d3-tree format.
 */
export function transformToTreeData(nodes: ScenarioNode[]): TreeNodeData | null {
  // Build parent-child map
  const nodeMap = new Map<string, ScenarioNode>();
  const childrenMap = new Map<string, string[]>();

  nodes.forEach(node => {
    nodeMap.set(node.id, node);
    if (node.parent_id) {
      const siblings = childrenMap.get(node.parent_id) || [];
      siblings.push(node.id);
      childrenMap.set(node.parent_id, siblings);
    }
  });

  // Find root (parent_id === null)
  const root = nodes.find(n => n.parent_id === null);
  if (!root) return null;

  // Recursive build
  function buildNode(nodeId: string): TreeNodeData {
    const node = nodeMap.get(nodeId)!;
    const childIds = childrenMap.get(nodeId) || [];

    return {
      name: node.simulation_results
        ? `${(node.simulation_results.success_rate * 100).toFixed(0)}%`
        : '—',
      attributes: {
        action: node.action_applied
          ? node.action_applied.slice(0, 30) + (node.action_applied.length > 30 ? '...' : '')
          : undefined,
        status: node.node_status,
      },
      children: childIds.length > 0
        ? childIds.map(buildNode)
        : undefined,
      __nodeData: node,
    };
  }

  return buildNode(root.id);
}

/**
 * Format success rate as percentage.
 */
export function formatSuccessRate(rate: number | null): string {
  if (rate === null) return '—';
  return `${(rate * 100).toFixed(1)}%`;
}

/**
 * Format delta with sign.
 */
export function formatDelta(delta: number): string {
  const sign = delta >= 0 ? '+' : '';
  return `${sign}${(delta * 100).toFixed(1)}%`;
}
```

## Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| goal_value | 0 ≤ x ≤ 1 | "Meta deve estar entre 0% e 100%" |
| beam_width | 1 ≤ x ≤ 10 | "Beam width deve estar entre 1 e 10" |
| max_depth | 1 ≤ x ≤ 10 | "Profundidade máxima deve estar entre 1 e 10" |

## Zod Schema (for form validation)

```typescript
import { z } from 'zod';

export const explorationCreateSchema = z.object({
  experiment_id: z.string().regex(/^exp_[a-f0-9]{8}$/),
  goal_value: z.number()
    .min(0, 'Meta deve ser maior que 0%')
    .max(1, 'Meta deve ser menor que 100%'),
  beam_width: z.number()
    .int()
    .min(1, 'Beam width mínimo é 1')
    .max(10, 'Beam width máximo é 10')
    .default(3),
  max_depth: z.number()
    .int()
    .min(1, 'Profundidade mínima é 1')
    .max(10, 'Profundidade máxima é 10')
    .default(5),
});

export type ExplorationCreateForm = z.infer<typeof explorationCreateSchema>;
```

/**
 * TypeScript types for quantitative analysis (causal DAG + Monte Carlo simulation).
 *
 * Maps to API contracts in specs/042-quantitative-analysis/contracts/api.md
 */

// --- Causal Model Types ---

export interface LikertOption {
  text: string;
  mu: number;
  sigma: number;
}

export interface CausalEdge {
  id: string;
  from_node: string;
  to_node: string;
  user_var: string;
  direction: 1 | -1;
  header: string;
  options: [LikertOption, LikertOption, LikertOption, LikertOption, LikertOption];
  default_option: number;
  selected_option: number | null;
}

export interface CausalModel {
  id: string;
  experiment_id: string;
  label: string;
  intercept_mu: number;
  intercept_sigma: number;
  nodes: string[];
  edges: CausalEdge[];
  created_at: string;
}

// --- Edge Selection Types ---

export interface EdgeSelections {
  selections: Record<string, number>;
}

export interface EdgeUpdateResponse {
  updated_count: number;
  all_answered: boolean;
  answered_count: number;
  total_edges: number;
}

// --- Simulation Types ---

export interface SimulationStats {
  mean: number;
  median: number;
  std: number;
  p10: number;
  p90: number;
}

export interface SegmentResult {
  rate: number;
  count: number;
}

export interface Segments {
  age: Record<string, SegmentResult>;
  income: Record<string, SegmentResult>;
  education: Record<string, SegmentResult>;
}

export interface SensitivityItem {
  edge_id: string;
  header: string;
  impact: number;
  mean_low: number;
  mean_high: number;
}

export interface Interpretation {
  raw_text: string;
  ai_text: string;
}

export interface SimulationInterpretations {
  distribution: Interpretation;
  segments: Interpretation;
  sensitivity: Interpretation;
}

export interface SimulationRun {
  id: string;
  experiment_id: string;
  causal_model_id: string;
  n_iterations: number;
  n_synths: number;
  stats: SimulationStats;
  distribution: number[];
  segments: Segments;
  sensitivity: SensitivityItem[];
  interpretations: SimulationInterpretations;
  created_at: string;
}

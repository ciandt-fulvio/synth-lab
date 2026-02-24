/**
 * TypeScript types for quantitative analysis (causal DAG + Monte Carlo simulation).
 *
 * Maps to API contracts in specs/042-quantitative-analysis/contracts/api.md
 */

// --- Node Types ---

export type NodeType = 'demographic' | 'sensitivity' | 'product' | 'interaction' | 'outcome';

export interface CausalNodeMeta {
  name: string;
  node_type: NodeType;
  product_calibration?: 'low' | 'medium' | 'high' | null;
  product_description?: string | null;
  sensitivity_key?: string | null;
  description?: string | null;
  // Premissa fields (interaction + outcome nodes)
  header?: string | null;
  options?: LikertOption[] | null;
  default_option?: number | null;
  selected_option?: number | null;
}

// --- Node Selections Types ---

export interface NodeSelections {
  selections: Record<string, number>;
}

export interface NodeSelectionsResponse {
  updated_count: number;
  all_answered: boolean;
  answered_count: number;
  total_nodes: number;
}

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
  user_var: string | null;
  direction: 1 | -1;
  header: string;
  options: LikertOption[];
  default_option: number;
  selected_option: number | null;
  edge_type: 'likert' | 'fixed';
  weight: number | null;
}

export interface CausalModel {
  id: string;
  experiment_id: string;
  label: string;
  intercept_mu: number;
  intercept_sigma: number;
  nodes: string[];
  node_metadata: Record<string, CausalNodeMeta> | null;
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

// --- Product Calibration Types ---

export interface ProductCalibrationRequest {
  calibrations: Record<string, string>;
}

export interface ProductCalibrationResponse {
  updated_count: number;
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

// --- Multi-Scenario Batch Types ---

export interface ScenarioRunResult {
  run_id: string;
  product_values: Record<string, string>;
  stats: SimulationStats;
  n_synths: number;
}

export interface MultiScenarioResponse {
  batch_id: string;
  experiment_id: string;
  n_scenarios: number;
  n_synths: number;
  n_repetitions: number;
  status: string;
  created_at: string | null;
  scenarios: ScenarioRunResult[];
}

// --- Synth Profile Types ---

export interface SynthGroupProfile {
  count: number;
  avg_age: number | null;
  avg_income: number | null;
  top_education: string;
  avg_adoption: number;
}

export interface ClusterStats {
  count: number;
  avg_adoption: number;
}

export interface ProductSynthCorrelationResponse {
  product_attributes: string[];
  clusters: string[];
  matrix: Record<string, Record<string, number>>; // cluster → {attr: diff_pp}
}

export interface SynthProfilesResponse {
  best_scenario_mean: number;
  best_scenario_product_values: Record<string, string>;
  adopters: SynthGroupProfile;
  rejectors: SynthGroupProfile;
  clusters: Record<string, ClusterStats>;
}

// --- Synth Attribute Insights Types ---

export interface SynthAttributeCorrelation {
  attribute: string;
  label: string;
  r_value: number;
  is_positive: boolean;
}

export interface SynthSegmentHeatmapCell {
  row_bin: string;
  col_bin: string;
  adoption_pct: number;
  count: number;
}

export interface SynthAttributeInsightsResponse {
  correlations: SynthAttributeCorrelation[];
  heatmap_row_attr: string;
  heatmap_col_attr: string;
  heatmap_row_label: string;
  heatmap_col_label: string;
  heatmap: SynthSegmentHeatmapCell[];
}

// --- Simulation Report ---

export interface SimulationReport {
  id: string;
  experiment_id: string;
  batch_id: string;
  content: string;  // markdown
  model: string;
  created_at: string;
}

// frontend/src/types/simulation.ts
// TypeScript types for simulation analysis results

// =============================================================================
// Phase 1: Overview Charts (Try vs Success, Distribution, Sankey)
// =============================================================================

/** Point in Try vs Success scatter chart */
export interface TryVsSuccessPoint {
  synth_id: string;
  attempt_rate: number;
  success_rate: number;
  quadrant: 'ok' | 'usability_issue' | 'discovery_issue' | 'low_value';
}

/** Quadrant summary for Try vs Success chart */
export interface QuadrantSummary {
  quadrant: 'ok' | 'usability_issue' | 'discovery_issue' | 'low_value';
  count: number;
  percentage: number;
}

/** Quadrant counts from API */
export interface QuadrantCounts {
  ok: number;
  usability_issue: number;
  discovery_issue: number;
  low_value: number;
}

/** Try vs Success scatter chart data */
export interface TryVsSuccessChart {
  simulation_id: string;
  points: TryVsSuccessPoint[];
  quadrant_counts: QuadrantCounts;
  quadrant_thresholds: {
    x: number;
    y: number;
  };
  total_synths: number;
}

/** Single synth distribution from API */
export interface SynthDistribution {
  synth_id: string;
  did_not_try_rate: number;
  failed_rate: number;
  success_rate: number;
  sort_key: number;
}

/** Outcome distribution chart data (from API) */
export interface OutcomeDistributionChart {
  simulation_id: string;
  distributions: SynthDistribution[];
  summary: {
    avg_success: number;
    avg_failed: number;
    avg_did_not_try: number;
    median_success: number;
    std_success: number;
  };
  worst_performers: string[];
  best_performers: string[];
  total_synths: number;
}

/** Node in Sankey diagram (from API) */
export interface SankeyNode {
  id: string;
  label: string;
  value: number;
}

/** Link in Sankey diagram (from API) */
export interface SankeyLink {
  source: string;
  target: string;
  value: number;
  percentage: number;
}

/** Sankey diagram data (from API) */
export interface SankeyChart {
  simulation_id: string;
  total_synths: number;
  nodes: SankeyNode[];
  links: SankeyLink[];
}

// =============================================================================
// Phase 2: Problem Location Charts (Heatmap, Box Plot, Scatter, Tornado)
// =============================================================================

/** Cell in failure heatmap */
export interface HeatmapCell {
  x_bin: string;
  y_bin: string;
  x_range: [number, number];
  y_range: [number, number];
  metric_value: number;
  synth_count: number;
  synth_ids: string[];
}

/** Failure heatmap chart data */
export interface FailureHeatmapChart {
  simulation_id: string;
  cells: HeatmapCell[];
  x_axis: string;
  y_axis: string;
  metric: 'failed_rate' | 'success_rate' | 'did_not_try_rate';
  bins: number;
  max_value: number;
  min_value: number;
  critical_cells: HeatmapCell[];
  critical_threshold: number;
}

/** Box plot statistics */
export interface BoxPlotStats {
  category: string;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  outliers: number[];
}

/** Box plot chart data */
export interface BoxPlotChart {
  simulation_id: string;
  series: BoxPlotStats[];
  attribute: string;
}

/** Point in scatter correlation chart */
export interface ScatterPoint {
  synth_id: string;
  x_value: number;
  y_value: number;
}

/** Correlation statistics */
export interface CorrelationStats {
  pearson_r: number;
  p_value: number;
  r_squared: number;
  is_significant: boolean;
  trend_slope: number;
  trend_intercept: number;
}

/** Point on the trend line */
export interface TrendlinePoint {
  x: number;
  y: number;
}

/** Scatter correlation chart data */
export interface ScatterCorrelationChart {
  simulation_id: string;
  points: ScatterPoint[];
  x_axis: string;
  y_axis: string;
  correlation: CorrelationStats;
  trendline: TrendlinePoint[];
}

/** Bar in tornado chart */
export interface TornadoBar {
  dimension: string;
  low_delta: number;
  high_delta: number;
  impact_score: number;
}

/** Tornado chart data */
export interface TornadoChart {
  simulation_id: string;
  bars: TornadoBar[];
  baseline_success: number;
}

// =============================================================================
// Phase 3: Clustering (K-Means, Hierarchical, Radar)
// =============================================================================

/** Cluster profile from K-Means */
export interface ClusterProfile {
  cluster_id: number;
  size: number;
  percentage: number;
  centroid: Record<string, number>;
  avg_success_rate: number;
  avg_failed_rate: number;
  avg_did_not_try_rate: number;
  label?: string;
}

/** Elbow chart data point */
export interface ElbowDataPoint {
  k: number;
  inertia: number;
  silhouette: number;
}

/** K-Means clustering result */
export interface KMeansResult {
  simulation_id: string;
  n_clusters: number;
  clusters: ClusterProfile[];
  elbow_data: ElbowDataPoint[];
  synth_assignments: Record<string, number>;
  features_used: string[];
}

/** Node in dendrogram tree */
export interface DendrogramNode {
  id: number;
  left?: DendrogramNode;
  right?: DendrogramNode;
  distance: number;
  synth_count: number;
  synth_ids: string[];
}

/** Suggested cut point for hierarchical clustering */
export interface SuggestedCut {
  n_clusters: number;
  distance: number;
  silhouette: number;
}

/** Hierarchical clustering result */
export interface HierarchicalResult {
  simulation_id: string;
  dendrogram: DendrogramNode;
  linkage_method: 'ward' | 'complete' | 'average' | 'single';
  suggested_cuts: SuggestedCut[];
  features_used: string[];
  cluster_assignments?: Record<string, number>;
  cluster_profiles?: ClusterProfile[];
}

/** Radar chart axis value */
export interface RadarAxis {
  axis: string;
  value: number;
}

/** Cluster radar data */
export interface ClusterRadar {
  cluster_id: number;
  label: string;
  data: RadarAxis[];
}

/** Radar chart comparison data */
export interface RadarChart {
  simulation_id: string;
  clusters: ClusterRadar[];
  axis_labels: string[];
  baseline?: RadarAxis[];
}

// =============================================================================
// Phase 4: Edge Cases & Outliers
// =============================================================================

/** Synth identified as extreme case */
export interface ExtremeSynth {
  synth_id: string;
  success_rate: number;
  failed_rate: number;
  did_not_try_rate: number;
  attributes: Record<string, number>;
  category: 'worst_failure' | 'best_success' | 'unexpected';
  suggested_questions: string[];
}

/** Table of extreme cases */
export interface ExtremeCasesTable {
  simulation_id: string;
  worst_failures: ExtremeSynth[];
  best_successes: ExtremeSynth[];
  unexpected_cases: ExtremeSynth[];
}

/** Synth identified as statistical outlier */
export interface OutlierSynth {
  synth_id: string;
  anomaly_score: number;
  success_rate: number;
  failed_rate: number;
  did_not_try_rate: number;
  attributes: Record<string, number>;
  outlier_type: 'attribute_outlier' | 'outcome_outlier' | 'both';
  explanation: string;
}

/** Outlier detection result */
export interface OutlierResult {
  simulation_id: string;
  method: 'isolation_forest';
  contamination: number;
  outliers: OutlierSynth[];
  total_synths: number;
  outlier_percentage: number;
}

// =============================================================================
// Phase 5: Explainability (SHAP & PDP)
// =============================================================================

/** Single SHAP contribution */
export interface ShapContribution {
  feature: string;
  value: number;
  shap_value: number;
}

/** SHAP explanation for a single synth */
export interface ShapExplanation {
  simulation_id: string;
  synth_id: string;
  base_value: number;
  predicted_value: number;
  contributions: ShapContribution[];
  explanation_text?: string;
}

/** Feature importance from SHAP summary */
export interface FeatureImportance {
  feature: string;
  mean_abs_shap: number;
  direction: 'positive' | 'negative' | 'mixed';
}

/** SHAP summary (global feature importance) */
export interface ShapSummary {
  simulation_id: string;
  feature_importance: FeatureImportance[];
  top_features: string[];
  explanation_text?: string;
}

/** Point in PDP curve */
export interface PDPPoint {
  feature_value: number;
  avg_prediction: number;
  std_prediction?: number;
}

/** Partial Dependence Plot result */
export interface PDPResult {
  simulation_id: string;
  feature: string;
  points: PDPPoint[];
  feature_range: [number, number];
  effect_type: 'linear' | 'monotonic' | 'nonlinear' | 'threshold';
  effect_strength: number;
}

/** PDP comparison across features */
export interface PDPComparison {
  simulation_id: string;
  pdps: PDPResult[];
  feature_ranking: string[];
}

// =============================================================================
// Phase 6: LLM Insights
// =============================================================================

/** Chart types that can have insights generated */
export type ChartType =
  | 'try_vs_success'
  | 'distribution'
  | 'sankey'
  | 'failure_heatmap'
  | 'box_plot'
  | 'scatter'
  | 'tornado'
  | 'elbow'
  | 'radar'
  | 'dendrogram'
  | 'extreme_cases'
  | 'outliers'
  | 'shap_summary'
  | 'shap_explanation'
  | 'pdp'
  | 'pdp_comparison';

/** Caption for a chart */
export interface ChartCaption {
  short: string;
  medium: string;
}

/** Evidence supporting an insight */
export interface InsightEvidence {
  metric: string;
  value: string | number;
  interpretation: string;
}

/** LLM-generated insight for a chart */
export interface ChartInsight {
  simulation_id: string;
  chart_type: ChartType;
  caption: ChartCaption;
  explanation: string;
  evidence: InsightEvidence[];
  recommendation: string;
  generated_at: string;
}

/** All insights for a simulation */
export interface SimulationInsights {
  simulation_id: string;
  insights: ChartInsight[];
  executive_summary?: string;
  updated_at: string;
}

// =============================================================================
// Request Types
// =============================================================================

/** Request to create clustering */
export interface ClusterRequest {
  method: 'kmeans' | 'hierarchical';
  n_clusters?: number;
  features?: string[];
  linkage?: 'ward' | 'complete' | 'average' | 'single';
}

/** Request to cut dendrogram */
export interface CutDendrogramRequest {
  n_clusters: number;
}

/** Request to generate chart insight */
export interface GenerateInsightRequest {
  chart_data: Record<string, unknown>;
  force_regenerate?: boolean;
}

/** Executive summary response */
export interface ExecutiveSummaryResponse {
  simulation_id: string;
  summary: string;
  total_insights: number;
}

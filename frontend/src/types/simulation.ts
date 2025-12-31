// frontend/src/types/simulation.ts
// TypeScript types for simulation analysis results

// =============================================================================
// Phase 1: Overview Charts (Try vs Success, Distribution)
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


// =============================================================================
// Phase 2: Problem Location Charts (Heatmap, Box Plot, Scatter)
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

/** Correlation of single attribute with outcomes */
export interface AttributeCorrelation {
  attribute: string;
  attribute_label: string;
  correlation_attempt: number;
  correlation_success: number;
  p_value_attempt: number;
  p_value_success: number;
  is_significant_attempt: boolean;
  is_significant_success: boolean;
}

/** Attribute correlation chart data */
export interface AttributeCorrelationChart {
  simulation_id: string;
  correlations: AttributeCorrelation[];
  total_synths: number;
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

/** Node in dendrogram tree (hierarchical structure for rendering) */
export interface DendrogramTreeNode {
  id: string;
  height: number;
  count: number;
  children?: DendrogramTreeNode[] | null;
}

/** Suggested cut point for hierarchical clustering */
export interface SuggestedCut {
  n_clusters: number;
  distance: number;
  silhouette_estimate: number;
}

/** Flat node structure from backend */
export interface DendrogramNode {
  id: number;
  synth_id?: string;
  left_child?: number;
  right_child?: number;
  distance: number;
  count: number;
}

/** Hierarchical clustering result */
export interface HierarchicalResult {
  simulation_id: string;
  method: 'hierarchical';
  linkage_method: 'ward' | 'complete' | 'average' | 'single';
  features_used: string[];
  nodes: DendrogramNode[];
  suggested_cuts: SuggestedCut[];
  cluster_assignments?: Record<string, number>;
  n_clusters?: number;
  cut_height?: number;
  // Computed properties from backend
  dendrogram_tree: DendrogramTreeNode;
  total_synths: number;
  max_height: number;
}

/** Radar chart axis value */
export interface RadarAxis {
  name: string;
  label: string;
  value: number;
  normalized: number;
}

/** Cluster radar data */
export interface ClusterRadar {
  cluster_id: number;
  label: string;
  explanation: string;
  color: string;
  axes: RadarAxis[];
  success_rate: number;
}

/** Radar chart comparison data */
export interface RadarChart {
  simulation_id: string;
  clusters: ClusterRadar[];
  axis_labels: string[];
  baseline: number[];
}

/** Point in PCA scatter plot */
export interface PCAScatterPoint {
  synth_id: string;
  x: number;
  y: number;
  cluster_id: number;
  cluster_label: string;
  color: string;
}

/** PCA 2D scatter chart with cluster colors */
export interface PCAScatterChart {
  simulation_id: string;
  points: PCAScatterPoint[];
  explained_variance: [number, number];
  total_variance: number;
}

// =============================================================================
// Phase 4: Edge Cases & Outliers
// =============================================================================

/** Synth identified as extreme case */
export interface ExtremeSynth {
  synth_id: string;
  synth_name: string;
  success_rate: number;
  failed_rate: number;
  did_not_try_rate: number;
  category: 'worst_failure' | 'best_success' | 'unexpected';
  profile_summary: string;
  interview_questions: string[];
  capability_mean: number;
  trust_mean: number;
  friction_tolerance_mean: number;
}

/** Table of extreme cases */
export interface ExtremeCasesTable {
  simulation_id: string;
  worst_failures: ExtremeSynth[];
  best_successes: ExtremeSynth[];
  unexpected_cases: ExtremeSynth[];
  total_synths: number;
}

/** Synth identified as statistical outlier */
export interface OutlierSynth {
  synth_id: string;
  anomaly_score: number;
  success_rate: number;
  failed_rate: number;
  did_not_try_rate: number;
  outlier_type: 'unexpected_failure' | 'unexpected_success' | 'atypical_profile';
  explanation: string;
  capability_mean: number;
  trust_mean: number;
  friction_tolerance_mean: number;
  digital_literacy: number;
  similar_tool_experience: number;
}

/** Outlier detection result */
export interface OutlierResult {
  simulation_id: string;
  method: 'isolation_forest';
  contamination: number;
  outliers: OutlierSynth[];
  total_synths: number;
  n_outliers: number;
  outlier_percentage: number;
  features_used: string[];
}

// =============================================================================
// Phase 5: Explainability (SHAP & PDP)
// =============================================================================

/** Single SHAP contribution */
export interface ShapContribution {
  feature_name: string;
  feature_value: number;
  shap_value: number;
  baseline_value: number;
  impact: 'positive' | 'negative';
}

/** SHAP explanation for a single synth */
export interface ShapExplanation {
  simulation_id: string;
  synth_id: string;
  predicted_success_rate: number;
  actual_success_rate: number;
  baseline_prediction: number;
  contributions: ShapContribution[];
  explanation_text: string;
  model_type: string;
}

/** SHAP summary (global feature importance) */
export interface ShapSummary {
  simulation_id: string;
  feature_importances: Record<string, number>;
  top_features: string[];
  total_synths: number;
  model_score: number;
}

/** Point in PDP curve */
export interface PDPPoint {
  feature_value: number;
  predicted_success: number;
  confidence_lower?: number;
  confidence_upper?: number;
}

/** Partial Dependence Plot result */
export interface PDPResult {
  simulation_id: string;
  feature_name: string;
  feature_display_name: string;
  pdp_values: PDPPoint[];
  effect_type: 'monotonic_increasing' | 'monotonic_decreasing' | 'non_linear' | 'flat';
  effect_strength: number;
  baseline_value: number;
}

/** PDP comparison across features */
export interface PDPComparison {
  simulation_id: string;
  pdp_results: PDPResult[];
  feature_ranking: string[];
  total_synths: number;
}

// =============================================================================
// Phase 6: LLM Insights
// =============================================================================

/** Chart types that can have insights generated */
export type ChartType =
  | 'try_vs_success'
  | 'distribution'
  | 'failure_heatmap'
  | 'box_plot'
  | 'scatter'
  | 'elbow'
  | 'radar'
  | 'dendrogram'
  | 'pca_scatter'
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

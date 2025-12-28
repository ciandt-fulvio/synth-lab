# Data Model: Experiment Results Frontend

**Feature**: 020-experiment-results-frontend
**Date**: 2025-12-28
**Location**: `frontend/src/types/simulation.ts`

## Overview

This document defines TypeScript types for the simulation analysis frontend. Types mirror backend Pydantic models from:
- `synth_lab/domain/entities/chart_insight.py`
- `synth_lab/domain/entities/cluster_result.py`
- `synth_lab/domain/entities/outlier_result.py`
- `synth_lab/domain/entities/explainability.py`
- Chart entities from `synth_lab/domain/entities/__init__.py`

## Types Definition

```typescript
// frontend/src/types/simulation.ts

// =============================================================================
// Phase 1: Overview Charts (Try vs Success, Distribution, Sankey)
// =============================================================================

/** Point in Try vs Success scatter chart */
export interface TryVsSuccessPoint {
  synth_id: string;
  attempt_rate: number;  // 1 - did_not_try_rate
  success_rate: number;
  quadrant: 'ok' | 'usability_issue' | 'discovery_issue' | 'low_value';
}

/** Quadrant summary for Try vs Success chart */
export interface QuadrantSummary {
  quadrant: 'ok' | 'usability_issue' | 'discovery_issue' | 'low_value';
  count: number;
  percentage: number;
}

/** Try vs Success scatter chart data */
export interface TryVsSuccessChart {
  simulation_id: string;
  points: TryVsSuccessPoint[];
  quadrants: QuadrantSummary[];
  thresholds: {
    attempt_rate: number;
    success_rate: number;
  };
}

/** Single outcome bar for distribution chart */
export interface OutcomeBar {
  synth_id: string;
  did_not_try_rate: number;
  failed_rate: number;
  success_rate: number;
}

/** Outcome distribution chart data */
export interface OutcomeDistributionChart {
  simulation_id: string;
  bars: OutcomeBar[];
  summary: {
    total_synths: number;
    avg_success_rate: number;
    avg_failed_rate: number;
    avg_did_not_try_rate: number;
  };
}

/** Node in Sankey diagram */
export interface SankeyNode {
  name: string;
}

/** Link in Sankey diagram */
export interface SankeyLink {
  source: number;
  target: number;
  value: number;
}

/** Sankey diagram data */
export interface SankeyChart {
  simulation_id: string;
  nodes: SankeyNode[];
  links: SankeyLink[];
}

// =============================================================================
// Phase 2: Problem Location Charts (Heatmap, Box Plot, Scatter, Tornado)
// =============================================================================

/** Cell in failure heatmap */
export interface HeatmapCell {
  x_bin: number;
  y_bin: number;
  x_label: string;
  y_label: string;
  count: number;
  metric_value: number;
}

/** Failure heatmap chart data */
export interface FailureHeatmapChart {
  simulation_id: string;
  cells: HeatmapCell[];
  x_axis: string;
  y_axis: string;
  x_labels: string[];
  y_labels: string[];
  metric: 'failed_rate' | 'success_rate' | 'did_not_try_rate';
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
  x: number;
  y: number;
  outcome: 'success' | 'failed' | 'did_not_try';
}

/** Trend line in scatter chart */
export interface TrendLine {
  slope: number;
  intercept: number;
  r_squared: number;
}

/** Scatter correlation chart data */
export interface ScatterCorrelationChart {
  simulation_id: string;
  points: ScatterPoint[];
  x_axis: string;
  y_axis: string;
  correlation: number;
  p_value: number;
  trendline?: TrendLine;
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
  synth_assignments: Record<string, number>;  // synth_id -> cluster_id
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
  value: number;       // Feature value for this synth
  shap_value: number;  // SHAP contribution (positive or negative)
}

/** SHAP explanation for a single synth */
export interface ShapExplanation {
  simulation_id: string;
  synth_id: string;
  base_value: number;          // Expected value (average prediction)
  predicted_value: number;     // Actual prediction for this synth
  contributions: ShapContribution[];
  explanation_text?: string;   // Human-readable explanation
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
  effect_strength: number;  // 0-1 scale
}

/** PDP comparison across features */
export interface PDPComparison {
  simulation_id: string;
  pdps: PDPResult[];
  feature_ranking: string[];  // Sorted by effect_strength
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
  short: string;   // <=20 tokens
  medium: string;  // <=50 tokens
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
  explanation: string;      // <=200 tokens
  evidence: InsightEvidence[];
  recommendation: string;   // Actionable suggestion
  generated_at: string;     // ISO datetime
}

/** All insights for a simulation */
export interface SimulationInsights {
  simulation_id: string;
  insights: ChartInsight[];
  executive_summary?: string;
  updated_at: string;
}

// =============================================================================
// Clustering Request Types
// =============================================================================

/** Request to create clustering */
export interface ClusterRequest {
  method: 'kmeans' | 'hierarchical';
  n_clusters?: number;          // Required for kmeans
  features?: string[];          // Optional feature selection
  linkage?: 'ward' | 'complete' | 'average' | 'single';  // For hierarchical
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
```

## Field Mappings

| Backend Field | Frontend Field | Notes |
|--------------|----------------|-------|
| `synth_id` | `synth_id` | String UUID |
| `simulation_id` | `simulation_id` | String UUID |
| `cluster_id` | `cluster_id` | Number (0-indexed) |
| `shap_value` | `shap_value` | Number (positive/negative) |
| `metric_value` | `metric_value` | Number (0-1 scale) |
| `generated_at` | `generated_at` | ISO 8601 string |

## Validation Rules

1. All rate values (success_rate, failed_rate, did_not_try_rate) must be in [0, 1]
2. Rates should sum to ~1.0 (allowing for floating-point precision)
3. Cluster IDs are 0-indexed integers
4. SHAP values can be positive or negative
5. Anomaly scores are typically in [0, 1] with higher = more anomalous

## State Transitions

### Clustering State
```
[No Clusters] --POST /clusters--> [Clusters Generated]
[Clusters Generated] --GET /clusters--> [View Clusters]
[Hierarchical Result] --POST /cut--> [Cut with Assignments]
```

### Insight Generation State
```
[No Insight] --POST /insights/{chart_type}--> [Generating]
[Generating] --success--> [Available]
[Generating] --failure--> [Failed]
[Available] --force_regenerate=true--> [Generating]
```

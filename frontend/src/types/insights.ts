/**
 * TypeScript types for AI-generated insights feature.
 *
 * Mirrors backend entities from src/synth_lab/domain/entities/chart_insight.py
 * and executive_summary.py
 *
 * References:
 *   - Spec: specs/023-quantitative-ai-insights/spec.md
 *   - Data Model: specs/023-quantitative-ai-insights/data-model.md
 */

/**
 * AI-generated insight for a specific chart type.
 */
export interface ChartInsight {
  analysis_id: string
  chart_type: string
  problem_understanding: string
  trends_observed: string
  key_findings: string[] // 2-4 items
  summary: string // ≤200 words
  generation_timestamp: string // ISO 8601
  status: "pending" | "completed" | "failed"
  model: string // e.g., "o1-mini"
  reasoning_trace?: string | null
}

/**
 * Aggregated synthesis of all chart insights for an analysis.
 */
export interface ExecutiveSummary {
  analysis_id: string
  overview: string // ≤200 words
  explainability: string // ≤200 words
  segmentation: string // ≤200 words
  edge_cases: string // ≤200 words
  recommendations: string[] // 2-3 items
  included_chart_types: string[] // min 1
  generation_timestamp: string // ISO 8601
  status: "pending" | "completed" | "failed" | "partial"
  model: string // e.g., "o1-mini"
}

/**
 * Chart types that support AI-generated insights.
 */
export type ChartTypeWithInsight =
  | "try_vs_success"
  | "shap_summary"
  | "pdp"
  | "pca_scatter"
  | "radar_comparison"
  | "extreme_cases"
  | "outliers"

/**
 * Response from GET /experiments/{id}/insights (all insights + stats).
 */
export interface AllInsightsResponse {
  analysis_id: string
  insights: ChartInsight[]
  executive_summary: ExecutiveSummary | null
  stats: {
    total_charts: number
    completed_insights: number
    pending_insights: number
    failed_insights: number
  }
}

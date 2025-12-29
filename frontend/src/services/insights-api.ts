/**
 * Insights API Client
 *
 * TypeScript client for AI-generated chart insights and executive summaries.
 *
 * References:
 *   - Backend API: src/synth_lab/api/routers/insights.py
 *   - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 1, 2)
 *
 * Endpoints:
 *   - GET /experiments/{id}/insights/{chart_type} - Get specific chart insight
 *   - GET /experiments/{id}/insights - Get all insights with stats
 *   - GET /experiments/{id}/insights/executive-summary - Get executive summary
 */

import { fetchAPI } from './api';
import type { ChartInsight, AllInsightsResponse, ExecutiveSummary } from '../types/insights';

/**
 * Get AI-generated insight for a specific chart type.
 *
 * @param experimentId - Experiment ID
 * @param chartType - Chart type (try_vs_success, shap_summary, pdp, pca_scatter, radar_comparison, extreme_cases, outliers)
 * @returns ChartInsight for the requested chart type
 * @throws 404 if experiment or insight not found
 * @throws 400 if chart_type is invalid
 */
export async function getChartInsight(
  experimentId: string,
  chartType: string
): Promise<ChartInsight> {
  return fetchAPI<ChartInsight>(`/experiments/${experimentId}/insights/${chartType}`);
}

/**
 * Get all chart insights for an experiment with statistics.
 *
 * Returns all generated insights along with stats about completion progress.
 *
 * @param experimentId - Experiment ID
 * @returns All insights, executive summary (if available), and stats
 * @throws 404 if experiment or analysis not found
 */
export async function getAllChartInsights(experimentId: string): Promise<AllInsightsResponse> {
  return fetchAPI<AllInsightsResponse>(`/experiments/${experimentId}/insights`);
}

/**
 * Get executive summary synthesizing all chart insights.
 *
 * @param experimentId - Experiment ID
 * @returns ExecutiveSummary with aggregated insights
 * @throws 404 if experiment, analysis, or summary not found
 */
export async function getExecutiveSummary(experimentId: string): Promise<ExecutiveSummary> {
  return fetchAPI<ExecutiveSummary>(`/experiments/${experimentId}/insights/executive-summary`);
}

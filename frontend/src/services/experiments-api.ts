/**
 * T021 Experiments API service.
 *
 * API client for experiment CRUD operations.
 *
 * References:
 *   - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
 *   - Types: src/types/experiment.ts
 */

import { fetchAPI } from './api';
import type {
  ExperimentCreate,
  ExperimentUpdate,
  ExperimentDetail,
  PaginatedExperimentSummary,
  AnalysisSummary,
} from '@/types/experiment';
import type { FeatureMechanisms } from '@/types/simulation';
import type { InterviewCreateRequest, ResearchExecuteResponse } from '@/types/research';

/**
 * Pagination parameters for experiments list.
 */
export interface ExperimentsListParams {
  limit?: number;
  offset?: number;
  search?: string;
  tag?: string;
  sort_by?: 'created_at' | 'name';
  sort_order?: 'asc' | 'desc';
}

/**
 * List experiments with pagination, search, and sorting.
 */
export async function listExperiments(
  params?: ExperimentsListParams
): Promise<PaginatedExperimentSummary> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());
  if (params?.search) queryParams.append('search', params.search);
  if (params?.tag) queryParams.append('tag', params.tag);
  if (params?.sort_by) queryParams.append('sort_by', params.sort_by);
  if (params?.sort_order) queryParams.append('sort_order', params.sort_order);

  const query = queryParams.toString();
  const endpoint = query ? `/experiments/list?${query}` : '/experiments/list';

  return fetchAPI<PaginatedExperimentSummary>(endpoint);
}

/**
 * Get experiment details by ID.
 */
export async function getExperiment(id: string): Promise<ExperimentDetail> {
  return fetchAPI<ExperimentDetail>(`/experiments/${id}`);
}

/**
 * Create a new experiment.
 */
export async function createExperiment(
  data: ExperimentCreate
): Promise<ExperimentDetail> {
  return fetchAPI<ExperimentDetail>('/experiments', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update an existing experiment.
 */
export async function updateExperiment(
  id: string,
  data: ExperimentUpdate
): Promise<ExperimentDetail> {
  return fetchAPI<ExperimentDetail>(`/experiments/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Delete an experiment.
 */
export async function deleteExperiment(id: string): Promise<void> {
  return fetchAPI<void>(`/experiments/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Update feature mechanisms for an experiment.
 *
 * Updates only the mechanisms field in the experiment's scorecard_data.
 * Reference: specs/038-mechanism-based-simulation
 */
export async function updateExperimentMechanisms(
  id: string,
  mechanisms: FeatureMechanisms
): Promise<ExperimentDetail> {
  return fetchAPI<ExperimentDetail>(`/experiments/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ mechanisms }),
  });
}

/**
 * Create an interview linked to an experiment.
 *
 * The interview is automatically associated with the specified experiment.
 */
export async function createInterviewForExperiment(
  experimentId: string,
  data: InterviewCreateRequest
): Promise<ResearchExecuteResponse> {
  return fetchAPI<ResearchExecuteResponse>(`/experiments/${experimentId}/interviews`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Create an automatic interview with extreme cases (top 5 + bottom 5 performers).
 *
 * Automatically selects the 10 most extreme synths from the experiment's
 * simulation results and creates an interview with them.
 */
/**
 * Get auto-interview for an experiment if it exists.
 *
 * Returns the most recent auto-interview (extreme cases) created for this experiment.
 */
export async function getAutoInterview(
  experimentId: string
): Promise<ResearchExecuteResponse | null> {
  return fetchAPI<ResearchExecuteResponse | null>(
    `/experiments/${experimentId}/interviews/auto`
  );
}

/**
 * Create auto-interview with extreme cases (5 best + 5 worst).
 */
export async function createAutoInterview(
  experimentId: string
): Promise<ResearchExecuteResponse> {
  return fetchAPI<ResearchExecuteResponse>(`/experiments/${experimentId}/interviews/auto`, {
    method: 'POST',
  });
}

/**
 * Request for running analysis.
 */
export interface RunAnalysisRequest {
  /** Number of synths to simulate (default: 500) */
  n_synths?: number;
  /** Number of Monte Carlo executions per synth (default: 100) */
  n_executions?: number;
  /** Standard deviation for noise (default: 0.05) */
  sigma?: number;
  /** Random seed for reproducibility */
  seed?: number;
}

/**
 * Run quantitative analysis for an experiment.
 *
 * Creates and executes a Monte Carlo simulation to estimate adoption rates.
 * Requires the experiment to have a scorecard configured.
 */
export async function runAnalysis(
  experimentId: string,
  config?: RunAnalysisRequest
): Promise<AnalysisSummary> {
  return fetchAPI<AnalysisSummary>(`/experiments/${experimentId}/analysis`, {
    method: 'POST',
    body: config ? JSON.stringify(config) : undefined,
  });
}

// =============================================================================
// Analysis Chart Endpoints
// =============================================================================

import type {
  OutcomeDistributionChart,
  FailureHeatmapChart,
  ScatterCorrelationChart,
} from '@/types/simulation';

/**
 * Get outcome distribution chart for experiment analysis.
 */
export async function getAnalysisDistributionChart(
  experimentId: string,
  sortBy = 'adopted_rate',
  order = 'desc',
  limit = 50
): Promise<OutcomeDistributionChart> {
  const params = new URLSearchParams({
    sort_by: sortBy,
    order,
    limit: String(limit),
  });
  return fetchAPI(`/experiments/${experimentId}/analysis/charts/distribution?${params}`);
}

/**
 * Get failure heatmap chart for experiment analysis.
 */
export async function getAnalysisFailureHeatmap(
  experimentId: string,
  xAxis = 'capability_mean',
  yAxis = 'trust_mean',
  bins = 5,
  metric = 'not_adopted_rate'
): Promise<FailureHeatmapChart> {
  const params = new URLSearchParams({
    x_axis: xAxis,
    y_axis: yAxis,
    bins: String(bins),
    metric,
  });
  return fetchAPI(`/experiments/${experimentId}/analysis/charts/failure-heatmap?${params}`);
}

/**
 * Get scatter correlation chart for experiment analysis.
 */
export async function getAnalysisScatterCorrelation(
  experimentId: string,
  xAxis = 'trust_mean',
  yAxis = 'adopted_rate',
  showTrendline = true
): Promise<ScatterCorrelationChart> {
  const params = new URLSearchParams({
    x_axis: xAxis,
    y_axis: yAxis,
    show_trendline: String(showTrendline),
  });
  return fetchAPI(`/experiments/${experimentId}/analysis/charts/scatter?${params}`);
}

// =============================================================================
// Phase 3: Edge Cases & Outliers Endpoints
// =============================================================================

import type {
  ExtremeCasesTable,
  OutlierResult,
  ShapSummary,
  ShapExplanation,
} from '@/types/simulation';

/**
 * Get extreme cases for qualitative research.
 */
export async function getAnalysisExtremeCases(
  experimentId: string,
  nPerCategory = 10
): Promise<ExtremeCasesTable> {
  const params = new URLSearchParams({ n_per_category: String(nPerCategory) });
  return fetchAPI(`/experiments/${experimentId}/analysis/extreme-cases?${params}`);
}

/**
 * Get statistical outliers using Isolation Forest.
 */
export async function getAnalysisOutliers(
  experimentId: string,
  contamination = 0.1
): Promise<OutlierResult> {
  const params = new URLSearchParams({ contamination: String(contamination) });
  return fetchAPI(`/experiments/${experimentId}/analysis/outliers?${params}`);
}

// =============================================================================
// Explainability (SHAP) Endpoints
// =============================================================================

/**
 * Get global SHAP summary showing feature importance.
 */
export async function getAnalysisShapSummary(experimentId: string): Promise<ShapSummary> {
  return fetchAPI(`/experiments/${experimentId}/analysis/shap/summary`);
}

/**
 * Get SHAP explanation for a specific synth.
 */
export async function getAnalysisShapExplanation(
  experimentId: string,
  synthId: string
): Promise<ShapExplanation> {
  return fetchAPI(`/experiments/${experimentId}/analysis/shap/${synthId}`);
}

// =============================================================================
// Insights Endpoints
// =============================================================================

import type { SimulationInsights, ChartInsight } from '@/types/simulation';

/**
 * Get all cached insights for experiment analysis.
 */
export async function getAnalysisInsights(experimentId: string): Promise<SimulationInsights> {
  return fetchAPI(`/experiments/${experimentId}/analysis/insights`);
}

/**
 * Generate LLM insight for a specific chart.
 */
export async function generateAnalysisChartInsight(
  experimentId: string,
  chartType: string,
  chartData: Record<string, unknown>
): Promise<ChartInsight> {
  return fetchAPI(`/experiments/${experimentId}/analysis/insights/${chartType}`, {
    method: 'POST',
    body: JSON.stringify({ chart_type: chartType, chart_data: chartData }),
  });
}

interface GenerateSummaryResponse {
  executive_summary: string;
  total_insights: number;
}

/**
 * Generate executive summary from all insights.
 */
export async function generateAnalysisExecutiveSummary(
  experimentId: string
): Promise<GenerateSummaryResponse> {
  return fetchAPI(`/experiments/${experimentId}/analysis/insights/executive-summary`, {
    method: 'POST',
  });
}

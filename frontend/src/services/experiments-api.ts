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
  ScorecardCreate,
  ScorecardResponse,
  ScorecardEstimateResponse,
  AnalysisSummary,
} from '@/types/experiment';
import type { InterviewCreateRequest, ResearchExecuteResponse } from '@/types/research';
import type { PaginationParams } from '@/types';

/**
 * List experiments with pagination.
 */
export async function listExperiments(
  params?: PaginationParams
): Promise<PaginatedExperimentSummary> {
  const queryParams = new URLSearchParams();

  if (params?.limit) queryParams.append('limit', params.limit.toString());
  if (params?.offset) queryParams.append('offset', params.offset.toString());

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
 * Create a scorecard linked to an experiment.
 *
 * The scorecard is automatically associated with the specified experiment.
 */
export async function createScorecardForExperiment(
  experimentId: string,
  data: ScorecardCreate
): Promise<ScorecardResponse> {
  return fetchAPI<ScorecardResponse>(`/experiments/${experimentId}/scorecards`, {
    method: 'POST',
    body: JSON.stringify(data),
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
 * Estimate scorecard dimensions using AI.
 *
 * Uses the experiment's name, hypothesis, and description to generate
 * AI-powered estimates for all scorecard dimensions.
 */
export async function estimateScorecardForExperiment(
  experimentId: string
): Promise<ScorecardEstimateResponse> {
  return fetchAPI<ScorecardEstimateResponse>(
    `/experiments/${experimentId}/estimate-scorecard`,
    { method: 'POST' }
  );
}

/**
 * Request for scorecard estimation from text.
 */
export interface ScorecardEstimateRequest {
  name: string;
  hypothesis: string;
  description?: string;
}

/**
 * Estimate scorecard dimensions using AI from text input.
 *
 * This allows estimation before an experiment exists.
 * Useful for the experiment form to get AI-generated slider values.
 */
export async function estimateScorecardFromText(
  data: ScorecardEstimateRequest
): Promise<ScorecardEstimateResponse> {
  return fetchAPI<ScorecardEstimateResponse>(
    '/experiments/estimate-scorecard',
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  );
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
  TryVsSuccessChart,
  OutcomeDistributionChart,
  SankeyChart,
  FailureHeatmapChart,
  ScatterCorrelationChart,
  TornadoChart,
  AttributeCorrelationChart,
  ClusterRequest,
  KMeansResult,
  HierarchicalResult,
  CutDendrogramRequest,
  RadarComparisonChart,
  ElbowPoint,
} from '@/types/simulation';

/**
 * Get try vs success quadrant chart for experiment analysis.
 */
export async function getAnalysisTryVsSuccessChart(
  experimentId: string,
  attemptRateThreshold = 0.5,
  successRateThreshold = 0.5
): Promise<TryVsSuccessChart> {
  const params = new URLSearchParams({
    attempt_rate_threshold: String(attemptRateThreshold),
    success_rate_threshold: String(successRateThreshold),
  });
  return fetchAPI(`/experiments/${experimentId}/analysis/charts/try-vs-success?${params}`);
}

/**
 * Get outcome distribution chart for experiment analysis.
 */
export async function getAnalysisDistributionChart(
  experimentId: string,
  sortBy = 'success_rate',
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
 * Get sankey flow diagram for experiment analysis.
 */
export async function getAnalysisSankeyChart(experimentId: string): Promise<SankeyChart> {
  return fetchAPI(`/experiments/${experimentId}/analysis/charts/sankey`);
}

/**
 * Get failure heatmap chart for experiment analysis.
 */
export async function getAnalysisFailureHeatmap(
  experimentId: string,
  xAxis = 'capability_mean',
  yAxis = 'trust_mean',
  bins = 5,
  metric = 'failed_rate'
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
  yAxis = 'success_rate',
  showTrendline = true
): Promise<ScatterCorrelationChart> {
  const params = new URLSearchParams({
    x_axis: xAxis,
    y_axis: yAxis,
    show_trendline: String(showTrendline),
  });
  return fetchAPI(`/experiments/${experimentId}/analysis/charts/scatter?${params}`);
}

/**
 * Get tornado chart for experiment analysis.
 */
export async function getAnalysisTornadoChart(experimentId: string): Promise<TornadoChart> {
  return fetchAPI(`/experiments/${experimentId}/analysis/charts/tornado`);
}

/**
 * Get attribute correlations chart for experiment analysis.
 *
 * Shows correlation of each synth attribute with attempt_rate and success_rate.
 */
export async function getAnalysisAttributeCorrelations(
  experimentId: string
): Promise<AttributeCorrelationChart> {
  return fetchAPI(`/experiments/${experimentId}/analysis/charts/attribute-correlations`);
}

// =============================================================================
// Phase 3: Clustering Endpoints
// =============================================================================

/**
 * Create clustering for experiment analysis.
 */
export async function createAnalysisClustering(
  experimentId: string,
  request: ClusterRequest
): Promise<KMeansResult | HierarchicalResult> {
  return fetchAPI(`/experiments/${experimentId}/analysis/clusters`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get cached clustering for experiment analysis.
 */
export async function getAnalysisClustering(
  experimentId: string
): Promise<KMeansResult | HierarchicalResult> {
  return fetchAPI(`/experiments/${experimentId}/analysis/clusters`);
}

/**
 * Get elbow method data for experiment analysis.
 */
export async function getAnalysisElbow(
  experimentId: string,
  maxK = 10
): Promise<ElbowPoint[]> {
  const params = new URLSearchParams({ max_k: String(maxK) });
  return fetchAPI(`/experiments/${experimentId}/analysis/clusters/elbow?${params}`);
}

/**
 * Get dendrogram data for experiment analysis.
 */
export async function getAnalysisDendrogram(
  experimentId: string
): Promise<HierarchicalResult> {
  return fetchAPI(`/experiments/${experimentId}/analysis/clusters/dendrogram`);
}

/**
 * Get radar comparison chart for experiment analysis.
 */
export async function getAnalysisRadarComparison(
  experimentId: string
): Promise<RadarComparisonChart> {
  return fetchAPI(`/experiments/${experimentId}/analysis/clusters/radar`);
}

/**
 * Cut dendrogram at specified height.
 */
export async function cutAnalysisDendrogram(
  experimentId: string,
  request: CutDendrogramRequest
): Promise<HierarchicalResult> {
  return fetchAPI(`/experiments/${experimentId}/analysis/clusters/cut`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// =============================================================================
// Phase 4: Edge Cases & Outliers Endpoints
// =============================================================================

import type {
  ExtremeCasesTable,
  OutlierResult,
  ShapSummary,
  ShapExplanation,
  PDPResult,
  PDPComparison,
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
// Phase 5: Explainability (SHAP & PDP) Endpoints
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

/**
 * Get Partial Dependence Plot for a single feature.
 */
export async function getAnalysisPDP(
  experimentId: string,
  feature: string,
  gridResolution = 20
): Promise<PDPResult> {
  const params = new URLSearchParams({
    feature,
    grid_resolution: String(gridResolution),
  });
  return fetchAPI(`/experiments/${experimentId}/analysis/pdp?${params}`);
}

/**
 * Get PDP comparison for multiple features.
 */
export async function getAnalysisPDPComparison(
  experimentId: string,
  features: string[],
  gridResolution = 20
): Promise<PDPComparison> {
  const params = new URLSearchParams({
    features: features.join(','),
    grid_resolution: String(gridResolution),
  });
  return fetchAPI(`/experiments/${experimentId}/analysis/pdp/comparison?${params}`);
}

// =============================================================================
// Phase 6: Insights Endpoints
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

// frontend/src/services/simulation-api.ts
// API service for simulation analysis endpoints

import { fetchAPI } from './api';
import type {
  TryVsSuccessChart,
  OutcomeDistributionChart,
  SankeyChart,
  FailureHeatmapChart,
  BoxPlotChart,
  ScatterCorrelationChart,
  KMeansResult,
  HierarchicalResult,
  ElbowDataPoint,
  RadarChart,
  ExtremeCasesTable,
  OutlierResult,
  ShapExplanation,
  ShapSummary,
  PDPResult,
  PDPComparison,
  ChartInsight,
  SimulationInsights,
  ClusterRequest,
  CutDendrogramRequest,
  ChartType,
  ExecutiveSummaryResponse,
} from '@/types/simulation';

// =============================================================================
// Phase 1: Overview Charts
// =============================================================================

export async function getTryVsSuccessChart(
  simulationId: string,
  attemptRateThreshold = 0.5,
  successRateThreshold = 0.5
): Promise<TryVsSuccessChart> {
  const params = new URLSearchParams({
    attempt_rate_threshold: String(attemptRateThreshold),
    success_rate_threshold: String(successRateThreshold),
  });
  return fetchAPI(`/simulation/simulations/${simulationId}/charts/try-vs-success?${params}`);
}

export async function getDistributionChart(
  simulationId: string,
  sortBy = 'success_rate',
  order = 'desc',
  limit = 50
): Promise<OutcomeDistributionChart> {
  const params = new URLSearchParams({
    sort_by: sortBy,
    order,
    limit: String(limit),
  });
  return fetchAPI(`/simulation/simulations/${simulationId}/charts/distribution?${params}`);
}

export async function getSankeyChart(simulationId: string): Promise<SankeyChart> {
  return fetchAPI(`/simulation/simulations/${simulationId}/charts/sankey`);
}

// =============================================================================
// Phase 2: Problem Location Charts
// =============================================================================

export async function getFailureHeatmap(
  simulationId: string,
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
  return fetchAPI(`/simulation/simulations/${simulationId}/charts/failure-heatmap?${params}`);
}

export async function getBoxPlotChart(
  simulationId: string,
  attribute = 'trust_mean'
): Promise<BoxPlotChart> {
  const params = new URLSearchParams({ attribute });
  return fetchAPI(`/simulation/simulations/${simulationId}/charts/box-plot?${params}`);
}

export async function getScatterCorrelation(
  simulationId: string,
  xAxis = 'trust_mean',
  yAxis = 'success_rate',
  showTrendline = true
): Promise<ScatterCorrelationChart> {
  const params = new URLSearchParams({
    x_axis: xAxis,
    y_axis: yAxis,
    show_trendline: String(showTrendline),
  });
  return fetchAPI(`/simulation/simulations/${simulationId}/charts/scatter?${params}`);
}

// =============================================================================
// Phase 3: Clustering
// =============================================================================

export async function createClustering(
  simulationId: string,
  request: ClusterRequest
): Promise<KMeansResult | HierarchicalResult> {
  return fetchAPI(`/simulation/simulations/${simulationId}/clusters`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getClustering(
  simulationId: string
): Promise<KMeansResult | HierarchicalResult | null> {
  try {
    return await fetchAPI(`/simulation/simulations/${simulationId}/clusters`);
  } catch {
    return null;
  }
}

export async function getElbowData(simulationId: string): Promise<ElbowDataPoint[]> {
  return fetchAPI(`/simulation/simulations/${simulationId}/clusters/elbow`);
}

export async function getDendrogram(
  simulationId: string
): Promise<HierarchicalResult> {
  return fetchAPI(`/simulation/simulations/${simulationId}/clusters/dendrogram`);
}

export async function getClusterRadar(
  simulationId: string,
  clusterId: number
): Promise<RadarChart> {
  return fetchAPI(`/simulation/simulations/${simulationId}/clusters/${clusterId}/radar`);
}

export async function getRadarComparison(simulationId: string): Promise<RadarChart> {
  return fetchAPI(`/simulation/simulations/${simulationId}/clusters/radar-comparison`);
}

export async function cutDendrogram(
  simulationId: string,
  request: CutDendrogramRequest
): Promise<HierarchicalResult> {
  return fetchAPI(`/simulation/simulations/${simulationId}/clusters/cut`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// =============================================================================
// Phase 4: Edge Cases & Outliers
// =============================================================================

export async function getExtremeCases(
  simulationId: string,
  nPerCategory = 10
): Promise<ExtremeCasesTable> {
  const params = new URLSearchParams({ n_per_category: String(nPerCategory) });
  return fetchAPI(`/simulation/simulations/${simulationId}/extreme-cases?${params}`);
}

export async function getOutliers(
  simulationId: string,
  contamination = 0.1
): Promise<OutlierResult> {
  const params = new URLSearchParams({ contamination: String(contamination) });
  return fetchAPI(`/simulation/simulations/${simulationId}/outliers?${params}`);
}

// =============================================================================
// Phase 5: Explainability (SHAP & PDP)
// =============================================================================

export async function getShapSummary(simulationId: string): Promise<ShapSummary> {
  return fetchAPI(`/simulation/simulations/${simulationId}/shap/summary`);
}

export async function getShapExplanation(
  simulationId: string,
  synthId: string
): Promise<ShapExplanation> {
  return fetchAPI(`/simulation/simulations/${simulationId}/shap/${synthId}`);
}

export async function getPDP(
  simulationId: string,
  feature: string,
  gridResolution = 20
): Promise<PDPResult> {
  const params = new URLSearchParams({
    feature,
    grid_resolution: String(gridResolution),
  });
  return fetchAPI(`/simulation/simulations/${simulationId}/pdp?${params}`);
}

export async function getPDPComparison(
  simulationId: string,
  features: string[],
  gridResolution = 20
): Promise<PDPComparison> {
  const params = new URLSearchParams({
    features: features.join(','),
    grid_resolution: String(gridResolution),
  });
  return fetchAPI(`/simulation/simulations/${simulationId}/pdp/comparison?${params}`);
}

// =============================================================================
// Phase 6: LLM Insights
// =============================================================================

export async function getSimulationInsights(simulationId: string): Promise<SimulationInsights> {
  return fetchAPI(`/simulation/simulations/${simulationId}/insights`);
}

export async function generateChartInsight(
  simulationId: string,
  chartType: ChartType,
  chartData: Record<string, unknown>,
  forceRegenerate = false
): Promise<ChartInsight> {
  return fetchAPI(`/simulation/simulations/${simulationId}/insights/${chartType}`, {
    method: 'POST',
    body: JSON.stringify({
      chart_data: chartData,
      force_regenerate: forceRegenerate,
    }),
  });
}

export async function generateExecutiveSummary(
  simulationId: string
): Promise<ExecutiveSummaryResponse> {
  return fetchAPI(`/simulation/simulations/${simulationId}/insights/executive-summary`, {
    method: 'POST',
  });
}

export async function clearInsights(simulationId: string): Promise<void> {
  return fetchAPI(`/simulation/simulations/${simulationId}/insights`, {
    method: 'DELETE',
  });
}

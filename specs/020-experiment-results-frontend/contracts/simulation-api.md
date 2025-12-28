# API Contracts: Simulation Analysis Endpoints

**Feature**: 020-experiment-results-frontend
**Date**: 2025-12-28
**Base Path**: `/api/simulation`

## Overview

This document describes the API endpoints consumed by the frontend for experiment analysis results. All endpoints are already implemented in the backend (`src/synth_lab/api/routers/simulation.py`).

## Endpoint Categories

### Phase 1: Overview Charts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/simulations/{id}/charts/try-vs-success` | Try vs Success scatter plot |
| GET | `/simulations/{id}/charts/distribution` | Outcome distribution bars |
| GET | `/simulations/{id}/charts/sankey` | Sankey flow diagram |

### Phase 2: Problem Location

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/simulations/{id}/charts/failure-heatmap` | Failure heatmap grid |
| GET | `/simulations/{id}/charts/box-plot` | Box plot statistics |
| GET | `/simulations/{id}/charts/scatter` | Scatter correlation |
| GET | `/simulations/{id}/charts/tornado` | Tornado sensitivity chart |

### Phase 3: Clustering

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/simulations/{id}/clusters` | Create clustering |
| GET | `/simulations/{id}/clusters` | Get cached clustering |
| GET | `/simulations/{id}/clusters/elbow` | Elbow method data |
| GET | `/simulations/{id}/clusters/dendrogram` | Hierarchical dendrogram |
| GET | `/simulations/{id}/clusters/{cluster_id}/radar` | Single cluster radar |
| GET | `/simulations/{id}/clusters/radar-comparison` | All clusters radar |
| POST | `/simulations/{id}/clusters/cut` | Cut dendrogram at k |

### Phase 4: Edge Cases & Outliers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/simulations/{id}/extreme-cases` | Extreme cases table |
| GET | `/simulations/{id}/outliers` | Outlier detection |

### Phase 5: Explainability

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/simulations/{id}/shap/summary` | Global SHAP summary |
| GET | `/simulations/{id}/shap/{synth_id}` | Individual SHAP explanation |
| GET | `/simulations/{id}/pdp` | Partial dependence plot |
| GET | `/simulations/{id}/pdp/comparison` | PDP comparison |

### Phase 6: LLM Insights

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/simulations/{id}/insights` | All cached insights |
| POST | `/simulations/{id}/insights/{chart_type}` | Generate chart insight |
| POST | `/simulations/{id}/insights/executive-summary` | Generate executive summary |
| DELETE | `/simulations/{id}/insights` | Clear cached insights |

---

## Detailed Endpoint Specifications

### GET /simulations/{id}/charts/try-vs-success

**Query Parameters:**
- `attempt_rate_threshold` (float, default: 0.5): Threshold for high engagement
- `success_rate_threshold` (float, default: 0.5): Threshold for high success

**Response:** `TryVsSuccessChart`
```json
{
  "simulation_id": "uuid",
  "points": [
    {
      "synth_id": "uuid",
      "attempt_rate": 0.8,
      "success_rate": 0.6,
      "quadrant": "ok"
    }
  ],
  "quadrants": [
    {"quadrant": "ok", "count": 50, "percentage": 0.5}
  ],
  "thresholds": {
    "attempt_rate": 0.5,
    "success_rate": 0.5
  }
}
```

---

### GET /simulations/{id}/charts/distribution

**Query Parameters:**
- `sort_by` (string, default: "success_rate"): Sort field
- `order` (string, default: "desc"): Sort order (asc/desc)
- `limit` (int, default: 50): Max results

**Response:** `OutcomeDistributionChart`
```json
{
  "simulation_id": "uuid",
  "bars": [
    {
      "synth_id": "uuid",
      "did_not_try_rate": 0.1,
      "failed_rate": 0.3,
      "success_rate": 0.6
    }
  ],
  "summary": {
    "total_synths": 100,
    "avg_success_rate": 0.55,
    "avg_failed_rate": 0.25,
    "avg_did_not_try_rate": 0.20
  }
}
```

---

### GET /simulations/{id}/charts/sankey

**Response:** `SankeyChart`
```json
{
  "simulation_id": "uuid",
  "nodes": [
    {"name": "All Synths"},
    {"name": "Attempted"},
    {"name": "Not Attempted"},
    {"name": "Success"},
    {"name": "Failed"}
  ],
  "links": [
    {"source": 0, "target": 1, "value": 80},
    {"source": 0, "target": 2, "value": 20},
    {"source": 1, "target": 3, "value": 50},
    {"source": 1, "target": 4, "value": 30}
  ]
}
```

---

### GET /simulations/{id}/charts/failure-heatmap

**Query Parameters:**
- `x_axis` (string, default: "capability_mean"): X-axis attribute
- `y_axis` (string, default: "trust_mean"): Y-axis attribute
- `bins` (int, default: 5): Number of bins per axis
- `metric` (string, default: "failed_rate"): Metric to display

**Response:** `FailureHeatmapChart`
```json
{
  "simulation_id": "uuid",
  "cells": [
    {
      "x_bin": 0,
      "y_bin": 0,
      "x_label": "0.0-0.2",
      "y_label": "0.0-0.2",
      "count": 15,
      "metric_value": 0.45
    }
  ],
  "x_axis": "capability_mean",
  "y_axis": "trust_mean",
  "x_labels": ["0.0-0.2", "0.2-0.4", ...],
  "y_labels": ["0.0-0.2", "0.2-0.4", ...],
  "metric": "failed_rate"
}
```

---

### POST /simulations/{id}/clusters

**Request Body:** `ClusterRequest`
```json
{
  "method": "kmeans",
  "n_clusters": 4,
  "features": ["trust_mean", "capability_mean", "success_rate"]
}
```

**Response:** `KMeansResult` or `HierarchicalResult`

---

### GET /simulations/{id}/extreme-cases

**Query Parameters:**
- `n_per_category` (int, default: 10): Number per category (1-50)

**Response:** `ExtremeCasesTable`
```json
{
  "simulation_id": "uuid",
  "worst_failures": [
    {
      "synth_id": "uuid",
      "success_rate": 0.05,
      "failed_rate": 0.85,
      "did_not_try_rate": 0.10,
      "attributes": {"trust_mean": 0.2, ...},
      "category": "worst_failure",
      "suggested_questions": ["Why did you struggle with..."]
    }
  ],
  "best_successes": [...],
  "unexpected_cases": [...]
}
```

---

### GET /simulations/{id}/shap/{synth_id}

**Response:** `ShapExplanation`
```json
{
  "simulation_id": "uuid",
  "synth_id": "uuid",
  "base_value": 0.55,
  "predicted_value": 0.72,
  "contributions": [
    {"feature": "trust_mean", "value": 0.85, "shap_value": 0.12},
    {"feature": "capability_mean", "value": 0.3, "shap_value": -0.08}
  ],
  "explanation_text": "High trust (+0.12) compensated for low capability (-0.08)"
}
```

---

### POST /simulations/{id}/insights/{chart_type}

**Path Parameters:**
- `chart_type`: One of the `ChartType` enum values

**Request Body:** `GenerateInsightRequest`
```json
{
  "chart_data": { /* chart-specific data */ },
  "force_regenerate": false
}
```

**Response:** `ChartInsight`
```json
{
  "simulation_id": "uuid",
  "chart_type": "try_vs_success",
  "caption": {
    "short": "High engagement, mixed success",
    "medium": "Most users try the feature but success varies significantly"
  },
  "explanation": "The scatter plot shows that 75% of synths attempt the feature (above threshold), but only 45% succeed. The usability_issue quadrant contains 30% of synths.",
  "evidence": [
    {"metric": "attempt_rate", "value": "75%", "interpretation": "High feature discovery"},
    {"metric": "usability_issues", "value": "30%", "interpretation": "Significant UX problems"}
  ],
  "recommendation": "Focus on improving success for high-engagement users in the usability_issue quadrant",
  "generated_at": "2025-12-28T10:00:00Z"
}
```

---

## Error Responses

All endpoints return standard HTTP errors:

| Status | Description |
|--------|-------------|
| 400 | Bad request (invalid parameters, insufficient data) |
| 404 | Simulation or resource not found |
| 500 | Server error (analysis failed, LLM error) |

**Error Response Format:**
```json
{
  "detail": "Error message describing the issue"
}
```

---

## Frontend Service Implementation

```typescript
// services/simulation-api.ts

import { fetchAPI } from './api';
import type {
  TryVsSuccessChart,
  OutcomeDistributionChart,
  SankeyChart,
  FailureHeatmapChart,
  ScatterCorrelationChart,
  TornadoChart,
  KMeansResult,
  HierarchicalResult,
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
  GenerateInsightRequest,
  ChartType,
} from '@/types/simulation';

// Phase 1: Overview Charts
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

// Phase 2: Problem Location
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

export async function getTornadoChart(simulationId: string): Promise<TornadoChart> {
  return fetchAPI(`/simulation/simulations/${simulationId}/charts/tornado`);
}

// Phase 3: Clustering
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
): Promise<KMeansResult | HierarchicalResult> {
  return fetchAPI(`/simulation/simulations/${simulationId}/clusters`);
}

export async function getElbowData(simulationId: string): Promise<ElbowDataPoint[]> {
  return fetchAPI(`/simulation/simulations/${simulationId}/clusters/elbow`);
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

// Phase 4: Edge Cases & Outliers
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

// Phase 5: Explainability
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

// Phase 6: LLM Insights
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
): Promise<{ simulation_id: string; summary: string; total_insights: number }> {
  return fetchAPI(`/simulation/simulations/${simulationId}/insights/executive-summary`, {
    method: 'POST',
  });
}

export async function clearInsights(simulationId: string): Promise<void> {
  return fetchAPI(`/simulation/simulations/${simulationId}/insights`, {
    method: 'DELETE',
  });
}
```
